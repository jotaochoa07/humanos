"""Transcription backend protocol — pluggable ASR (SF3).

Default v0: FasterWhisperBackend.
Future: medium / large-v3 / API backends without rewriting the pipeline.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Sequence


@dataclass(frozen=True)
class TranscriptionSegment:
    id: int
    start: float
    end: float
    text: str


@dataclass(frozen=True)
class TranscriptionResult:
    language: str
    segments: Sequence[TranscriptionSegment]
    engine: str
    model: str
    device: str
    compute_type: str
    duration_sec: Optional[float] = None


class TranscriptionBackend(ABC):
    """Abstract transcription interface used by the pipeline."""

    @abstractmethod
    def transcribe(
        self,
        audio_path: Path,
        *,
        language: str = "auto",
        model: str = "small",
        device: str = "auto",
        compute_type: str = "auto",
    ) -> TranscriptionResult:
        """Transcribe *audio_path* and return timed segments."""
