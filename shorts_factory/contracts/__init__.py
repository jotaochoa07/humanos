"""Transcript + candidates data contracts for Shorts Factory."""

from __future__ import annotations

from typing import Any, TypedDict

from shorts_factory.backends.ranking import RankingConfig


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


class ScoreDimensionsDict(TypedDict, total=False):
    hook_strength: float
    context_completeness: float
    conceptual_completeness: float
    standalone_clarity: float
    payoff_strength: float


class CandidateItem(TypedDict, total=False):
    id: str
    start: float
    end: float
    duration_sec: float
    transcript: str
    hook: str
    minimum_context: str
    central_idea: str
    idea_development: str
    payoff: str
    selection_reason: str
    score: float
    scores: ScoreDimensionsDict
    score_penalty: float
    penalty_reasons: list[str]
    suggested_title: str
    folder: str
    segment_id_start: int
    segment_id_end: int
    boundary_refined: bool
    expanded_start_segments: int
    expanded_end_segments: int
    clip_horizontal: str


class CandidatesDocument(TypedDict, total=False):
    source_video: str
    generated_at: str
    milestone: int
    ranker: str
    snap_rules_version: str
    config: dict[str, Any]
    candidates: list[CandidateItem]


REQUIRED_TOP_LEVEL = (
    "source_video",
    "duration_sec",
    "language",
    "engine",
    "segments",
)
REQUIRED_SEGMENT = ("id", "start", "end", "text")

REQUIRED_CANDIDATES_TOP = (
    "source_video",
    "generated_at",
    "config",
    "candidates",
)
REQUIRED_CANDIDATE = (
    "id",
    "start",
    "end",
    "duration_sec",
    "transcript",
    "hook",
    "central_idea",
    "selection_reason",
    "score",
    "suggested_title",
)

# m2-v3 score dimension keys (required when snap_rules_version == m2-v3)
SCORE_DIMENSION_KEYS = (
    "hook_strength",
    "context_completeness",
    "conceptual_completeness",
    "standalone_clarity",
    "payoff_strength",
)


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


def validate_candidates_shape(doc: Any) -> list[str]:
    """Return validation errors for candidates.json (empty = OK)."""
    errors: list[str] = []
    if not isinstance(doc, dict):
        return ["candidates document must be a JSON object"]
    for key in REQUIRED_CANDIDATES_TOP:
        if key not in doc:
            errors.append(f"missing top-level key: {key}")
    cfg = doc.get("config")
    if cfg is not None and not isinstance(cfg, dict):
        errors.append("config must be an object")
    elif isinstance(cfg, dict):
        for key in ("duration_min_sec", "duration_max_sec", "target_count"):
            if key not in cfg:
                errors.append(f"config missing key: {key}")
    require_scores = str(doc.get("snap_rules_version") or "") == "m2-v3"
    cands = doc.get("candidates")
    if cands is None:
        return errors
    if not isinstance(cands, list):
        errors.append("candidates must be a list")
        return errors
    for i, item in enumerate(cands):
        if not isinstance(item, dict):
            errors.append(f"candidates[{i}] must be an object")
            continue
        for key in REQUIRED_CANDIDATE:
            if key not in item:
                errors.append(f"candidates[{i}] missing key: {key}")
        if "start" in item and "end" in item:
            try:
                if float(item["end"]) < float(item["start"]):
                    errors.append(f"candidates[{i}] end < start")
            except (TypeError, ValueError):
                errors.append(f"candidates[{i}] start/end must be numbers")
        if "score" in item:
            try:
                score = float(item["score"])
                if score < 0 or score > 1:
                    errors.append(f"candidates[{i}] score out of range [0,1]")
            except (TypeError, ValueError):
                errors.append(f"candidates[{i}] score must be a number")
        if require_scores:
            scores = item.get("scores")
            if not isinstance(scores, dict):
                errors.append(f"candidates[{i}] missing scores object (m2-v3)")
            else:
                for key in SCORE_DIMENSION_KEYS:
                    if key not in scores:
                        errors.append(f"candidates[{i}].scores missing {key}")
                    else:
                        try:
                            v = float(scores[key])
                            if v < 0 or v > 1:
                                errors.append(
                                    f"candidates[{i}].scores.{key} out of range"
                                )
                        except (TypeError, ValueError):
                            errors.append(
                                f"candidates[{i}].scores.{key} must be a number"
                            )
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


def build_candidates_document(
    *,
    source_video: str,
    generated_at: str,
    config: RankingConfig,
    candidates: list[dict[str, Any]],
    ranker: str,
    snap_rules_version: str = "m2-v3",
) -> CandidatesDocument:
    return {
        "source_video": source_video,
        "generated_at": generated_at,
        "milestone": 2,
        "ranker": ranker,
        "snap_rules_version": snap_rules_version,
        "config": {
            "duration_min_sec": float(config.duration_min_sec),
            "duration_max_sec": float(config.duration_max_sec),
            "preferred_duration_min_sec": float(config.preferred_duration_min_sec),
            "preferred_duration_max_sec": float(config.preferred_duration_max_sec),
            "target_count": int(config.target_count),
            "overlap_iou_threshold": float(config.overlap_iou_threshold),
            "editorial_criteria": "self_contained_narrative_unit",
        },
        "candidates": list(candidates),
    }
