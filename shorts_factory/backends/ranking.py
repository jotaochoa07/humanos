"""Candidate ranking backend protocol — pluggable analysis (M2 / m2-v4 spans).

AI proposes self-contained narrative units as 1–3 temporal *spans*
(semantic editing). Timestamps snap to ASR segment boundaries in postprocess.
Score dimensions from m2-v3 are retained.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Literal, Mapping, Optional, Sequence

# Narrative function of each spoken span (documented schema).
# - hook: why keep watching
# - context: minimum problem/situation setup
# - development: idea being explained / argued
# - payoff: conclusion / takeaway
# Single continuous unit that already works → one span with role "development"
# (the whole closed arc in one stretch). Prefer multi-span when filler sits
# between hook/context and payoff.
SpanRole = Literal["hook", "context", "development", "payoff"]
SPAN_ROLES: tuple[str, ...] = ("hook", "context", "development", "payoff")


@dataclass(frozen=True)
class RankingConfig:
    """Knobs for candidate detection / ranking (m2-v4 spans)."""

    duration_min_sec: float = 20.0
    duration_max_sec: float = 90.0  # hard max on *sum of span durations*
    # Soft preference for total spoken duration (sum of spans)
    preferred_duration_min_sec: float = 30.0
    preferred_duration_max_sec: float = 60.0
    target_count: int = 5
    overlap_iou_threshold: float = 0.45
    max_spans: int = 3
    model: Optional[str] = None


@dataclass(frozen=True)
class ScoreDimensions:
    """Per-dimension editorial scores in [0, 1] (m2-v3, retained)."""

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
class RawSpan:
    """One spoken span with a narrative role (approx timestamps from LLM)."""

    role: str
    start: float
    end: float


@dataclass
class RawCandidate:
    """Unvalidated proposal from a ranker (timestamps may be approximate)."""

    start: float  # envelope start (min of spans); kept for compat
    end: float  # envelope end (max of spans)
    hook: str
    central_idea: str
    selection_reason: str
    score: float
    suggested_title: str
    transcript: str = ""
    minimum_context: str = ""
    idea_development: str = ""
    payoff: str = ""
    scores: ScoreDimensions = field(default_factory=ScoreDimensions)
    spans: list[RawSpan] = field(default_factory=list)
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

        Implementations must NOT cut video or invent speech. They may return
        approximate span timestamps; the pipeline snaps them to ASR boundaries.
        """
