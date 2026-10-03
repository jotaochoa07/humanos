"""Transcript data contract for Shorts Factory milestone 1."""

from __future__ import annotations

from typing import Any, TypedDict


class TranscriptSegment(TypedDict):
    id: int
    start: float
    end: float
    text: str


class TranscriptDocument(TypedDict):
    source_video: str
    duration_sec: float
    language: str
    engine: str
    model: str
    device: str
    compute_type: str
    segments: list[TranscriptSegment]


REQUIRED_TOP_LEVEL = (
    "source_video",
    "duration_sec",
    "language",
    "engine",
    "segments",
)
REQUIRED_SEGMENT = ("id", "start", "end", "text")


def validate_transcript_shape(doc: Any) -> list[str]:
    """Return a list of validation errors (empty = OK). Does not raise."""
    errors: list[str] = []
    if not isinstance(doc, dict):
        return ["transcript must be a JSON object"]
    for key in REQUIRED_TOP_LEVEL:
        if key not in doc:
            errors.append(f"missing top-level key: {key}")
    if "duration_sec" in doc and not isinstance(doc["duration_sec"], (int, float)):
        errors.append("duration_sec must be a number")
    segments = doc.get("segments")
    if segments is None:
        return errors
    if not isinstance(segments, list):
        errors.append("segments must be a list")
        return errors
    for i, seg in enumerate(segments):
        if not isinstance(seg, dict):
            errors.append(f"segments[{i}] must be an object")
            continue
        for key in REQUIRED_SEGMENT:
            if key not in seg:
                errors.append(f"segments[{i}] missing key: {key}")
        if "start" in seg and "end" in seg:
            try:
                if float(seg["end"]) < float(seg["start"]):
                    errors.append(f"segments[{i}] end < start")
            except (TypeError, ValueError):
                errors.append(f"segments[{i}] start/end must be numbers")
    return errors


def build_transcript_document(
    *,
    source_video: str,
    duration_sec: float,
    language: str,
    engine: str,
    model: str,
    device: str,
    compute_type: str,
    segments: list[TranscriptSegment],
) -> TranscriptDocument:
    return {
        "source_video": source_video,
        "duration_sec": float(duration_sec),
        "language": language,
        "engine": engine,
        "model": model,
        "device": device,
        "compute_type": compute_type,
        "segments": segments,
    }
