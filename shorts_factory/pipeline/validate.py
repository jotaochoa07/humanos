"""Validate source video for Shorts Factory ingest."""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".webm", ".m4v", ".avi"}


@dataclass(frozen=True)
class VideoInfo:
    path: Path
    duration_sec: float
    width: Optional[int]
    height: Optional[int]
    has_audio: bool


class VideoValidationError(ValueError):
    """Raised when the source video cannot be used."""


def _ffprobe_bin(ffmpeg_bin: str) -> str:
    """Derive ffprobe path from ffmpeg binary name/path."""
    p = Path(ffmpeg_bin)
    name = p.name
    if name.lower().startswith("ffmpeg"):
        probe_name = name.replace("ffmpeg", "ffprobe").replace("FFMPEG", "ffprobe")
        candidate = p.with_name(probe_name)
        if candidate.exists() or shutil.which(str(candidate)):
            return str(candidate)
        which_probe = shutil.which("ffprobe")
        if which_probe:
            return which_probe
    which_probe = shutil.which("ffprobe")
    if which_probe:
        return which_probe
    return "ffprobe"


def validate_video(
    video_path: str | Path,
    *,
    ffmpeg_bin: str = "ffmpeg",
) -> VideoInfo:
    """Ensure *video_path* exists, is a readable media file, and report duration."""
    path = Path(video_path).expanduser().resolve()
    if not path.is_file():
        raise VideoValidationError(f"Video not found: {path}")
    if path.suffix.lower() not in VIDEO_EXTENSIONS:
        raise VideoValidationError(
            f"Unsupported video extension {path.suffix!r}; "
            f"expected one of {sorted(VIDEO_EXTENSIONS)}"
        )

    # Prefer ffprobe for metadata; fall back to ffmpeg -i parsing only via ffprobe requirement
    probe = _ffprobe_bin(ffmpeg_bin)
    if not shutil.which(probe) and not Path(probe).exists():
        # Still allow if ffmpeg exists — try a lightweight open via ffmpeg
        if not shutil.which(ffmpeg_bin) and not Path(ffmpeg_bin).exists():
            raise VideoValidationError(
                f"ffmpeg not found ({ffmpeg_bin!r}). Install system ffmpeg and ensure it is on PATH "
                "or set HUMANOS_FFMPEG / config.ffmpeg."
            )
        raise VideoValidationError(
            "ffprobe not found. Install ffmpeg (includes ffprobe) or set PATH accordingly."
        )

    cmd = [
        probe,
        "-v",
        "quiet",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        str(path),
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    except FileNotFoundError as exc:
        raise VideoValidationError(f"ffprobe executable not runnable: {probe}") from exc

    if proc.returncode != 0:
        raise VideoValidationError(
            f"ffprobe failed for {path}: {proc.stderr.strip() or proc.stdout.strip()}"
        )

    try:
        meta = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise VideoValidationError(f"Invalid ffprobe JSON for {path}") from exc

    fmt = meta.get("format") or {}
    try:
        duration = float(fmt.get("duration") or 0.0)
    except (TypeError, ValueError):
        duration = 0.0
    if duration <= 0:
        raise VideoValidationError(f"Could not determine positive duration for {path}")

    width = height = None
    has_audio = False
    has_video = False
    for stream in meta.get("streams") or []:
        codec_type = stream.get("codec_type")
        if codec_type == "video" and not has_video:
            has_video = True
            try:
                width = int(stream["width"]) if stream.get("width") else None
                height = int(stream["height"]) if stream.get("height") else None
            except (TypeError, ValueError, KeyError):
                width = height = None
        if codec_type == "audio":
            has_audio = True

    if not has_video:
        raise VideoValidationError(f"No video stream found in {path}")
    if not has_audio:
        raise VideoValidationError(
            f"No audio stream found in {path}; transcription requires audio"
        )

    return VideoInfo(
        path=path,
        duration_sec=duration,
        width=width,
        height=height,
        has_audio=has_audio,
    )
