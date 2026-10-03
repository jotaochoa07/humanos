"""Deterministic scoring helpers for m2-v3 self-contained narrative units.

Combines LLM dimension scores with heavy penalties for clips that fail as
independent conceptual units. Does not hardcode Buzz themes.
"""

from __future__ import annotations

import re
from typing import Any, Mapping, Sequence

from shorts_factory.backends.ranking import ScoreDimensions
from shorts_factory.pipeline.text_heuristics import (
    looks_like_mid_sentence_start,
    looks_like_sentence_end,
)

# Opening pronouns / deictics that usually need prior context
_PRONOUN_START_RE = re.compile(
    r"^(esto|eso|esta|ese|estos|esos|esta?s?|ellos?|ellas?|lo|la|le|les|"
    r"this|that|these|those|they|them|it|he|she)\b",
    re.IGNORECASE,
)

# Trailing connectors that suggest the thought was cut before the conclusion
_TRAILING_CONNECTOR_RE = re.compile(
    r"\b(porque|entonces|pero|y|o|aunque|asi|así|because|so|but|and|or|then)\s*$",
    re.IGNORECASE,
)

_OPEN_STRIP_RE = re.compile(r'^[\s"\'“”‘’¿¡(\[]+')


def _first_words(text: str, n: int = 8) -> str:
    stripped = _OPEN_STRIP_RE.sub("", (text or "").strip())
    parts = re.split(r"\s+", stripped)
    return " ".join(parts[:n])


def _last_words(text: str, n: int = 8) -> str:
    parts = re.split(r"\s+", (text or "").strip())
    return " ".join(parts[-n:])


def clamp01(x: float) -> float:
    return max(0.0, min(1.0, float(x)))


def weighted_dimension_score(dims: ScoreDimensions) -> float:
    """Base score from dimensions — payoff + standalone weighted highest."""
    w = {
        "hook_strength": 0.15,
        "context_completeness": 0.20,
        "conceptual_completeness": 0.20,
        "standalone_clarity": 0.25,
        "payoff_strength": 0.20,
    }
    d = dims.as_dict()
    return sum(clamp01(d[k]) * w[k] for k in w)


def standalone_penalties(
    *,
    start_text: str,
    end_text: str,
    full_transcript: str,
    payoff_text: str = "",
    dims: ScoreDimensions | None = None,
) -> tuple[float, list[str]]:
    """Return (penalty 0..1, reason codes). Heavy penalties for non-standalone clips."""
    reasons: list[str] = []
    penalty = 0.0
    start = (start_text or "").strip()
    end = (end_text or "").strip()
    head = _first_words(start, 6)

    # 1) Starts with pronouns/references without context
    if _PRONOUN_START_RE.search(_OPEN_STRIP_RE.sub("", start)):
        penalty += 0.22
        reasons.append("pronoun_start_without_context")
    if looks_like_mid_sentence_start(start):
        penalty += 0.18
        reasons.append("mid_sentence_start")

    # 2) Ending before the conclusion
    if not looks_like_sentence_end(end):
        penalty += 0.20
        reasons.append("incomplete_sentence_end")
    if _TRAILING_CONNECTOR_RE.search(end.rstrip(".,!?;:…\"'”’")):
        penalty += 0.15
        reasons.append("trailing_connector_no_payoff")

    # 3) Depends on a prior sentence (deictic / "como dije" style)
    prior_dep = re.search(
        r"\b(como (ya )?dije|como vimos|antes|anteriormente|lo anterior|"
        r"as i (said|mentioned)|previously|earlier)\b",
        full_transcript or "",
        re.IGNORECASE,
    )
    if prior_dep:
        penalty += 0.18
        reasons.append("depends_on_prior_context")

    # 4) Observation without resolution — weak/empty payoff signals
    dims = dims or ScoreDimensions()
    payoff = (payoff_text or "").strip()
    if dims.payoff_strength < 0.35 or (not payoff and dims.conceptual_completeness < 0.45):
        penalty += 0.20
        reasons.append("observation_without_resolution")

    # 5) Standalone clarity already very low from LLM
    if dims.standalone_clarity < 0.35:
        penalty += 0.15
        reasons.append("low_standalone_clarity")

    # Mild signal: head is only a continuation cue
    if head.lower().startswith(("y ", "pero ", "porque ", "and ", "but ", "because ")):
        if "mid_sentence_start" not in reasons:
            penalty += 0.10
            reasons.append("continuation_opener")

    return clamp01(penalty), reasons


def compose_final_score(
    dims: ScoreDimensions,
    *,
    start_text: str,
    end_text: str,
    full_transcript: str,
    payoff_text: str = "",
    duration_sec: float | None = None,
    preferred_min: float = 45.0,
    preferred_max: float = 60.0,
) -> tuple[float, float, list[str]]:
    """Return (final_score, penalty, reasons).

    Heavily penalizes non-self-contained units. Soft bonus for 45–60s closed units.
    """
    base = weighted_dimension_score(dims)
    penalty, reasons = standalone_penalties(
        start_text=start_text,
        end_text=end_text,
        full_transcript=full_transcript,
        payoff_text=payoff_text,
        dims=dims,
    )
    score = base * (1.0 - 0.85 * penalty)  # heavy: up to ~85% of base wiped

    # Soft preference for well-closed mid-length ideas
    if duration_sec is not None and preferred_min <= duration_sec <= preferred_max:
        if looks_like_sentence_end(end_text) and not looks_like_mid_sentence_start(start_text):
            score = min(1.0, score + 0.03)
            reasons.append("preferred_duration_closed_bonus")

    return clamp01(score), penalty, reasons


def parse_score_dimensions(item: Mapping[str, Any]) -> ScoreDimensions:
    """Extract dimension scores from LLM JSON (tolerant)."""
    nested = item.get("scores") if isinstance(item.get("scores"), dict) else {}

    def _get(key: str, default: float = 0.5) -> float:
        for src in (item, nested):
            if key in src and src[key] is not None:
                try:
                    return clamp01(float(src[key]))
                except (TypeError, ValueError):
                    pass
        return default

    # If only a single score was provided, seed dimensions from it
    seed = 0.5
    if "score" in item:
        try:
            seed = clamp01(float(item["score"]))
        except (TypeError, ValueError):
            seed = 0.5

    return ScoreDimensions(
        hook_strength=_get("hook_strength", seed),
        context_completeness=_get("context_completeness", seed),
        conceptual_completeness=_get("conceptual_completeness", seed),
        standalone_clarity=_get("standalone_clarity", seed),
        payoff_strength=_get("payoff_strength", seed),
    )


def duplicate_idea_penalty(
    candidate: Mapping[str, Any],
    kept: Sequence[Mapping[str, Any]],
) -> float:
    """Extra penalty when central_idea closely duplicates a better-kept candidate."""
    idea = re.sub(r"\s+", " ", str(candidate.get("central_idea") or "").lower()).strip()
    if len(idea) < 12:
        return 0.0
    for other in kept:
        other_idea = re.sub(
            r"\s+", " ", str(other.get("central_idea") or "").lower()
        ).strip()
        if len(other_idea) < 12:
            continue
        # crude token overlap
        a, b = set(idea.split()), set(other_idea.split())
        if not a or not b:
            continue
        overlap = len(a & b) / max(1, len(a | b))
        if overlap >= 0.55:
            return 0.25
    return 0.0
