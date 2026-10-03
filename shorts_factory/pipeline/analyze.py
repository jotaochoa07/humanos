"""Milestone 2: transcript.json → candidates.json via CandidateRanker + postprocess."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Optional

from shorts_factory.backends.ranking import CandidateRanker, RankingConfig
from shorts_factory.contracts import (
    build_candidates_document,
    validate_candidates_shape,
    validate_transcript_shape,
)
from shorts_factory.pipeline.postprocess import postprocess_candidates

logger = logging.getLogger(__name__)

CANDIDATES_JSON = "candidates.json"
TRANSCRIPT_JSON = "transcript.json"


def load_transcript_json(path: Path) -> dict[str, Any]:
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"transcript not found: {path}")
    doc = json.loads(path.read_text(encoding="utf-8"))
    errors = validate_transcript_shape(doc)
    if errors:
        raise ValueError("invalid transcript.json: " + "; ".join(errors))
    return doc


def resolve_transcript_path(
    *,
    run_dir: Optional[Path] = None,
    from_transcript: Optional[Path] = None,
) -> Path:
    """Resolve transcript.json from a run directory or explicit path."""
    if from_transcript is not None:
        p = Path(from_transcript)
        if p.is_dir():
            p = p / TRANSCRIPT_JSON
        return p.resolve()
    if run_dir is not None:
        return (Path(run_dir) / TRANSCRIPT_JSON).resolve()
    raise ValueError("Provide run_dir or from_transcript")


def write_candidates_json(document: Mapping[str, Any], path: Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(document, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def analyze_transcript(
    transcript: Mapping[str, Any],
    *,
    ranker: CandidateRanker,
    config: RankingConfig,
    generated_at: Optional[str] = None,
) -> dict[str, Any]:
    """Run ranker + deterministic post-steps → candidates document."""
    errors = validate_transcript_shape(transcript)
    if errors:
        raise ValueError("invalid transcript: " + "; ".join(errors))

    raw = list(ranker.propose_candidates(transcript, config=config))
    logger.info("Ranker proposed %s raw candidates", len(raw))
    candidates = postprocess_candidates(raw, transcript, config=config)
    logger.info("Post-process kept %s candidates", len(candidates))

    ts = generated_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    document = build_candidates_document(
        source_video=str(transcript.get("source_video", "")),
        generated_at=ts,
        config=config,
        candidates=candidates,
        ranker=getattr(ranker, "name", ranker.__class__.__name__),
        snap_rules_version="m2-v1",
    )
    shape_errors = validate_candidates_shape(document)
    if shape_errors:
        raise ValueError("invalid candidates document: " + "; ".join(shape_errors))
    return document


def run_candidates_stage(
    *,
    ranker: CandidateRanker,
    config: RankingConfig,
    run_dir: Optional[Path] = None,
    from_transcript: Optional[Path] = None,
    candidates_out: Optional[Path] = None,
) -> dict[str, Any]:
    """Load transcript, analyze, write candidates.json under the run directory."""
    transcript_path = resolve_transcript_path(
        run_dir=run_dir, from_transcript=from_transcript
    )
    transcript = load_transcript_json(transcript_path)
    out_dir = Path(run_dir) if run_dir is not None else transcript_path.parent
    out_path = Path(candidates_out) if candidates_out else out_dir / CANDIDATES_JSON

    document = analyze_transcript(transcript, ranker=ranker, config=config)
    write_candidates_json(document, out_path)
    logger.info("Wrote %s (%s candidates)", out_path, len(document["candidates"]))
    return {
        "transcript_path": transcript_path,
        "candidates_path": out_path.resolve(),
        "output_dir": out_dir.resolve(),
        "document": document,
    }
