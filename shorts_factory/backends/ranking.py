"""Candidate ranking backend protocol — pluggable analysis (M2 / m2-v3).

AI is used for comprehension / proposal of self-contained narrative units.
Timestamps are grounded and expanded to ASR segment boundaries in
deterministic post-steps (see pipeline/postprocess.py).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Mapping, Optional, Sequence


@dataclass(frozen=True)
class RankingConfig:
    """Knobs for candidate detection / ranking (m2-v3)."""

    duration_min_sec: float = 20.0
    duration_max_sec: float = 90.0
    # Soft preference: prefer well-closed ~45–60s units over incomplete shorts
    preferred_duration_min_sec: float = 45.0
    preferred_duration_max_sec: float = 60.0
    # Fewer clips, more self-contained (m2-v3 philosophy)
    target_count: int = 5
    overlap_iou_threshold: float = 0.45
    model: Optional[str] = None  # LLM model id when using OpenRouter


@dataclass(frozen=True)
class ScoreDimensions:
    """Per-dimension editorial scores in [0, 1]."""

    hook_strength: float = 0.5
    context_completeness: float = 0.5
    conceptual_completeness: float = 0.5
    standalone_clarity: float = 0.5
    payoff_strength: float = 0.5

    def as_dict(self) -> dict[str, float]:
        return {
            "hook_strength": float(self.hook_strength),
            "context_completeness": float(self.context_completeness),
            "conceptual_completeness": float(self.conceptual_completeness),
            "standalone_clarity": float(self.standalone_clarity),
            "payoff_strength": float(self.payoff_strength),
        }


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
    transcript: str = ""
    # Narrative unit fields (m2-v3)
    minimum_context: str = ""
    idea_development: str = ""
    payoff: str = ""
    scores: ScoreDimensions = field(default_factory=ScoreDimensions)
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
        start/end times; the pipeline snaps/expands them to ASR boundaries.
        """
