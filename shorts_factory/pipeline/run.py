"""Shorts Factory orchestrators: M1 (transcript) + M2 (candidates) + M3 (clips)."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from shorts_factory.backends.faster_whisper import FasterWhisperBackend
from shorts_factory.backends.openrouter_ranker import OpenRouterCandidateRanker
from shorts_factory.backends.ranking import CandidateRanker, RankingConfig
from shorts_factory.backends.transcription import TranscriptionBackend
from shorts_factory.config import PathsConfig, sanitize_source_name
from shorts_factory.pipeline.analyze import (
    CANDIDATES_JSON,
    TRANSCRIPT_JSON,
    run_candidates_stage,
)
from shorts_factory.pipeline.captions import write_srt
from shorts_factory.pipeline.extract_audio import extract_audio
from shorts_factory.pipeline.extract_clips import Milestone3Result, run_clips_stage
from shorts_factory.pipeline.transcribe import transcribe_audio
from shorts_factory.pipeline.validate import VideoInfo, validate_video

logger = logging.getLogger(__name__)

# Artifact names — keep stable across milestones
CAPTIONS_SRT = "captions.srt"
AUDIO_WAV = "audio.wav"


@dataclass(frozen=True)
class Milestone1Result:
    source_video: Path
    source_name: str
    output_dir: Path
    transcript_json: Path
    captions_srt: Path
    audio_wav: Path
    video_info: VideoInfo
    transcript: dict


@dataclass(frozen=True)
class Milestone2Result:
    source_video: str
    output_dir: Path
    transcript_json: Path
    candidates_json: Path
    document: dict


def build_default_ranker(
    paths: PathsConfig,
    *,
    ranker: Optional[CandidateRanker] = None,
) -> CandidateRanker:
    if ranker is not None:
        return ranker
    backend = (paths.ranker_backend or "openrouter").lower()
    if backend in ("openrouter", "llm", "default"):
        return OpenRouterCandidateRanker()
    raise ValueError(
        f"Unknown ranker backend {paths.ranker_backend!r}. "
        "Supported: openrouter (or inject CandidateRanker)."
    )


def run_milestone1(
    video: str | Path,
    paths: PathsConfig,
    *,
    backend: Optional[TranscriptionBackend] = None,
    keep_audio: bool = True,
    source_name: Optional[str] = None,
) -> Milestone1Result:
    """Run milestone 1 only: ingest → audio → ASR → transcript.json + captions.srt."""
    video_info = validate_video(video, ffmpeg_bin=paths.ffmpeg_bin())
    name = sanitize_source_name(source_name or video_info.path)
    out_dir = paths.source_output_dir(name)
    out_dir.mkdir(parents=True, exist_ok=True)

    audio_path = out_dir / AUDIO_WAV
    transcript_path = out_dir / TRANSCRIPT_JSON
    srt_path = out_dir / CAPTIONS_SRT

    logger.info("Extracting audio → %s", audio_path)
    extract_audio(video_info.path, audio_path, ffmpeg_bin=paths.ffmpeg_bin())

    if backend is None:
        backend = FasterWhisperBackend(download_root=paths.asr_models)

    logger.info(
        "Transcribing with model=%s language=%s device=%s compute_type=%s",
        paths.whisper_model,
        paths.language,
        paths.device,
        paths.compute_type,
    )
    document = transcribe_audio(
        backend,
        audio_path,
        source_video=str(video_info.path),
        duration_sec=video_info.duration_sec,
        language=paths.language,
        model=paths.whisper_model,
        device=paths.device,
        compute_type=paths.compute_type,
        transcript_out=transcript_path,
    )

    write_srt(document["segments"], srt_path)
    logger.info("Wrote %s and %s", transcript_path, srt_path)

    if not keep_audio and audio_path.is_file():
        audio_path.unlink()
        logger.info("Removed intermediate audio %s", audio_path)

    return Milestone1Result(
        source_video=video_info.path,
        source_name=name,
        output_dir=out_dir,
        transcript_json=transcript_path,
        captions_srt=srt_path,
        audio_wav=audio_path,
        video_info=video_info,
        transcript=document,
    )


def run_milestone2(
    paths: PathsConfig,
    *,
    run_dir: Optional[Path] = None,
    from_transcript: Optional[Path] = None,
    ranker: Optional[CandidateRanker] = None,
    ranking_config: Optional[RankingConfig] = None,
) -> Milestone2Result:
    """Run milestone 2 only: transcript.json → candidates.json.

    Does **not** cut/extract video, reframe, burn-in, or invoke Remotion/NLE.
    """
    cfg = ranking_config or paths.ranking_config()
    active_ranker = build_default_ranker(paths, ranker=ranker)
    result = run_candidates_stage(
        ranker=active_ranker,
        config=cfg,
        run_dir=Path(run_dir) if run_dir is not None else None,
        from_transcript=Path(from_transcript) if from_transcript is not None else None,
    )
    doc = result["document"]
    return Milestone2Result(
        source_video=str(doc.get("source_video", "")),
        output_dir=result["output_dir"],
        transcript_json=result["transcript_path"],
        candidates_json=result["candidates_path"],
        document=doc,
    )


def run_milestone3(
    paths: PathsConfig,
    *,
    run_dir: Path,
    video: Optional[Path] = None,
    runner=None,
) -> Milestone3Result:
    """Run milestone 3 only: candidates.json → horizontal clips + meta.json.

    Does **not** reframe 9:16, face-track, burn-in captions, or Remotion/NLE.
    Re-reads possibly hand-edited start/end from candidates.json.
    """
    return run_clips_stage(
        run_dir=Path(run_dir),
        ffmpeg_bin=paths.ffmpeg_bin(),
        video=Path(video) if video is not None else None,
        runner=runner,
    )


def run_shorts_pipeline(
    video: str | Path,
    paths: PathsConfig,
    *,
    backend: Optional[TranscriptionBackend] = None,
    ranker: Optional[CandidateRanker] = None,
    keep_audio: bool = True,
    source_name: Optional[str] = None,
    skip_transcribe: bool = False,
    skip_candidates: bool = False,
    force_transcribe: bool = False,
    with_clips: bool = False,
    clip_runner=None,
) -> tuple[Optional[Milestone1Result], Optional[Milestone2Result], Optional[Milestone3Result]]:
    """Run M1 → M2 (and optionally M3) under outputs/shorts_factory/<source_name>/."""
    video_path = Path(video)
    name = sanitize_source_name(source_name or video_path)
    out_dir = paths.source_output_dir(name)
    transcript_path = out_dir / TRANSCRIPT_JSON

    m1: Optional[Milestone1Result] = None
    need_m1 = force_transcribe or not transcript_path.is_file()
    if skip_transcribe and not transcript_path.is_file():
        raise FileNotFoundError(
            f"--skip-transcribe requires existing {transcript_path}"
        )
    if skip_transcribe:
        need_m1 = False

    if need_m1:
        m1 = run_milestone1(
            video_path,
            paths,
            backend=backend,
            keep_audio=keep_audio,
            source_name=name,
        )
        out_dir = m1.output_dir
    else:
        logger.info("Reusing existing transcript %s", transcript_path)
        out_dir.mkdir(parents=True, exist_ok=True)

    m2: Optional[Milestone2Result] = None
    if not skip_candidates:
        m2 = run_milestone2(paths, run_dir=out_dir, ranker=ranker)

    m3: Optional[Milestone3Result] = None
    if with_clips:
        if skip_candidates and not (out_dir / CANDIDATES_JSON).is_file():
            raise FileNotFoundError(
                f"--with-clips requires {out_dir / CANDIDATES_JSON}"
            )
        m3 = run_milestone3(
            paths,
            run_dir=out_dir,
            video=video_path if video_path.is_file() else None,
            runner=clip_runner,
        )

    return m1, m2, m3
