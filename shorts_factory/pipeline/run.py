"""Milestone 1 orchestrator: video → transcript.json + captions.srt."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from shorts_factory.backends.faster_whisper import FasterWhisperBackend
from shorts_factory.backends.transcription import TranscriptionBackend
from shorts_factory.config import PathsConfig, sanitize_source_name
from shorts_factory.pipeline.captions import write_srt
from shorts_factory.pipeline.extract_audio import extract_audio
from shorts_factory.pipeline.transcribe import transcribe_audio
from shorts_factory.pipeline.validate import VideoInfo, validate_video

logger = logging.getLogger(__name__)

# Artifact names (documented in README) — keep stable for milestone 1
TRANSCRIPT_JSON = "transcript.json"
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


def run_milestone1(
    video: str | Path,
    paths: PathsConfig,
    *,
    backend: Optional[TranscriptionBackend] = None,
    keep_audio: bool = True,
    source_name: Optional[str] = None,
) -> Milestone1Result:
    """Run milestone 1 only: ingest → audio → ASR → transcript.json + captions.srt.

    Does **not** select candidates, extract clips, reframe, or burn-in captions.
    """
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
