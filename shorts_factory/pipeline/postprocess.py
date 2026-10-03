"""Deterministic post-steps for Shorts Factory candidates (m2-v3).

Timestamp grounding + narrative-unit completion (`snap_rules_version: m2-v3`):
1. Raw LLM start/end may be approximate floats in seconds.
2. **Start snap / end snap** to ASR segment boundaries (nearest containing).
3. Expand/trim whole segments to satisfy `duration_min_sec` / `duration_max_sec`.
4. **Multi-segment narrative completion** (within max duration):
   - Expand **backward** while the start looks mid-sentence / pronoun-deictic /
     continuation, as long as duration ≤ max.
   - Expand **forward** while the end looks incomplete (no terminal punctuation
     / trailing connector), as long as duration ≤ max.
   - Prefer a well-closed ~45–60s idea over an incomplete short clip
     (soft preference via scoring bonus; hard cap remains `duration_max_sec`).
5. Rebuild transcript from inclusive ASR span.
6. Attach score dimensions + apply deterministic standalone penalties.
7. Duration filter → sort by final score → NMS by IoU → drop near-duplicate
   ideas → take top N (fewer, better — default target_count=5).
"""

from __future__ import annotations

import re
from typing import Any, Mapping, Sequence

from shorts_factory.backends.ranking import RankingConfig, RawCandidate, ScoreDimensions
from shorts_factory.pipeline.scoring import (
    compose_final_score,
    duplicate_idea_penalty,
)
from shorts_factory.pipeline.text_heuristics import (
    looks_like_mid_sentence_start,
    looks_like_sentence_end,
)

_SLUG_RE = re.compile(r"[^a-z0-9]+")
_PRONOUN_START_RE = re.compile(
    r"^(esto|eso|esta|ese|estos|esos|ellos?|ellas?|lo|la|le|les|"
    r"this|that|these|those|they|them|it|he|she)\b",
    re.IGNORECASE,
)
_OPEN_STRIP_RE = re.compile(r'^[\s"\'“”‘’¿¡(\[]+')
_TRAILING_CONNECTOR_RE = re.compile(
    r"\b(porque|entonces|pero|y|o|aunque|asi|así|because|so|but|and|or|then)\s*$",
    re.IGNORECASE,
)


def temporal_iou(a_start: float, a_end: float, b_start: float, b_end: float) -> float:
    inter = max(0.0, min(a_end, b_end) - max(a_start, b_start))
    if inter <= 0:
        return 0.0
    union = max(a_end, b_end) - min(a_start, b_start)
    if union <= 0:
        return 0.0
    return inter / union


def _nearest_segment_index(segments: Sequence[Mapping[str, Any]], t: float) -> int:
    best_i = 0
    best_dist = float("inf")
    for i, seg in enumerate(segments):
        start = float(seg["start"])
        end = float(seg["end"])
        if start <= t <= end:
            return i
        if t < start:
            dist = start - t
        elif t > end:
            dist = t - end
        else:
            dist = 0.0
        if dist < best_dist:
            best_dist = dist
            best_i = i
    return best_i


def _join_transcript(segments: Sequence[Mapping[str, Any]], i0: int, i1: int) -> str:
    parts = [str(segments[i].get("text", "")).strip() for i in range(i0, i1 + 1)]
    return " ".join(p for p in parts if p)


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


def _span_duration(segments: Sequence[Mapping[str, Any]], a: int, b: int) -> float:
    return float(segments[b]["end"]) - float(segments[a]["start"])


def _needs_expand_start(text: str) -> bool:
    if looks_like_mid_sentence_start(text):
        return True
    stripped = _OPEN_STRIP_RE.sub("", (text or "").strip())
    return bool(_PRONOUN_START_RE.search(stripped))


def _needs_expand_end(text: str) -> bool:
    if not looks_like_sentence_end(text):
        return True
    trimmed = (text or "").strip().rstrip(".,!?;:…\"'”’")
    return bool(_TRAILING_CONNECTOR_RE.search(trimmed))


def complete_narrative_unit(
    i_start: int,
    i_end: int,
    segments: Sequence[Mapping[str, Any]],
    *,
    duration_max_sec: float,
) -> tuple[int, int, dict[str, int]]:
    """Expand multiple ASR segments (±) to complete a self-contained unit.

    Stops when start/end look complete or further expand would exceed max duration.
    """
    flags = {"expanded_start_segments": 0, "expanded_end_segments": 0}
    n = len(segments)
    if n == 0 or i_start < 0 or i_end < i_start:
        return i_start, i_end, flags

    # Expand backward while start is incomplete
    while i_start > 0:
        start_text = str(segments[i_start].get("text", ""))
        if not _needs_expand_start(start_text):
            break
        trial = i_start - 1
        if _span_duration(segments, trial, i_end) > duration_max_sec:
            break
        i_start = trial
        flags["expanded_start_segments"] += 1

    # Expand forward while end is incomplete
    while i_end + 1 < n:
        end_text = str(segments[i_end].get("text", ""))
        if not _needs_expand_end(end_text):
            break
        trial = i_end + 1
        if _span_duration(segments, i_start, trial) > duration_max_sec:
            break
        i_end = trial
        flags["expanded_end_segments"] += 1

    # Soft preference: if still short of preferred band and end is OK but we can
    # include one more complete sentence forward without exceeding max, do it
    # only when current duration < preferred_min (handled by caller via config).
    return i_start, i_end, flags


# Back-compat alias used by older tests
def refine_boundaries(
    i_start: int,
    i_end: int,
    segments: Sequence[Mapping[str, Any]],
    *,
    duration_max_sec: float,
) -> tuple[int, int, dict[str, bool]]:
    """Legacy ±1-style API wrapping multi-segment completion."""
    a, b, counts = complete_narrative_unit(
        i_start, i_end, segments, duration_max_sec=duration_max_sec
    )
    return (
        a,
        b,
        {
            "expanded_start_back": counts["expanded_start_segments"] > 0,
            "expanded_end_forward": counts["expanded_end_segments"] > 0,
        },
    )


def snap_candidate_to_segments(
    raw: RawCandidate,
    segments: Sequence[Mapping[str, Any]],
    *,
    config: RankingConfig,
) -> dict[str, Any] | None:
    """Snap/expand/complete one raw candidate onto ASR boundaries. None = reject."""
    if not segments:
        return None

    i_start = _nearest_segment_index(segments, raw.start)
    i_end = _nearest_segment_index(segments, raw.end)
    if i_end < i_start:
        i_start, i_end = i_end, i_start

    while (
        _span_duration(segments, i_start, i_end) < config.duration_min_sec
        and i_end + 1 < len(segments)
    ):
        i_end += 1

    while (
        _span_duration(segments, i_start, i_end) > config.duration_max_sec
        and i_end > i_start
    ):
        i_end -= 1

    i_start, i_end, expand_counts = complete_narrative_unit(
        i_start,
        i_end,
        segments,
        duration_max_sec=config.duration_max_sec,
    )

    # Soft grow toward preferred_min ONLY while the unit still looks incomplete
    # (prefer a closed ~45–60s idea over a truncated short — never force-pad
    # an already-closed unit).
    while (
        _span_duration(segments, i_start, i_end) < config.preferred_duration_min_sec
        and i_end + 1 < len(segments)
        and _span_duration(segments, i_start, i_end + 1) <= config.duration_max_sec
        and _needs_expand_end(str(segments[i_end].get("text", "")))
    ):
        i_end += 1
        expand_counts["expanded_end_segments"] += 1

    while (
        _span_duration(segments, i_start, i_end) > config.duration_max_sec
        and i_end > i_start
    ):
        i_end -= 1

    duration = _span_duration(segments, i_start, i_end)
    if duration < config.duration_min_sec or duration > config.duration_max_sec:
        return None

    start = float(segments[i_start]["start"])
    end = float(segments[i_end]["end"])
    transcript = _join_transcript(segments, i_start, i_end)
    start_text = str(segments[i_start].get("text", ""))
    end_text = str(segments[i_end].get("text", ""))

    dims = raw.scores if isinstance(raw.scores, ScoreDimensions) else ScoreDimensions()
    final_score, penalty, penalty_reasons = compose_final_score(
        dims,
        start_text=start_text,
        end_text=end_text,
        full_transcript=transcript,
        payoff_text=raw.payoff,
        duration_sec=duration,
        preferred_min=config.preferred_duration_min_sec,
        preferred_max=config.preferred_duration_max_sec,
    )

    # Prefer LLM score only as a seed; final is dimension+penalty composed
    # Blend lightly with raw.score if LLM provided an overall
    if raw.score > 0:
        final_score = max(0.0, min(1.0, 0.85 * final_score + 0.15 * float(raw.score)))

    return {
        "start": start,
        "end": end,
        "duration_sec": round(end - start, 3),
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
        "segment_id_start": int(segments[i_start]["id"]),
        "segment_id_end": int(segments[i_end]["id"]),
        "boundary_refined": bool(
            expand_counts["expanded_start_segments"]
            or expand_counts["expanded_end_segments"]
        ),
        "expanded_start_segments": expand_counts["expanded_start_segments"],
        "expanded_end_segments": expand_counts["expanded_end_segments"],
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
            # Penalize near-duplicate ideas vs already kept (better-resolved wins)
            dup = duplicate_idea_penalty(cand, kept)
            item = dict(cand)
            if dup > 0:
                item["score"] = max(0.0, float(item["score"]) - dup)
                reasons = list(item.get("penalty_reasons") or [])
                reasons.append("duplicate_of_better_resolved_idea")
                item["penalty_reasons"] = reasons
                item["score_penalty"] = round(float(item.get("score_penalty") or 0) + dup, 4)
            kept.append(item)
    # Re-sort after duplicate penalties
    kept.sort(key=lambda c: float(c["score"]), reverse=True)
    # Second pass NMS-style drop of heavily penalized dups that now score poorly
    # Keep order; if duplicate flag and score collapsed below 0.25 vs peer, drop
    final: list[dict[str, Any]] = []
    for cand in kept:
        if (
            "duplicate_of_better_resolved_idea" in (cand.get("penalty_reasons") or [])
            and float(cand["score"]) < 0.35
        ):
            continue
        # re-check IoU against final (scores may have reordered)
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
    """Full chain: snap → multi-expand → score → filter → NMS → top N → ids."""
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
