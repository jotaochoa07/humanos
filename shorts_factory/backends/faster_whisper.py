"""FasterWhisperBackend — default TranscriptionBackend (SF3).

Defaults (locked): model=small, language=auto, device=auto, compute_type=auto.
If compatible CUDA is detected → use it; otherwise CPU.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from shorts_factory.backends.transcription import (
    TranscriptionBackend,
    TranscriptionResult,
    TranscriptionSegment,
)

logger = logging.getLogger(__name__)


def detect_cuda_available() -> bool:
    """Return True if a usable CUDA device is present for ctranslate2/faster-whisper."""
    try:
        import ctranslate2

        return ctranslate2.get_cuda_device_count() > 0
    except Exception:
        return False


def resolve_device_and_compute(
    device: str = "auto",
    compute_type: str = "auto",
) -> tuple[str, str]:
    """Pick concrete device + compute_type from auto/explicit settings."""
    device_l = (device or "auto").lower()
    compute_l = (compute_type or "auto").lower()

    if device_l == "auto":
        resolved_device = "cuda" if detect_cuda_available() else "cpu"
    elif device_l in {"cpu", "cuda"}:
        if device_l == "cuda" and not detect_cuda_available():
            logger.warning("CUDA requested but not available; falling back to CPU")
            resolved_device = "cpu"
        else:
            resolved_device = device_l
    else:
        raise ValueError(f"Unsupported device={device!r}; use auto|cpu|cuda")

    if compute_l == "auto":
        resolved_compute = "float16" if resolved_device == "cuda" else "int8"
    else:
        resolved_compute = compute_l

    return resolved_device, resolved_compute


class FasterWhisperBackend(TranscriptionBackend):
    """Local faster-whisper implementation.

    Constructor accepts an optional model cache directory; model size is
    chosen per ``transcribe()`` call so medium/large-v3 can be swapped later
    without changing the pipeline.
    """

    engine_name = "faster-whisper"

    def __init__(self, *, download_root: Optional[Path] = None) -> None:
        self.download_root = Path(download_root) if download_root else None

    def transcribe(
        self,
        audio_path: Path,
        *,
        language: str = "auto",
        model: str = "small",
        device: str = "auto",
        compute_type: str = "auto",
    ) -> TranscriptionResult:
        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:  # pragma: no cover
            raise ImportError(
                "faster-whisper is required for FasterWhisperBackend. "
                "Install with: pip install -r requirements-shorts.txt"
            ) from exc

        audio_path = Path(audio_path)
        if not audio_path.is_file():
            raise FileNotFoundError(f"Audio not found: {audio_path}")

        resolved_device, resolved_compute = resolve_device_and_compute(device, compute_type)
        logger.info(
            "Loading faster-whisper model=%s device=%s compute_type=%s",
            model,
            resolved_device,
            resolved_compute,
        )

        kwargs = {
            "device": resolved_device,
            "compute_type": resolved_compute,
        }
        if self.download_root is not None:
            kwargs["download_root"] = str(self.download_root)

        whisper = WhisperModel(model, **kwargs)

        lang = None if (not language or language.lower() == "auto") else language
        segments_iter, info = whisper.transcribe(
            str(audio_path),
            language=lang,
            vad_filter=True,
        )

        segments: list[TranscriptionSegment] = []
        for i, seg in enumerate(segments_iter, start=1):
            text = (seg.text or "").strip()
            segments.append(
                TranscriptionSegment(
                    id=i,
                    start=float(seg.start),
                    end=float(seg.end),
                    text=text,
                )
            )

        detected = getattr(info, "language", None) or (language if language != "auto" else "unknown")
        duration = getattr(info, "duration", None)

        return TranscriptionResult(
            language=str(detected),
            segments=segments,
            engine=self.engine_name,
            model=model,
            device=resolved_device,
            compute_type=resolved_compute,
            duration_sec=float(duration) if duration is not None else None,
        )
