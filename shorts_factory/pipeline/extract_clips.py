"""Milestone 3: extract horizontal clips from candidates.json via ffmpeg.

No reframe, face tracking, burn-in, or Remotion — cut only.
Re-reads possibly hand-edited start/end from candidates.json.
"""

from __future__ import annotations

import json
import logging
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Optional, Sequence

from shorts_factory.contracts import validate_candidates_shape
from shorts_factory.pipeline.analyze import CANDIDATES_JSON, write_candidates_json

logger = logging.getLogger(__name__)

CLIP_HORIZONTAL = "clip_horizontal.mp4"
META_JSON = "meta.json"


class ClipExtractionError(RuntimeError):
    """Raised when ffmpeg clip extraction fails."""


FfmpegRunner = Callable[[Sequence[str]], subprocess.CompletedProcess]


def _default_runner(cmd: Sequence[str]) -> subprocess.CompletedProcess:
    return subprocess.run(list(cmd), capture_output=True, text=True, check=False)


def load_candidates_json(path: Path) -> dict[str, Any]:
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"candidates.json not found: {path}")
    doc = json.loads(path.read_text(encoding="utf-8"))
    errors = validate_candidates_shape(doc)
    if errors:
        raise ValueError("invalid candidates.json: " + "; ".join(errors))
    return doc


def resolve_source_video(
    document: Mapping[str, Any],
    *,
    video_override: Optional[Path] = None,
) -> Path:
    if video_override is not None:
        p = Path(video_override)
        if not p.is_file():
            raise FileNotFoundError(f"source video not found: {p}")
        return p.resolve()
    raw = document.get("source_video")
    if not raw:
        raise ValueError(
            "candidates.json missing source_video; pass --video to override"
        )
    p = Path(str(raw))
    if not p.is_file():
        raise FileNotFoundError(
            f"source video from candidates.json not found: {p}. "
            "Pass --video PATH to override."
        )
    return p.resolve()


def extract_horizontal_clip(
    video_path: Path,
    clip_out: Path,
    *,
    start: float,
    end: float,
    ffmpeg_bin: str = "ffmpeg",
    runner: Optional[FfmpegRunner] = None,
) -> Path:
    """Cut [start, end) from *video_path* into *clip_out* (stream copy)."""
    if end <= start:
        raise ClipExtractionError(f"invalid clip range: start={start} end={end}")
    video_path = Path(video_path)
    clip_out = Path(clip_out)
    clip_out.parent.mkdir(parents=True, exist_ok=True)

    if not shutil.which(ffmpeg_bin) and not Path(ffmpeg_bin).exists():
        # Allow injected runners in tests even if ffmpeg missing on PATH
        if runner is None:
            raise ClipExtractionError(
                f"ffmpeg not found ({ffmpeg_bin!r}). Install system ffmpeg or set HUMANOS_FFMPEG."
            )

    duration = float(end) - float(start)
    cmd = [
        ffmpeg_bin,
        "-y",
        "-ss",
        f"{float(start):.3f}",
        "-i",
        str(video_path),
        "-t",
        f"{duration:.3f}",
        "-c",
        "copy",
        "-avoid_negative_ts",
        "make_zero",
        str(clip_out),
    ]
    run = runner or _default_runner
    proc = run(cmd)
    if proc.returncode != 0:
        raise ClipExtractionError(
            "ffmpeg clip extraction failed:\n"
            + ((proc.stderr or "").strip() or (proc.stdout or "").strip() or f"exit {proc.returncode}")
        )
    # In production ffmpeg creates the file; tests' mock runners should touch it.
    if not clip_out.is_file() and runner is None:
        raise ClipExtractionError(f"ffmpeg reported success but missing output: {clip_out}")
    return clip_out


def _candidate_folder_name(cand: Mapping[str, Any], index: int) -> str:
    folder = str(cand.get("folder") or "").strip().strip("/")
    if folder:
        return folder
    cid = str(cand.get("id") or "").strip().strip("/")
    if cid:
        return cid
    return f"{index:02d}-clip"


def extract_clips_from_candidates(
    document: Mapping[str, Any],
    *,
    run_dir: Path,
    video_path: Path,
    ffmpeg_bin: str = "ffmpeg",
    runner: Optional[FfmpegRunner] = None,
) -> dict[str, Any]:
    """Extract one horizontal clip per candidate; update document in memory."""
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    updated = dict(document)
    candidates = [dict(c) for c in (document.get("candidates") or [])]
    out_list: list[dict[str, Any]] = []

    for i, cand in enumerate(candidates, start=1):
        try:
            start = float(cand["start"])
            end = float(cand["end"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ClipExtractionError(f"candidate[{i}] missing valid start/end: {exc}") from exc

        folder_name = _candidate_folder_name(cand, i)
        folder_path = run_dir / folder_name
        folder_path.mkdir(parents=True, exist_ok=True)
        clip_path = folder_path / CLIP_HORIZONTAL

        logger.info(
            "Extracting %s [%.2f–%.2f] → %s",
            folder_name,
            start,
            end,
            clip_path,
        )
        extract_horizontal_clip(
            video_path,
            clip_path,
            start=start,
            end=end,
            ffmpeg_bin=ffmpeg_bin,
            runner=runner,
        )

        # Ensure duration_sec matches possibly hand-edited bounds
        cand["duration_sec"] = round(end - start, 3)
        cand["folder"] = f"{folder_name}/"
        cand["clip_horizontal"] = f"{folder_name}/{CLIP_HORIZONTAL}"
        if "id" not in cand or not cand["id"]:
            cand["id"] = folder_name

        meta = {
            **cand,
            "source_video": str(video_path),
            "clip_horizontal_path": str(clip_path.resolve()),
        }
        meta_path = folder_path / META_JSON
        meta_path.write_text(
            json.dumps(meta, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        out_list.append(cand)

    updated["candidates"] = out_list
    updated["milestone"] = max(int(updated.get("milestone") or 2), 3)
    return updated


@dataclass(frozen=True)
class Milestone3Result:
    source_video: Path
    output_dir: Path
    candidates_json: Path
    document: dict
    clip_paths: tuple[Path, ...]


def run_clips_stage(
    *,
    run_dir: Path,
    ffmpeg_bin: str = "ffmpeg",
    video: Optional[Path] = None,
    candidates_path: Optional[Path] = None,
    runner: Optional[FfmpegRunner] = None,
) -> Milestone3Result:
    """M3 orchestrator: load candidates.json → cut clips → rewrite candidates.json."""
    run_dir = Path(run_dir)
    cand_path = Path(candidates_path) if candidates_path else run_dir / CANDIDATES_JSON
    document = load_candidates_json(cand_path)
    video_path = resolve_source_video(document, video_override=video)

    updated = extract_clips_from_candidates(
        document,
        run_dir=run_dir,
        video_path=video_path,
        ffmpeg_bin=ffmpeg_bin,
        runner=runner,
    )
    write_candidates_json(updated, cand_path)

    clip_paths = tuple(
        (run_dir / str(c["clip_horizontal"])).resolve()
        for c in updated["candidates"]
        if c.get("clip_horizontal")
    )
    return Milestone3Result(
        source_video=video_path,
        output_dir=run_dir.resolve(),
        candidates_json=cand_path.resolve(),
        document=updated,
        clip_paths=clip_paths,
    )
