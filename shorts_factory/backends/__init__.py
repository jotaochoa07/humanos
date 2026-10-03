"""Shorts Factory backends package."""

from shorts_factory.backends.faster_whisper import FasterWhisperBackend
from shorts_factory.backends.openrouter_ranker import OpenRouterCandidateRanker
from shorts_factory.backends.ranking import (
    CandidateRanker,
    RankingConfig,
    RawCandidate,
    ScoreDimensions,
)
from shorts_factory.backends.transcription import (
    TranscriptionBackend,
    TranscriptionResult,
    TranscriptionSegment,
)

__all__ = [
    "TranscriptionBackend",
    "TranscriptionResult",
    "TranscriptionSegment",
    "FasterWhisperBackend",
    "CandidateRanker",
    "RankingConfig",
    "RawCandidate",
    "ScoreDimensions",
    "OpenRouterCandidateRanker",
]
