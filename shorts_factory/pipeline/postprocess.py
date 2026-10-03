"""Deterministic post-steps for Shorts Factory candidates (m2-v4 spans).

`snap_rules_version: m2-v4` — semantic editing with 1–3 narrative spans.

Rules:
1. Each span snaps independently to ASR segment boundaries (light ±1 refine only).
2. Do **not** solve conceptual completeness by expanding one continuous range
   to 80–90s. Prefer cutting filler via gaps between spans.
3. 1–3 spans, temporal order, gaps allowed, no invented speech.
4. `duration_sec` = sum of span durations (spoken time). Prefer 30–60s total.
5. If the unit already works continuously → keep **1 span**.
6. Score dimensions from m2-v3 retained; add soft penalties for oversized
   continuous singles and reward cutting interstitial gaps when multi-span.
7. NMS by envelope IoU + conceptual near-duplicate drop → top N.
"""

from __future__ import annotations

import re
from typing import Any, Mapping, Sequence

from shorts_factory.backends.ranking import RankingConfig, RawCandidate, ScoreDimensions
from shorts_factory.pipeline.scoring import (
    compose_final_score,
    duplicate_idea_penalty,
)
from shorts_factory.pipeline.spans import (
    envelope_and_total,
    interstitial_gap_sec,
    synthesize_spans_from_envelope,
    validate_and_snap_spans,
)
from shorts_factory.pipeline.text_heuristics import (
    looks_like_mid_sentence_start,
    looks_like_sentence_end,
)

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def temporal_iou(a_start: float, a_end: float, b_start: float, b_end: float) -> float:
    inter = max(0.0, min(a_end, b_end) - max(a_start, b_start))
    if inter <= 0:
        return 0.0
    union = max(a_end, b_end) - min(a_start, b_start)
    if union <= 0:
        return 0.0
    return inter / union


def _slugify(text: str, fallback: str) -> str:
    raw = text.strip().lower()
    for src, dst in (
        ("á", "a"),
        ("é", "e"),
        ("í", "i"),
        ("ó", "o"),
        ("ú", "u"),
        ("ñ", "n"),
        ("ü", "u"),
    ):
        raw = raw.replace(src, dst)
    cleaned = _SLUG_RE.sub("-", raw).strip("-")
    cleaned = re.sub(r"-{2,}", "-", cleaned)
    return cleaned[:48] or fallback


def snap_candidate_to_segments(
    raw: RawCandidate,
    segments: Sequence[Mapping[str, Any]],
    *,
    config: RankingConfig,
) -> dict[str, Any] | None:
    """Snap/validate spans → scored candidate dict. None = reject."""
    if not segments:
        return None

    raw_spans = synthesize_spans_from_envelope(raw)
    snapped, errors = validate_and_snap_spans(raw_spans, segments, config=config)
    if not snapped:
        return None

    env_start, env_end, spoken = envelope_and_total(snapped)
    gap_sec = interstitial_gap_sec(snapped)

    # Joined transcript with gap markers (not spoken — editorial only)
    parts = [str(s.get("transcript") or "").strip() for s in snapped]
    transcript = " […] ".join(p for p in parts if p)

    start_text = str(snapped[0].get("transcript") or "")
    end_text = str(snapped[-1].get("transcript") or "")

    dims = raw.scores if isinstance(raw.scores, ScoreDimensions) else ScoreDimensions()
    final_score, penalty, penalty_reasons = compose_final_score(
        dims,
        start_text=start_text,
        end_text=end_text,
        full_transcript=transcript.replace(" […]", ""),
        payoff_text=raw.payoff,
        duration_sec=spoken,
        preferred_min=config.preferred_duration_min_sec,
        preferred_max=config.preferred_duration_max_sec,
    )

    # Soft penalty: single continuous span that balloons past preferred max
    # (the anti-pattern of "expand to 80–90s for completeness")
    if len(snapped) == 1 and spoken > config.preferred_duration_max_sec + 5:
        over = (spoken - config.preferred_duration_max_sec) / max(
            1.0, config.duration_max_sec - config.preferred_duration_max_sec
        )
        extra = min(0.25, 0.08 + 0.2 * over)
        final_score = max(0.0, final_score - extra)
        penalty = min(1.0, penalty + extra)
        penalty_reasons = list(penalty_reasons) + ["oversized_continuous_span"]

    # Soft reward: multi-span that cuts interstitial filler
    if len(snapped) >= 2 and gap_sec >= 3.0:
        final_score = min(1.0, final_score + 0.04)
        penalty_reasons = list(penalty_reasons) + ["cut_interstitial_gap_bonus"]

    if raw.score > 0:
        final_score = max(0.0, min(1.0, 0.85 * final_score + 0.15 * float(raw.score)))

    return {
        "start": env_start,
        "end": env_end,
        "duration_sec": spoken,
        "envelope_duration_sec": round(env_end - env_start, 3),
        "interstitial_gap_sec": gap_sec,
        "spans": snapped,
        "transcript": transcript,
        "hook": raw.hook,
        "minimum_context": raw.minimum_context,
        "central_idea": raw.central_idea,
        "idea_development": raw.idea_development,
        "payoff": raw.payoff,
        "selection_reason": raw.selection_reason,
        "suggested_title": raw.suggested_title,
        "scores": dims.as_dict(),
        "score": round(final_score, 4),
        "score_penalty": round(penalty, 4),
        "penalty_reasons": penalty_reasons,
        "segment_id_start": int(snapped[0]["segment_id_start"]),
        "segment_id_end": int(snapped[-1]["segment_id_end"]),
        "boundary_refined": True,
        "span_count": len(snapped),
    }


def nms_by_iou(
    candidates: Sequence[Mapping[str, Any]],
    *,
    iou_threshold: float,
) -> list[dict[str, Any]]:
    kept: list[dict[str, Any]] = []
    for cand in candidates:
        overlaps = False
        for other in kept:
            iou = temporal_iou(
                float(cand["start"]),
                float(cand["end"]),
                float(other["start"]),
                float(other["end"]),
            )
            if iou >= iou_threshold:
                overlaps = True
                break
        if not overlaps:
            dup = duplicate_idea_penalty(cand, kept)
            item = dict(cand)
            if dup > 0:
                item["score"] = max(0.0, float(item["score"]) - dup)
                reasons = list(item.get("penalty_reasons") or [])
                reasons.append("duplicate_of_better_resolved_idea")
                item["penalty_reasons"] = reasons
                item["score_penalty"] = round(
                    float(item.get("score_penalty") or 0) + dup, 4
                )
            kept.append(item)
    kept.sort(key=lambda c: float(c["score"]), reverse=True)
    final: list[dict[str, Any]] = []
    for cand in kept:
        if (
            "duplicate_of_better_resolved_idea" in (cand.get("penalty_reasons") or [])
            and float(cand["score"]) < 0.35
        ):
            continue
        if any(
            temporal_iou(
                float(cand["start"]),
                float(cand["end"]),
                float(o["start"]),
                float(o["end"]),
            )
            >= iou_threshold
            for o in final
        ):
            continue
        final.append(cand)
    return final


def assign_ids(candidates: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    used: set[str] = set()
    out: list[dict[str, Any]] = []
    for idx, cand in enumerate(candidates, start=1):
        base = _slugify(str(cand.get("suggested_title") or ""), f"clip-{idx:02d}")
        slug = base
        n = 2
        while slug in used:
            slug = f"{base}-{n}"
            n += 1
        used.add(slug)
        cid = f"{idx:02d}-{slug}"
        item = dict(cand)
        item["id"] = cid
        item["folder"] = f"{cid}/"
        out.append(item)
    return out


def postprocess_candidates(
    raw_candidates: Sequence[RawCandidate],
    transcript: Mapping[str, Any],
    *,
    config: RankingConfig,
) -> list[dict[str, Any]]:
    """Full chain: snap spans → score → filter → NMS → top N → ids."""
    segments = transcript.get("segments") or []
    if not isinstance(segments, list) or not segments:
        return []

    snapped: list[dict[str, Any]] = []
    for raw in raw_candidates:
        item = snap_candidate_to_segments(raw, segments, config=config)
        if item is not None:
            snapped.append(item)

    snapped.sort(key=lambda c: float(c["score"]), reverse=True)
    kept = nms_by_iou(snapped, iou_threshold=config.overlap_iou_threshold)
    top = kept[: max(0, int(config.target_count))]
    return assign_ids(top)


# --- Back-compat shims used by older boundary tests ---

def refine_boundaries(
    i_start: int,
    i_end: int,
    segments: Sequence[Mapping[str, Any]],
    *,
    duration_max_sec: float,
) -> tuple[int, int, dict[str, bool]]:
    """Legacy helper: light ±1 refine (no multi-expand to max)."""
    flags = {"expanded_start_back": False, "expanded_end_forward": False}
    if not segments:
        return i_start, i_end, flags
    # Operate on indices directly
    i0, i1 = i_start, i_end
    start_text = str(segments[i0].get("text", ""))
    if looks_like_mid_sentence_start(start_text) and i0 > 0:
        trial = i0 - 1
        dur = float(segments[i1]["end"]) - float(segments[trial]["start"])
        if dur <= duration_max_sec:
            i0 = trial
            flags["expanded_start_back"] = True
    end_text = str(segments[i1].get("text", ""))
    if not looks_like_sentence_end(end_text) and i1 + 1 < len(segments):
        trial = i1 + 1
        dur = float(segments[trial]["end"]) - float(segments[i0]["start"])
        if dur <= duration_max_sec:
            i1 = trial
            flags["expanded_end_forward"] = True
    return i0, i1, flags


def complete_narrative_unit(
    i_start: int,
    i_end: int,
    segments: Sequence[Mapping[str, Any]],
    *,
    duration_max_sec: float,
) -> tuple[int, int, dict[str, int]]:
    """m2-v4: completeness via spans/gaps — here only light ±1 refine."""
    a, b, flags = refine_boundaries(
        i_start, i_end, segments, duration_max_sec=duration_max_sec
    )
    return (
        a,
        b,
        {
            "expanded_start_segments": 1 if flags["expanded_start_back"] else 0,
            "expanded_end_segments": 1 if flags["expanded_end_forward"] else 0,
        },
    )


# Re-export sentence helpers for tests that imported from postprocess
__all__ = [
    "assign_ids",
    "complete_narrative_unit",
    "nms_by_iou",
    "postprocess_candidates",
    "refine_boundaries",
    "snap_candidate_to_segments",
    "temporal_iou",
    "looks_like_mid_sentence_start",
    "looks_like_sentence_end",
]
