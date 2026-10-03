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

logger = logging.getLogger(__name__)

DEFAULT_OPENROUTER_MODEL = "google/gemini-2.5-flash-lite"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# m2-v3 editorial criteria: self-contained narrative units (not mere interesting moments).
SYSTEM_PROMPT = """\
Eres un editor de Shorts. Tu trabajo NO es marcar momentos interesantes:
es seleccionar UNIDADES NARRATIVAS AUTOCONTENIDAS.

Cada candidato debe poder entenderse SIN ver el video largo. Para aprobarlo,
debe contener (explícita o implícitamente) estas cuatro piezas:
1) HOOK — por qué seguir viendo (tensión, contraste, pregunta, tesis provocadora)
2) CONTEXTO MÍNIMO — qué problema / situación se está planteando
3) IDEA / DESARROLLO — qué se explica o argumenta
4) PAYOFF / CONCLUSIÓN — qué se lleva el espectador; la idea debe CERRAR

No se exige estructura teatral completa, pero la idea debe resolverse.
Prefiere un clip bien cerrado de ~45–60s a un clip incompleto de ~22s.
Menos clips, más autocontenidos — no maximices cantidad.

Rechaza / puntúa muy bajo si:
- empieza con pronombres o referencias sin contexto (esto/eso/ellos/this/that…)
- termina antes de la conclusión
- depende de una frase anterior del video
- es solo una observación sin resolución
- duplica otra idea ya mejor resuelta

Puntúa cada dimensión en [0,1]:
- hook_strength
- context_completeness
- conceptual_completeness
- standalone_clarity
- payoff_strength
El campo "score" debe ser tu juicio global YA penalizado por los fallos de arriba.

NO inventes hechos fuera del transcript. Timestamps start/end dentro del rango
ASR (aproximados OK; el sistema hará snap/expansión a fronteras de segmento).

Responde SOLO JSON:
{
  "candidates": [
    {
      "start": <float seconds>,
      "end": <float seconds>,
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
            f"Ventana dura de duración: {config.duration_min_sec:.0f}–"
            f"{config.duration_max_sec:.0f} s\n"
            f"Preferencia de duración (idea cerrada): "
            f"{config.preferred_duration_min_sec:.0f}–"
            f"{config.preferred_duration_max_sec:.0f} s\n"
            f"Cantidad objetivo FINAL: {config.target_count} "
            f"(propón como máximo {max(config.target_count + 3, 8)} brutos "
            f"de alta calidad; el post-proceso filtrará. Menos es mejor.)\n\n"
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
                extra={"slug_hint": _slugify_title(title)},
            )
        )
    return out
