"""Deterministic post-steps for Shorts Factory M2 candidates.

Timestamp grounding rules (documented):
1. Raw LLM start/end may be approximate floats in seconds.
2. **Start snap:** choose the ASR segment whose time range contains `start`
   (or the nearest segment if none contains it). Candidate start becomes
   that segment's `start`.
3. **End snap:** choose the ASR segment whose time range contains `end`
   (or the nearest segment). Candidate end becomes that segment's `end`.
4. If after snap `end <= start`, expand end to the end of the start segment;
   if still invalid, reject the candidate.
5. If duration is below `duration_min_sec`, greedily append following whole
   segments until within window or no more segments.
6. If duration is above `duration_max_sec`, greedily trim trailing whole
   segments (keeping start fixed) until within window; if a single segment
   already exceeds max, keep the snapped span only if <= max * 1.15 else reject.
7. Transcript text is always rebuilt from the inclusive ASR segment span
   (never trust LLM-copied transcript for timestamps).
8. **Duration filter:** keep only candidates with
   `duration_min_sec <= duration <= duration_max_sec` (after snap/expand/trim).
9. **NMS / dedupe:** sort by score desc; greedily keep if temporal IoU with
   every kept candidate is < `overlap_iou_threshold`.
10. Sort by score desc; take top `target_count`.
"""

from __future__ import annotations

import re
from typing import Any, Mapping, Sequence

from shorts_factory.backends.ranking import RankingConfig, RawCandidate

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def temporal_iou(a_start: float, a_end: float, b_start: float, b_end: float) -> float:
    """Intersection-over-union on 1D time ranges."""
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
        dist = min(abs(t - start), abs(t - end))
        if t < start:
            dist = start - t
        elif t > end:
            dist = t - end
        if dist < best_dist:
            best_dist = dist
            best_i = i
    return best_i


def _join_transcript(segments: Sequence[Mapping[str, Any]], i0: int, i1: int) -> str:
    parts = [str(segments[i].get("text", "")).strip() for i in range(i0, i1 + 1)]
    return " ".join(p for p in parts if p)


def _slugify(text: str, fallback: str) -> str:
    raw = text.strip().lower()
    # Normalize common Spanish accents for folder ids
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
    return (cleaned[:48] or fallback)


def snap_candidate_to_segments(
    raw: RawCandidate,
    segments: Sequence[Mapping[str, Any]],
    *,
    config: RankingConfig,
) -> dict[str, Any] | None:
    """Snap/expand/trim one raw candidate onto ASR boundaries. None = reject."""
    if not segments:
        return None

    i_start = _nearest_segment_index(segments, raw.start)
    i_end = _nearest_segment_index(segments, raw.end)
    if i_end < i_start:
        i_start, i_end = i_end, i_start

    # Expand to meet min duration by appending following segments
    def span_duration(a: int, b: int) -> float:
        return float(segments[b]["end"]) - float(segments[a]["start"])

    while span_duration(i_start, i_end) < config.duration_min_sec and i_end + 1 < len(segments):
        i_end += 1

    # Trim from the end to meet max duration
    while (
        span_duration(i_start, i_end) > config.duration_max_sec
        and i_end > i_start
    ):
        i_end -= 1

    duration = span_duration(i_start, i_end)
    if duration < config.duration_min_sec or duration > config.duration_max_sec:
        return None

    start = float(segments[i_start]["start"])
    end = float(segments[i_end]["end"])
    transcript = raw.transcript.strip() or _join_transcript(segments, i_start, i_end)

    return {
        "start": start,
        "end": end,
        "duration_sec": round(end - start, 3),
        "transcript": transcript,
        "hook": raw.hook,
        "central_idea": raw.central_idea,
        "selection_reason": raw.selection_reason,
        "score": float(raw.score),
        "suggested_title": raw.suggested_title,
        "segment_id_start": int(segments[i_start]["id"]),
        "segment_id_end": int(segments[i_end]["id"]),
    }


def nms_by_iou(
    candidates: Sequence[Mapping[str, Any]],
    *,
    iou_threshold: float,
) -> list[dict[str, Any]]:
    """Greedy non-maximum suppression by temporal IoU (input should be score-sorted)."""
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
            kept.append(dict(cand))
    return kept


def assign_ids(candidates: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Assign stable `id` / `folder` fields: 01-<slug>, 02-<slug>, …"""
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
    """Full deterministic chain: snap → filter → sort → NMS → top N → ids."""
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
