"""Candidate ranking backend protocol — pluggable analysis (M2).

AI is used only for comprehension / proposal of moments.
Timestamps are always grounded and snapped to ASR segment boundaries
in deterministic post-steps (see pipeline/postprocess.py).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Mapping, Optional, Sequence


@dataclass(frozen=True)
class RankingConfig:
    """Knobs for candidate detection / ranking."""

    duration_min_sec: float = 20.0
    duration_max_sec: float = 90.0
    target_count: int = 8
    overlap_iou_threshold: float = 0.45
    model: Optional[str] = None  # LLM model id when using OpenRouter


@dataclass
class RawCandidate:
    """Unvalidated proposal from a ranker (timestamps may be approximate)."""

    start: float
    end: float
    hook: str
    central_idea: str
    selection_reason: str
    score: float
    suggested_title: str
    transcript: str = ""  # optional; filled from ASR if empty
    extra: Mapping[str, Any] = field(default_factory=dict)


class CandidateRanker(ABC):
    """Abstract analysis/ranking interface used by milestone 2."""

    @abstractmethod
    def propose_candidates(
        self,
        transcript: Mapping[str, Any],
        *,
        config: RankingConfig,
    ) -> Sequence[RawCandidate]:
        """Propose raw short candidates from a transcript document.

        Implementations must NOT cut video. They may return approximate
        start/end times; the pipeline snaps them to ASR segment boundaries.
        """
