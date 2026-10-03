"""SRT caption generation from transcript segments (milestone 1 sidecar)."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Mapping, Sequence, Union

SegmentLike = Union[Mapping[str, object], object]


def _get(seg: SegmentLike, key: str):
    if isinstance(seg, Mapping):
        return seg[key]
    return getattr(seg, key)


def format_srt_timestamp(seconds: float) -> str:
    """Format seconds as SRT timestamp ``HH:MM:SS,mmm``."""
    if seconds < 0:
        seconds = 0.0
    total_ms = int(round(float(seconds) * 1000.0))
    hours, rem = divmod(total_ms, 3_600_000)
    minutes, rem = divmod(rem, 60_000)
    secs, ms = divmod(rem, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{ms:03d}"


def segments_to_srt(segments: Sequence[SegmentLike] | Iterable[SegmentLike]) -> str:
    """Convert timed segments to an SRT document string."""
    blocks: list[str] = []
    for i, seg in enumerate(segments, start=1):
        start = float(_get(seg, "start"))
        end = float(_get(seg, "end"))
        text = str(_get(seg, "text") or "").strip()
        if not text:
            continue
        idx = _get(seg, "id") if _has(seg, "id") else i
        try:
            idx_int = int(idx)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            idx_int = i
        blocks.append(
            f"{idx_int}\n"
            f"{format_srt_timestamp(start)} --> {format_srt_timestamp(end)}\n"
            f"{text}"
        )
    return "\n\n".join(blocks) + ("\n" if blocks else "")


def _has(seg: SegmentLike, key: str) -> bool:
    if isinstance(seg, Mapping):
        return key in seg
    return hasattr(seg, key)


def write_srt(segments: Sequence[SegmentLike] | Iterable[SegmentLike], path: Path) -> Path:
    """Write captions.srt (or any path) from segments."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(segments_to_srt(segments), encoding="utf-8")
    return path
