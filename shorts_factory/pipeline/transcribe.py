"""Transcription stage — wraps TranscriptionBackend → transcript.json."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from shorts_factory.backends.transcription import TranscriptionBackend, TranscriptionResult
from shorts_factory.contracts import TranscriptSegment, build_transcript_document


def result_to_document(
    result: TranscriptionResult,
    *,
    source_video: str,
    duration_sec: float,
) -> dict:
    segments: list[TranscriptSegment] = [
        {
            "id": int(seg.id),
            "start": float(seg.start),
            "end": float(seg.end),
            "text": str(seg.text),
        }
        for seg in result.segments
    ]
    dur = result.duration_sec if result.duration_sec is not None else duration_sec
    return build_transcript_document(
        source_video=source_video,
        duration_sec=float(dur),
        language=result.language,
        engine=result.engine,
        model=result.model,
        device=result.device,
        compute_type=result.compute_type,
        segments=segments,
    )


def write_transcript_json(document: dict, path: Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(document, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def transcribe_audio(
    backend: TranscriptionBackend,
    audio_path: Path,
    *,
    source_video: str,
    duration_sec: float,
    language: str = "auto",
    model: str = "small",
    device: str = "auto",
    compute_type: str = "auto",
    transcript_out: Optional[Path] = None,
) -> dict:
    """Run ASR and optionally persist transcript.json."""
    result = backend.transcribe(
        Path(audio_path),
        language=language,
        model=model,
        device=device,
        compute_type=compute_type,
    )
    document = result_to_document(
        result,
        source_video=source_video,
        duration_sec=duration_sec,
    )
    if transcript_out is not None:
        write_transcript_json(document, transcript_out)
    return document
