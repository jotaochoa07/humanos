"""OpenRouter-backed CandidateRanker for Shorts Factory (m2-v3).

Uses the same env conventions as repo `openrouter_client.py`
(OPENROUTER_API_KEY, OPENROUTER_MODEL) but lives inside shorts_factory
so editorial agents are untouched.
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
import urllib.error
import urllib.request
from typing import Any, Mapping, Optional, Sequence

from shorts_factory.backends.json_robust import loads_json_robust
from shorts_factory.backends.ranking import (
    CandidateRanker,
    RankingConfig,
    RawCandidate,
    ScoreDimensions,
)
from shorts_factory.pipeline.scoring import parse_score_dimensions
from shorts_factory.pipeline.spans import parse_raw_spans

logger = logging.getLogger(__name__)

DEFAULT_OPENROUTER_MODEL = "google/gemini-2.5-flash-lite"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# m2-v4: self-contained narrative units assembled as 1–3 semantic spans.
SYSTEM_PROMPT = """\
Eres un editor de Shorts con MONTAJE SEMÁNTICO. No marques solo momentos
interesantes: ensambla UNIDADES NARRATIVAS AUTOCONTENIDAS con 1–3 spans
de audio real del video (nunca inventes ni re-grabes habla).

Cada candidato debe entenderse SIN el video largo. Debe contener
(explícita o implícitamente):
1) HOOK — por qué seguir viendo
2) CONTEXTO MÍNIMO — problema / situación
3) IDEA / DESARROLLO — qué se explica
4) PAYOFF — conclusión / takeaway (la idea debe CERRAR)

MONTAJE (spans):
- 1 a 3 spans por short, en orden temporal original.
- role ∈ {hook, context, development, payoff}.
- Si la unidad ya funciona en un tramo continuo → USA 1 SOLO span
  (role "development" para el arco completo).
- Si hay relleno irrelevante entre piezas → USA 2–3 spans y DEJA GAPS
  (corta el filler). NO resuelvas completitud estirando un rango continuo
  a 80–90s.
- Preferencia de duración TOTAL HABLA (suma de spans): ~30–60s.
  Más solo si es realmente necesario (nunca por relleno).
- Cada span debe tener función narrativa clara.

Puntúa dimensiones [0,1] (igual que m2-v3):
hook_strength, context_completeness, conceptual_completeness,
standalone_clarity, payoff_strength.
"score" = juicio global ya penalizado por: pronombres sin contexto,
terminar antes del payoff, depender de frase previa, observación sin
resolución, duplicar una idea mejor resuelta, o incluir filler inútil.

NO inventes hechos. Timestamps dentro del ASR (aproximados OK).

Responde SOLO JSON:
{
  "candidates": [
    {
      "spans": [
        {"role": "hook", "start": <float>, "end": <float>},
        {"role": "context", "start": <float>, "end": <float>},
        {"role": "payoff", "start": <float>, "end": <float>}
      ],
      "start": <float envelope start>,
      "end": <float envelope end>,
      "hook": "<string>",
      "minimum_context": "<string>",
      "central_idea": "<string>",
      "idea_development": "<string>",
      "payoff": "<string>",
      "selection_reason": "<string>",
      "suggested_title": "<string corto>",
      "hook_strength": <0..1>,
      "context_completeness": <0..1>,
      "conceptual_completeness": <0..1>,
      "standalone_clarity": <0..1>,
      "payoff_strength": <0..1>,
      "score": <0..1>
    }
  ]
}
"""


def _format_segments_for_prompt(segments: Sequence[Mapping[str, Any]], *, max_chars: int = 48000) -> str:
    lines: list[str] = []
    for seg in segments:
        sid = seg.get("id", "?")
        start = float(seg["start"])
        end = float(seg["end"])
        text = str(seg.get("text", "")).strip()
        lines.append(f"[{sid}] {start:.2f}-{end:.2f} {text}")
    blob = "\n".join(lines)
    if len(blob) > max_chars:
        blob = blob[:max_chars] + "\n…[truncated]"
    return blob


def _slugify_title(title: str) -> str:
    raw = title.strip().lower()
    raw = re.sub(r"[^a-z0-9áéíóúñü\s-]", "", raw, flags=re.IGNORECASE)
    raw = re.sub(r"\s+", "-", raw).strip("-")
    return raw[:60] or "candidate"


class OpenRouterClient:
    """Minimal JSON chat client for shorts_factory (stdlib only)."""

    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        api_url: str = OPENROUTER_URL,
        default_model: Optional[str] = None,
        timeout_sec: float = 90.0,
        max_attempts: int = 3,
    ) -> None:
        self.api_key = api_key if api_key is not None else os.environ.get("OPENROUTER_API_KEY", "")
        self.api_url = api_url
        self.default_model = (
            default_model
            or os.environ.get("OPENROUTER_MODEL")
            or DEFAULT_OPENROUTER_MODEL
        )
        self.timeout_sec = timeout_sec
        self.max_attempts = max_attempts

    def complete_json(
        self,
        prompt: str,
        *,
        system_prompt: str,
        model: Optional[str] = None,
    ) -> dict[str, Any]:
        if not self.api_key:
            raise ValueError(
                "OPENROUTER_API_KEY is not set. Required for CandidateRanker "
                "(or inject a mock CandidateRanker / OpenRouterClient in tests)."
            )

        model_name = model or self.default_model
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/jotaochoa07/humanos",
            "X-Title": "HUMANOS Shorts Factory",
        }
        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "response_format": {"type": "json_object"},
            "max_tokens": 12000,
        }
        body = json.dumps(payload).encode("utf-8")
        last_error: Optional[BaseException] = None

        for attempt in range(1, self.max_attempts + 1):
            req = urllib.request.Request(
                self.api_url, data=body, headers=headers, method="POST"
            )
            try:
                with urllib.request.urlopen(req, timeout=self.timeout_sec) as response:
                    res_json = json.loads(response.read().decode("utf-8"))
                choices = res_json.get("choices")
                if not choices:
                    raise ValueError(f"OpenRouter response missing choices: {res_json!r}")
                content = choices[0]["message"]["content"]
                if not isinstance(content, str):
                    raise ValueError("OpenRouter message content is not a string")
                return loads_json_robust(content)
            except (
                urllib.error.URLError,
                urllib.error.HTTPError,
                TimeoutError,
                json.JSONDecodeError,
                ValueError,
            ) as exc:
                last_error = exc
                logger.warning(
                    "OpenRouter attempt %s/%s failed: %s",
                    attempt,
                    self.max_attempts,
                    exc,
                )
                if attempt < self.max_attempts:
                    time.sleep(2 * attempt)

        assert last_error is not None
        raise last_error


class OpenRouterCandidateRanker(CandidateRanker):
    """LLM ranker that proposes self-contained narrative-unit candidates."""

    name = "OpenRouterCandidateRanker"

    def __init__(self, client: Optional[OpenRouterClient] = None) -> None:
        self.client = client or OpenRouterClient()

    def propose_candidates(
        self,
        transcript: Mapping[str, Any],
        *,
        config: RankingConfig,
    ) -> Sequence[RawCandidate]:
        segments = transcript.get("segments") or []
        if not segments:
            return []

        segment_block = _format_segments_for_prompt(segments)
        user_prompt = (
            f"Fuente: {transcript.get('source_video', '')}\n"
            f"Duración total (s): {transcript.get('duration_sec', '')}\n"
            f"Idioma: {transcript.get('language', '')}\n"
            f"Duración TOTAL HABLA (suma de spans) dura: "
            f"{config.duration_min_sec:.0f}–{config.duration_max_sec:.0f} s\n"
            f"Preferencia suma de spans: "
            f"{config.preferred_duration_min_sec:.0f}–"
            f"{config.preferred_duration_max_sec:.0f} s\n"
            f"Máx spans por candidato: {config.max_spans}\n"
            f"Cantidad objetivo FINAL: {config.target_count} "
            f"(máx {max(config.target_count + 3, 8)} brutos; menos es mejor).\n"
            f"Recuerda: gaps OK; no estires un tramo continuo a 80–90s.\n\n"
            f"Segmentos ASR (id start-end text):\n{segment_block}\n"
        )

        data = self.client.complete_json(
            user_prompt,
            system_prompt=SYSTEM_PROMPT,
            model=config.model,
        )
        return parse_ranker_payload(data)


def parse_ranker_payload(data: Mapping[str, Any]) -> list[RawCandidate]:
    """Parse LLM JSON into RawCandidate list (tolerant; m2-v3 fields optional)."""
    raw_list = data.get("candidates")
    if raw_list is None and isinstance(data.get("items"), list):
        raw_list = data["items"]
    if not isinstance(raw_list, list):
        raise ValueError("ranker JSON must contain a 'candidates' list")

    out: list[RawCandidate] = []
    for i, item in enumerate(raw_list):
        if not isinstance(item, dict):
            logger.warning("Skipping non-object candidate at index %s", i)
            continue
        try:
            start = float(item["start"])
            end = float(item["end"])
            score = float(item.get("score", 0.5))
        except (KeyError, TypeError, ValueError) as exc:
            logger.warning("Skipping candidate %s: %s", i, exc)
            continue
        if end <= start:
            logger.warning("Skipping candidate %s: end <= start", i)
            continue
        title = str(item.get("suggested_title") or item.get("title") or f"clip-{i+1}").strip()
        dims: ScoreDimensions = parse_score_dimensions(item)
        spans = parse_raw_spans(item, start=start, end=end)
        # Envelope from spans if present
        if spans:
            start = min(sp.start for sp in spans)
            end = max(sp.end for sp in spans)
        out.append(
            RawCandidate(
                start=start,
                end=end,
                hook=str(item.get("hook") or "").strip(),
                central_idea=str(
                    item.get("central_idea") or item.get("thesis") or ""
                ).strip(),
                selection_reason=str(
                    item.get("selection_reason") or item.get("reason") or ""
                ).strip(),
                score=max(0.0, min(1.0, score)),
                suggested_title=title,
                transcript=str(item.get("transcript") or "").strip(),
                minimum_context=str(
                    item.get("minimum_context") or item.get("context") or ""
                ).strip(),
                idea_development=str(
                    item.get("idea_development") or item.get("development") or ""
                ).strip(),
                payoff=str(item.get("payoff") or item.get("conclusion") or "").strip(),
                scores=dims,
                spans=list(spans),
                extra={"slug_hint": _slugify_title(title)},
            )
        )
    return out
