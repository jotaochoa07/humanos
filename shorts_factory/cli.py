"""CLI for Shorts Factory.

Milestone 1+2:
  humanos shorts <video>
  humanos shorts candidates <run_dir>
  humanos shorts candidates --from-transcript path/to/transcript.json

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
    DEFAULT_DURATION_MAX_SEC,
    DEFAULT_DURATION_MIN_SEC,
    DEFAULT_LANGUAGE,
    DEFAULT_OVERLAP_IOU,
    DEFAULT_TARGET_COUNT,
    DEFAULT_WHISPER_MODEL,
    resolve_paths,
)
from shorts_factory.pipeline.run import run_milestone2, run_shorts_pipeline


def _add_shared_path_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--out",
        type=str,
        default=None,
        help="Override outputs root (default: outputs/shorts_factory under repo)",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to paths YAML (default: config/paths.example.yaml)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Debug logging",
    )


def _add_ranking_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--min-duration",
        type=float,
        default=None,
        help=f"Min candidate duration seconds (default: {DEFAULT_DURATION_MIN_SEC:g})",
    )
    parser.add_argument(
        "--max-duration",
        type=float,
        default=None,
        help=f"Max candidate duration seconds (default: {DEFAULT_DURATION_MAX_SEC:g})",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=None,
        help=f"Target candidate count (default: {DEFAULT_TARGET_COUNT})",
    )
    parser.add_argument(
        "--overlap-iou",
        type=float,
        default=None,
        help=f"NMS overlap IoU threshold (default: {DEFAULT_OVERLAP_IOU})",
    )
    parser.add_argument(
        "--ranker-model",
        type=str,
        default=None,
        help="OpenRouter model id (default: OPENROUTER_MODEL env / gemini flash-lite)",
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="humanos",
        description="HUMANOS tooling. Shorts Factory: transcript (M1) + candidates (M2).",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    sub = parser.add_subparsers(dest="command")

    shorts = sub.add_parser(
        "shorts",
        help="Shorts Factory: long video → transcript → candidates.json (M1+M2)",
    )
    shorts_sub = shorts.add_subparsers(dest="shorts_cmd")

    # humanos shorts <video> …
    run_p = shorts_sub.add_parser(
        "run",
        help="Run M1+M2 for a source video (also accepted as: humanos shorts <video>)",
    )
    run_p.add_argument("video", type=str, help="Path to source long video")
    _add_shared_path_flags(run_p)
    _add_ranking_flags(run_p)
    run_p.add_argument(
        "--whisper-model",
        type=str,
        default=None,
        help=f"faster-whisper model size (default: {DEFAULT_WHISPER_MODEL})",
    )
    run_p.add_argument(
        "--language",
        type=str,
        default=None,
        help=f"ASR language hint (default: {DEFAULT_LANGUAGE})",
    )
    run_p.add_argument(
        "--device",
        type=str,
        default=None,
        choices=["auto", "cpu", "cuda"],
        help=f"Inference device (default: {DEFAULT_DEVICE})",
    )
    run_p.add_argument(
        "--compute-type",
        type=str,
        default=None,
        help=f"ctranslate2 compute type (default: {DEFAULT_COMPUTE_TYPE})",
    )
    run_p.add_argument(
        "--ffmpeg",
        type=str,
        default=None,
        help="Path to ffmpeg binary (default: PATH / config)",
    )
    run_p.add_argument(
        "--source-name",
        type=str,
        default=None,
        help="Override output folder name under outputs/shorts_factory/",
    )
    run_p.add_argument(
        "--keep-audio",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Keep intermediate audio.wav (default: true)",
    )
    run_p.add_argument(
        "--skip-candidates",
        action="store_true",
        help="Milestone 1 only (do not write candidates.json)",
    )
    run_p.add_argument(
        "--skip-transcribe",
        action="store_true",
        help="Reuse existing transcript.json under the source output dir (M2 only)",
    )
    run_p.add_argument(
        "--force-transcribe",
        action="store_true",
        help="Re-run ASR even if transcript.json already exists",
    )

    # humanos shorts candidates <run_dir> | --from-transcript
    cand_p = shorts_sub.add_parser(
        "candidates",
        help="Milestone 2 only: transcript.json → candidates.json",
    )
    cand_p.add_argument(
        "run_dir",
        nargs="?",
        type=str,
        default=None,
        help="Run directory containing transcript.json (outputs/shorts_factory/<source>/)",
    )
    cand_p.add_argument(
        "--from-transcript",
        type=str,
        default=None,
        help="Explicit path to transcript.json (or a directory containing it)",
    )
    _add_shared_path_flags(cand_p)
    _add_ranking_flags(cand_p)

    return parser


def _normalize_argv(argv: list[str]) -> list[str]:
    """Allow `humanos shorts <video>` without an explicit `run` subcommand.

    Transforms:
      shorts path/to.mp4 …  →  shorts run path/to.mp4 …
    Leaves intact:
      shorts run …
      shorts candidates …
      shorts --help
    """
    if not argv or argv[0] != "shorts":
        return argv
    if len(argv) == 1:
        return argv
    second = argv[1]
    if second in ("run", "candidates", "-h", "--help"):
        return argv
    if second.startswith("-"):
        # flags before video are not supported in shorthand; keep as-is for argparse error
        return ["shorts", "run", *argv[1:]]
    return ["shorts", "run", *argv[1:]]


def _paths_overrides_from_args(args: argparse.Namespace) -> dict:
    overrides: dict = {}
    if getattr(args, "out", None):
        overrides["outputs"] = args.out
    if getattr(args, "whisper_model", None):
        overrides["whisper_model"] = args.whisper_model
    if getattr(args, "language", None):
        overrides["language"] = args.language
    if getattr(args, "device", None):
        overrides["device"] = args.device
    if getattr(args, "compute_type", None):
        overrides["compute_type"] = args.compute_type
    if getattr(args, "ffmpeg", None):
        overrides["ffmpeg"] = args.ffmpeg
    if getattr(args, "min_duration", None) is not None:
        overrides["duration_min_sec"] = args.min_duration
    if getattr(args, "max_duration", None) is not None:
        overrides["duration_max_sec"] = args.max_duration
    if getattr(args, "count", None) is not None:
        overrides["target_count"] = args.count
    if getattr(args, "overlap_iou", None) is not None:
        overrides["overlap_iou_threshold"] = args.overlap_iou
    if getattr(args, "ranker_model", None):
        overrides["ranker_model"] = args.ranker_model
    return overrides


def _print_m2(result) -> None:
    print(f"source:      {result.source_video}")
    print(f"output_dir:  {result.output_dir}")
    print(f"transcript:  {result.transcript_json}")
    print(f"candidates:  {result.candidates_json}")
    print(f"count:       {len(result.document.get('candidates', []))}")
    for cand in result.document.get("candidates", []):
        print(
            f"  - {cand['id']}: {cand['start']:.1f}-{cand['end']:.1f}s "
            f"(score={cand['score']:.2f}) {cand['suggested_title']}"
        )


def main(argv: Optional[Sequence[str]] = None) -> int:
    argv_list = _normalize_argv(list(argv) if argv is not None else sys.argv[1:])
    parser = _build_parser()
    args = parser.parse_args(argv_list)

    if not args.command:
        parser.print_help()
        print(
            "\nShorts Factory: humanos shorts <video> → transcript.json + candidates.json\n"
            "M2 only: humanos shorts candidates <run_dir>\n"
            "Not implemented yet: clip extract, 9:16 reframe, burn-in, Remotion/NLE.",
            file=sys.stderr,
        )
        return 2

    if args.command != "shorts":
        print(f"Unknown command: {args.command}", file=sys.stderr)
        return 2

    if not getattr(args, "shorts_cmd", None):
        parser.parse_args(["shorts", "--help"])
        return 2

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )

    config_path = Path(args.config) if getattr(args, "config", None) else None
    paths = resolve_paths(
        cli_overrides=_paths_overrides_from_args(args),
        config_path=config_path,
    )

    try:
        if args.shorts_cmd == "candidates":
            if not args.run_dir and not args.from_transcript:
                print(
                    "candidates requires <run_dir> or --from-transcript",
                    file=sys.stderr,
                )
                return 2
            run_dir = Path(args.run_dir) if args.run_dir else None
            from_transcript = (
                Path(args.from_transcript) if args.from_transcript else None
            )
            # If only --from-transcript given, derive run_dir from its parent
            if run_dir is None and from_transcript is not None:
                tp = from_transcript
                if tp.is_dir():
                    run_dir = tp
                    from_transcript = None
                else:
                    run_dir = tp.parent
            result = run_milestone2(
                paths,
                run_dir=run_dir,
                from_transcript=from_transcript,
            )
            _print_m2(result)
            return 0

        # shorts run <video>
        m1, m2 = run_shorts_pipeline(
            args.video,
            paths,
            keep_audio=args.keep_audio,
            source_name=args.source_name,
            skip_transcribe=args.skip_transcribe,
            skip_candidates=args.skip_candidates,
            force_transcribe=args.force_transcribe,
        )
        if m1 is not None:
            print(f"source:     {m1.source_video}")
            print(f"output_dir: {m1.output_dir}")
            print(f"transcript: {m1.transcript_json}")
            print(f"captions:   {m1.captions_srt}")
            if m1.audio_wav.is_file():
                print(f"audio:      {m1.audio_wav}")
            print(
                f"segments:   {len(m1.transcript.get('segments', []))} "
                f"(lang={m1.transcript.get('language')}, "
                f"model={m1.transcript.get('model')}, "
                f"device={m1.transcript.get('device')})"
            )
        if m2 is not None:
            _print_m2(m2)
        elif args.skip_candidates:
            print("candidates: skipped (--skip-candidates)")
    except Exception as exc:
        logging.getLogger(__name__).error("%s", exc)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
