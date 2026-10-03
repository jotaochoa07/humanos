"""Span helpers for m2-v4 semantic editing (1–3 narrative spans).

Schema (documented):
  role ∈ {hook, context, development, payoff}
  1–3 spans per candidate, original temporal order, gaps allowed.
  duration_sec = sum(span durations); never invent speech.
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from shorts_factory.backends.ranking import SPAN_ROLES, RankingConfig, RawCandidate, RawSpan
from shorts_factory.pipeline.text_heuristics import (
    looks_like_mid_sentence_start,
    looks_like_sentence_end,
)

_ROLE_ALIASES = {
    "hook": "hook",
    "context": "context",
    "development": "development",
    "payoff": "payoff",
    "conclusion": "payoff",
    "thesis": "development",
    "idea": "development",
    "context_development": "development",
    "context/development": "development",
    "setup": "context",
    "unit": "development",  # single continuous closed unit
    "full": "development",
}


def normalize_role(role: str) -> str | None:
    key = (role or "").strip().lower().replace(" ", "_")
    return _ROLE_ALIASES.get(key)


def _nearest_segment_index(
    segments: Sequence[Mapping[str, Any]],
    t: float,
    *,
    as_end: bool = False,
) -> int:
    """Pick ASR segment for time *t*.

    On exact boundaries, prefer the segment that *starts* at t (for span starts)
    or *ends* at t (for span ends) so adjacent spans do not steal each other's
    edges via refine.
    """
    containing: list[int] = []
    for i, seg in enumerate(segments):
        start = float(seg["start"])
        end = float(seg["end"])
        if start <= t <= end:
            containing.append(i)
    if containing:
        if as_end:
            for i in containing:
                if abs(float(segments[i]["end"]) - t) <= 1e-9:
                    return i
            return containing[-1]
        for i in containing:
            if abs(float(segments[i]["start"]) - t) <= 1e-9:
                return i
        return containing[0]

    best_i = 0
    best_dist = float("inf")
    for i, seg in enumerate(segments):
        start = float(seg["start"])
        end = float(seg["end"])
        dist = start - t if t < start else t - end
        if dist < best_dist:
            best_dist = dist
            best_i = i
    return best_i


def _join_transcript(segments: Sequence[Mapping[str, Any]], i0: int, i1: int) -> str:
    parts = [str(segments[i].get("text", "")).strip() for i in range(i0, i1 + 1)]
    return " ".join(p for p in parts if p)


def snap_span_to_segments(
    start: float,
    end: float,
    segments: Sequence[Mapping[str, Any]],
    *,
    light_refine: bool = True,
) -> dict[str, Any] | None:
    """Snap one span to ASR boundaries with light ±1 sentence refine only.

    Does **not** expand toward 80–90s. Completeness comes from other spans /
    gaps, not from stuffing interstitial filler into one continuous range.
    """
    if not segments or end <= start:
        return None
    i0 = _nearest_segment_index(segments, start, as_end=False)
    i1 = _nearest_segment_index(segments, end, as_end=True)
    if i1 < i0:
        i0, i1 = i1, i0

    if light_refine:
        # At most ±1 segment for mid-sentence edges (not multi-expand to 80–90s)
        start_text = str(segments[i0].get("text", ""))
        if looks_like_mid_sentence_start(start_text) and i0 > 0:
            i0 -= 1
        end_text = str(segments[i1].get("text", ""))
        if not looks_like_sentence_end(end_text) and i1 + 1 < len(segments):
            i1 += 1

    if i1 < i0:
        return None
    s = float(segments[i0]["start"])
    e = float(segments[i1]["end"])
    if e <= s:
        return None
    return {
        "start": s,
        "end": e,
        "duration_sec": round(e - s, 3),
        "transcript": _join_transcript(segments, i0, i1),
        "segment_id_start": int(segments[i0]["id"]),
        "segment_id_end": int(segments[i1]["id"]),
        "_i0": i0,
        "_i1": i1,
    }


def synthesize_spans_from_envelope(raw: RawCandidate) -> list[RawSpan]:
    """If LLM omitted spans, treat start/end as one continuous development span."""
    if raw.spans:
        return list(raw.spans)
    return [RawSpan(role="development", start=raw.start, end=raw.end)]


def parse_raw_spans(item: Mapping[str, Any], *, start: float, end: float) -> list[RawSpan]:
    """Parse spans list from LLM JSON; fall back to single envelope span."""
    raw_spans = item.get("spans")
    if not isinstance(raw_spans, list) or not raw_spans:
        return [RawSpan(role="development", start=start, end=end)]
    out: list[RawSpan] = []
    for sp in raw_spans:
        if not isinstance(sp, dict):
            continue
        role = normalize_role(str(sp.get("role") or ""))
        if role is None:
            continue
        try:
            s = float(sp["start"])
            e = float(sp["end"])
        except (KeyError, TypeError, ValueError):
            continue
        if e <= s:
            continue
        out.append(RawSpan(role=role, start=s, end=e))
    if not out:
        return [RawSpan(role="development", start=start, end=end)]
    return out


def validate_and_snap_spans(
    raw_spans: Sequence[RawSpan],
    segments: Sequence[Mapping[str, Any]],
    *,
    config: RankingConfig,
) -> tuple[list[dict[str, Any]], list[str]]:
    """Snap/validate spans. Returns (snapped_spans, errors). Empty spans = reject."""
    errors: list[str] = []
    if not raw_spans:
        return [], ["no spans"]
    if len(raw_spans) > config.max_spans:
        return [], [f"too many spans ({len(raw_spans)} > {config.max_spans})"]

    snapped: list[dict[str, Any]] = []
    for i, sp in enumerate(raw_spans):
        role = normalize_role(sp.role)
        if role is None or role not in SPAN_ROLES:
            errors.append(f"span[{i}] invalid role {sp.role!r}")
            continue
        piece = snap_span_to_segments(sp.start, sp.end, segments, light_refine=True)
        if piece is None:
            errors.append(f"span[{i}] failed ASR snap")
            continue
        piece["role"] = role
        snapped.append(piece)

    if not snapped:
        return [], errors or ["no valid spans after snap"]

    # Temporal order (by start)
    for a, b in zip(snapped, snapped[1:]):
        if float(b["start"]) < float(a["start"]):
            errors.append("spans not in temporal order")
            return [], errors

    # Resolve refine-induced overlaps by trimming the earlier span's end to the
    # next span's start (preserve gap-cutting intent; never invent speech).
    for i in range(len(snapped) - 1):
        a, b = snapped[i], snapped[i + 1]
        if float(b["start"]) < float(a["end"]) - 1e-9:
            new_end = float(b["start"])
            if new_end <= float(a["start"]) + 1e-6:
                errors.append("overlapping spans")
                return [], errors
            # Trim using segment ends ≤ new_end
            i0 = int(a["_i0"])
            i1 = int(a["_i1"])
            while i1 > i0 and float(segments[i1]["end"]) > new_end + 1e-9:
                i1 -= 1
            # If still past next start, clamp end time to next start
            a["end"] = min(float(segments[i1]["end"]), new_end)
            if a["end"] <= float(a["start"]):
                errors.append("overlapping spans")
                return [], errors
            a["_i1"] = i1
            a["segment_id_end"] = int(segments[i1]["id"])
            a["duration_sec"] = round(float(a["end"]) - float(a["start"]), 3)
            a["transcript"] = _join_transcript(segments, i0, i1)

    # Strip internal indices before return
    clean: list[dict[str, Any]] = []
    for s in snapped:
        item = {k: v for k, v in s.items() if not k.startswith("_")}
        clean.append(item)

    total = sum(float(s["duration_sec"]) for s in clean)
    if total < config.duration_min_sec:
        errors.append(f"total duration {total:.1f}s < min {config.duration_min_sec}")
        return [], errors
    if total > config.duration_max_sec:
        errors.append(f"total duration {total:.1f}s > max {config.duration_max_sec}")
        return [], errors

    return clean, errors


def envelope_and_total(spans: Sequence[Mapping[str, Any]]) -> tuple[float, float, float]:
    """Return (envelope_start, envelope_end, spoken_duration_sum)."""
    starts = [float(s["start"]) for s in spans]
    ends = [float(s["end"]) for s in spans]
    total = sum(float(s["end"]) - float(s["start"]) for s in spans)
    return min(starts), max(ends), round(total, 3)


def interstitial_gap_sec(spans: Sequence[Mapping[str, Any]]) -> float:
    """Sum of gaps between consecutive spans (filler cut out)."""
    if len(spans) < 2:
        return 0.0
    gaps = 0.0
    for a, b in zip(spans, spans[1:]):
        gap = float(b["start"]) - float(a["end"])
        if gap > 0:
            gaps += gap
    return round(gaps, 3)
