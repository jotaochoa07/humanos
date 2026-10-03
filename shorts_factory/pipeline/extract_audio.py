"""Extract mono WAV audio from a source video via ffmpeg."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


class AudioExtractionError(RuntimeError):
    """Raised when ffmpeg audio extraction fails."""


def extract_audio(
    video_path: Path,
    audio_out: Path,
    *,
    ffmpeg_bin: str = "ffmpeg",
    sample_rate: int = 16000,
) -> Path:
    """Extract mono PCM WAV suitable for Whisper from *video_path* → *audio_out*."""
    video_path = Path(video_path)
    audio_out = Path(audio_out)
    audio_out.parent.mkdir(parents=True, exist_ok=True)

    if not shutil.which(ffmpeg_bin) and not Path(ffmpeg_bin).exists():
        raise AudioExtractionError(
            f"ffmpeg not found ({ffmpeg_bin!r}). Install system ffmpeg or set HUMANOS_FFMPEG."
        )

    cmd = [
        ffmpeg_bin,
        "-y",
        "-i",
        str(video_path),
        "-vn",
        "-ac",
        "1",
        "-ar",
        str(sample_rate),
        "-c:a",
        "pcm_s16le",
        str(audio_out),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0 or not audio_out.is_file():
        raise AudioExtractionError(
            "ffmpeg audio extraction failed:\n"
            + (proc.stderr.strip() or proc.stdout.strip() or f"exit {proc.returncode}")
        )
    return audio_out
