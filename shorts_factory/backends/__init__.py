"""Shorts Factory backends package."""

from shorts_factory.backends.transcription import (
    TranscriptionBackend,
    TranscriptionResult,
    TranscriptionSegment,
)
from shorts_factory.backends.faster_whisper import FasterWhisperBackend

__all__ = [
    "TranscriptionBackend",
    "TranscriptionResult",
    "TranscriptionSegment",
    "FasterWhisperBackend",
]
