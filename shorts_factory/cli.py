"""CLI for Shorts Factory.

Preferred:
  humanos shorts <video> --whisper-model small

Also:
  python -m shorts_factory shorts <video>
  python -m shorts_factory.cli shorts <video>
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional, Sequence

from shorts_factory import __version__
from shorts_factory.config import (
    DEFAULT_COMPUTE_TYPE,
    DEFAULT_DEVICE,
    DEFAULT_LANGUAGE,
    DEFAULT_WHISPER_MODEL,
    resolve_paths,
)
from shorts_factory.pipeline.run import run_milestone1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="humanos",
        description="HUMANOS tooling. Milestone 1: Shorts Factory transcription.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    sub = parser.add_subparsers(dest="command")

    shorts = sub.add_parser(
        "shorts",
        help="Shorts Factory: long video → transcript.json + captions.srt (milestone 1)",
    )
    shorts.add_argument(
        "video",
        type=str,
        help="Path to source long video (mp4/mov/mkv/…)",
    )
    shorts.add_argument(
        "--out",
        type=str,
        default=None,
        help="Override outputs root (default: outputs/shorts_factory under repo)",
    )
    shorts.add_argument(
        "--whisper-model",
        type=str,
        default=None,
        help=f"faster-whisper model size (default: {DEFAULT_WHISPER_MODEL})",
    )
    shorts.add_argument(
        "--language",
        type=str,
        default=None,
        help=f"ASR language hint (default: {DEFAULT_LANGUAGE})",
    )
    shorts.add_argument(
        "--device",
        type=str,
        default=None,
        choices=["auto", "cpu", "cuda"],
        help=f"Inference device (default: {DEFAULT_DEVICE})",
    )
    shorts.add_argument(
        "--compute-type",
        type=str,
        default=None,
        help=f"ctranslate2 compute type (default: {DEFAULT_COMPUTE_TYPE})",
    )
    shorts.add_argument(
        "--ffmpeg",
        type=str,
        default=None,
        help="Path to ffmpeg binary (default: PATH / config)",
    )
    shorts.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to paths YAML (default: config/paths.example.yaml)",
    )
    shorts.add_argument(
        "--source-name",
        type=str,
        default=None,
        help="Override output folder name under outputs/shorts_factory/",
    )
    shorts.add_argument(
        "--keep-audio",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Keep intermediate audio.wav (default: true)",
    )
    shorts.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Debug logging",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    argv_list = list(argv) if argv is not None else sys.argv[1:]

    # Allow `python -m shorts_factory shorts …` and bare `humanos shorts …`.
    # Also accept legacy `python -m shorts_factory.cli shorts …`.
    parser = _build_parser()
    args = parser.parse_args(argv_list)

    if not args.command:
        parser.print_help()
        print(
            "\nMilestone 1 only: humanos shorts <video> → transcript.json + captions.srt\n"
            "Not implemented yet: candidates, clips, 9:16 reframe, burn-in, Remotion/NLE.",
            file=sys.stderr,
        )
        return 2

    if args.command != "shorts":
        print(f"Unknown command: {args.command}", file=sys.stderr)
        return 2

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )

    overrides = {}
    if args.out:
        overrides["outputs"] = args.out
    if args.whisper_model:
        overrides["whisper_model"] = args.whisper_model
    if args.language:
        overrides["language"] = args.language
    if args.device:
        overrides["device"] = args.device
    if args.compute_type:
        overrides["compute_type"] = args.compute_type
    if args.ffmpeg:
        overrides["ffmpeg"] = args.ffmpeg

    config_path = Path(args.config) if args.config else None
    paths = resolve_paths(cli_overrides=overrides, config_path=config_path)

    try:
        result = run_milestone1(
            args.video,
            paths,
            keep_audio=args.keep_audio,
            source_name=args.source_name,
        )
    except Exception as exc:
        logging.getLogger(__name__).error("%s", exc)
        return 1

    print(f"source:     {result.source_video}")
    print(f"output_dir: {result.output_dir}")
    print(f"transcript: {result.transcript_json}")
    print(f"captions:   {result.captions_srt}")
    if result.audio_wav.is_file():
        print(f"audio:      {result.audio_wav}")
    print(
        f"segments:   {len(result.transcript.get('segments', []))} "
        f"(lang={result.transcript.get('language')}, "
        f"model={result.transcript.get('model')}, "
        f"device={result.transcript.get('device')})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
