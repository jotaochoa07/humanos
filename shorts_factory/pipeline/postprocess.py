"""Deterministic post-steps for Shorts Factory M2 candidates.

Timestamp grounding rules (`snap_rules_version: m2-v2`):
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
   segments (keeping start fixed) until within window.
7. **Boundary refinement (±1 segment max)** — after duration snap/trim, improve
   self-containment using ASR segment *text* heuristics (does **not** change
   the ranker model/prompt):
   a. **Start looks mid-sentence** if the first segment text:
      - starts with a lowercase letter (incl. Spanish áéíóúñü), OR
      - starts with a mid-thought cue (`y`, `pero`, `porque`, `que`, `and`, …)
      after stripping opening quotes/¿¡.
      → If true and `i_start > 0`, expand **one** segment backward **only if**
      the new duration stays ≤ `duration_max_sec`.
   b. **End looks incomplete** if the last segment text does **not** end with
      terminal punctuation (`.?!…` optionally followed by quotes/brackets)
      after stripping trailing whitespace.
      → If true and a next segment exists, expand **one** segment forward
      **only if** the new duration stays ≤ `duration_max_sec`.
   c. At most one expand backward and one expand forward (never ±2).
   d. Prefer not expanding when the adjacent segment would clearly worsen
      containment (e.g. backward expand into a segment that itself ends with
      strong terminal punctuation *and* current start already looks like a
      sentence start — skipped via the mid-sentence check).
8. Transcript text is always rebuilt from the inclusive ASR segment span
   (never trust LLM-copied transcript for timestamps).
9. **Duration filter:** keep only candidates with
   `duration_min_sec <= duration <= duration_max_sec` (after snap/refine).
10. **NMS / dedupe:** sort by score desc; greedily keep if temporal IoU with
    every kept candidate is < `overlap_iou_threshold`.
11. Sort by score desc; take top `target_count`.
"""

from __future__ import annotations

import re
from typing import Any, Mapping, Sequence

from shorts_factory.backends.ranking import RankingConfig, RawCandidate

_SLUG_RE = re.compile(r"[^a-z0-9]+")

# Terminal sentence endings (ES/EN). Optional closing quotes/brackets after.
_TERMINAL_END_RE = re.compile(
    r'[.!?…]+["\'”’»)\]\}]*\s*$'
)

# Opening fluff stripped before start-of-sentence checks
_OPEN_STRIP_RE = re.compile(r'^[\s"\'“”‘’¿¡(\[]+')

# Mid-thought openers (lowercase, word boundary). Not a full NLP parse —
# conservative cues that the clip starts mid-clause.
_MID_THOUGHT_STARTERS = frozenset(
    {
        "y",
        "e",
        "o",
        "u",
        "pero",
        "porque",
        "que",
        "sino",
        "aunque",
        "entonces",
        "ademas",
        "además",
        "tambien",
        "también",
        "luego",
        "asi",
        "así",
        "and",
        "but",
        "because",
        "so",
        "then",
        "which",
        "where",
        "when",
    }
)


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


def looks_like_sentence_end(text: str) -> bool:
    """True if *text* ends with terminal punctuation (complete thought)."""
    t = (text or "").strip()
    if not t:
        return False
    return bool(_TERMINAL_END_RE.search(t))


def looks_like_mid_sentence_start(text: str) -> bool:
    """True if *text* likely begins mid-thought (bad clip start)."""
    t = (text or "").strip()
    if not t:
        return True
    stripped = _OPEN_STRIP_RE.sub("", t)
    if not stripped:
        return True
    first = stripped[0]
    # Lowercase letter start → mid-thought (ASR often drops capitals, but we
    # still treat clear lowercase as a signal when present).
    if first.isalpha() and first == first.lower() and first != first.upper():
        return True
    # Mid-thought cue words even if capitalized oddly
    first_word = re.split(r"\s+", stripped, maxsplit=1)[0]
    first_word = re.sub(r"[^\wáéíóúñüÁÉÍÓÚÑÜ]+$", "", first_word, flags=re.UNICODE)
    if first_word.lower() in _MID_THOUGHT_STARTERS:
        return True
    return False


def _span_duration(segments: Sequence[Mapping[str, Any]], a: int, b: int) -> float:
    return float(segments[b]["end"]) - float(segments[a]["start"])


def refine_boundaries(
    i_start: int,
    i_end: int,
    segments: Sequence[Mapping[str, Any]],
    *,
    duration_max_sec: float,
) -> tuple[int, int, dict[str, bool]]:
    """Expand by at most ±1 ASR segment to avoid mid-sentence cuts.

    Returns (new_start_idx, new_end_idx, flags).
    """
    flags = {"expanded_start_back": False, "expanded_end_forward": False}
    n = len(segments)
    if n == 0 or i_start < 0 or i_end < i_start:
        return i_start, i_end, flags

    start_text = str(segments[i_start].get("text", ""))
    if looks_like_mid_sentence_start(start_text) and i_start > 0:
        trial = i_start - 1
        if _span_duration(segments, trial, i_end) <= duration_max_sec:
            i_start = trial
            flags["expanded_start_back"] = True

    end_text = str(segments[i_end].get("text", ""))
    if not looks_like_sentence_end(end_text) and i_end + 1 < n:
        trial = i_end + 1
        if _span_duration(segments, i_start, trial) <= duration_max_sec:
            i_end = trial
            flags["expanded_end_forward"] = True

    return i_start, i_end, flags


def snap_candidate_to_segments(
    raw: RawCandidate,
    segments: Sequence[Mapping[str, Any]],
    *,
    config: RankingConfig,
) -> dict[str, Any] | None:
    """Snap/expand/trim/refine one raw candidate onto ASR boundaries. None = reject."""
    if not segments:
        return None

    i_start = _nearest_segment_index(segments, raw.start)
    i_end = _nearest_segment_index(segments, raw.end)
    if i_end < i_start:
        i_start, i_end = i_end, i_start

    # Expand to meet min duration by appending following segments
    while (
        _span_duration(segments, i_start, i_end) < config.duration_min_sec
        and i_end + 1 < len(segments)
    ):
        i_end += 1

    # Trim from the end to meet max duration
    while (
        _span_duration(segments, i_start, i_end) > config.duration_max_sec
        and i_end > i_start
    ):
        i_end -= 1

    # Boundary refinement (±1 segment) for sentence self-containment
    i_start, i_end, refine_flags = refine_boundaries(
        i_start,
        i_end,
        segments,
        duration_max_sec=config.duration_max_sec,
    )

    # If refinement pushed over max, trim end again (keep refined start if possible)
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
        "boundary_refined": bool(
            refine_flags["expanded_start_back"] or refine_flags["expanded_end_forward"]
        ),
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
    """Full deterministic chain: snap → refine → filter → sort → NMS → top N → ids."""
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
