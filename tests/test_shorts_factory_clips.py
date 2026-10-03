"""M3 clip extraction tests with mocked ffmpeg (CI-safe)."""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from shorts_factory.config import PathsConfig
from shorts_factory.pipeline.extract_clips import (
    extract_clips_from_candidates,
    run_clips_stage,
)
from shorts_factory.pipeline.run import run_milestone3


def _sample_candidates(video: Path) -> dict:
    return {
        "source_video": str(video),
        "generated_at": "2026-10-03T00:00:00+00:00",
        "milestone": 2,
        "ranker": "MockRanker",
        "snap_rules_version": "m2-v4",
        "config": {
            "duration_min_sec": 20,
            "duration_max_sec": 90,
            "target_count": 2,
            "overlap_iou_threshold": 0.45,
            "max_spans": 3,
        },
        "candidates": [
            {
                "id": "01-organigrama",
                "start": 12.0,
                "end": 44.0,
                "duration_sec": 32.0,
                "transcript": "texto uno",
                "hook": "hook",
                "central_idea": "idea",
                "selection_reason": "reason",
                "score": 0.9,
                "suggested_title": "Organigrama",
                "folder": "01-organigrama/",
                "scores": {
                    "hook_strength": 0.9,
                    "context_completeness": 0.9,
                    "conceptual_completeness": 0.9,
                    "standalone_clarity": 0.9,
                    "payoff_strength": 0.9,
                },
                "spans": [
                    {"role": "development", "start": 12.0, "end": 44.0},
                ],
            },
            {
                "id": "02-orquestacion",
                "start": 20.0,
                "end": 76.0,
                "duration_sec": 40.0,
                "transcript": "texto dos",
                "hook": "hook2",
                "central_idea": "idea2",
                "selection_reason": "reason2",
                "score": 0.8,
                "suggested_title": "Orquestacion",
                "folder": "02-orquestacion/",
                "scores": {
                    "hook_strength": 0.8,
                    "context_completeness": 0.8,
                    "conceptual_completeness": 0.8,
                    "standalone_clarity": 0.8,
                    "payoff_strength": 0.8,
                },
                "spans": [
                    {"role": "hook", "start": 20.0, "end": 36.0},
                    {"role": "payoff", "start": 52.0, "end": 76.0},
                ],
            },
        ],
    }


def _mock_runner(cmd):
    # Last arg is output path for our ffmpeg command shape
    out = Path(cmd[-1])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(b"fake-mp4")
    return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")


class TestExtractClips(unittest.TestCase):
    def test_extract_writes_meta_and_clips(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            video = root / "source.mp4"
            video.write_bytes(b"video")
            run_dir = root / "run"
            run_dir.mkdir()
            doc = _sample_candidates(video)

            updated = extract_clips_from_candidates(
                doc,
                run_dir=run_dir,
                video_path=video,
                runner=_mock_runner,
            )

            self.assertEqual(updated["milestone"], 3)
            for cand in updated["candidates"]:
                folder = run_dir / cand["folder"].rstrip("/")
                self.assertTrue((folder / "clip_horizontal.mp4").is_file())
                meta = json.loads((folder / "meta.json").read_text(encoding="utf-8"))
                self.assertEqual(meta["start"], cand["start"])
                self.assertEqual(meta["end"], cand["end"])
                self.assertIn("clip_horizontal", cand)
                self.assertIn("spans", meta)
                self.assertGreaterEqual(len(meta["spans"]), 1)

            # multi-span candidate kept 2 spans and spoken duration < envelope
            multi = updated["candidates"][1]
            self.assertEqual(multi["span_count"], 2)
            self.assertLess(multi["duration_sec"], multi["envelope_duration_sec"])

    def test_respects_hand_edited_timestamps(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            video = root / "source.mp4"
            video.write_bytes(b"video")
            run_dir = root / "run"
            run_dir.mkdir()
            doc = _sample_candidates(video)
            # Hand-edit first candidate spans (M3 re-reads spans)
            doc["candidates"][0]["spans"] = [
                {"role": "development", "start": 15.5, "end": 50.5}
            ]
            doc["candidates"][0]["start"] = 15.5
            doc["candidates"][0]["end"] = 50.5
            (run_dir / "candidates.json").write_text(
                json.dumps(doc), encoding="utf-8"
            )

            seen_ranges: list[tuple[float, float]] = []

            def runner(cmd):
                # Cut cmds include -ss; concat cmds do not
                if "-ss" in cmd:
                    ss = float(cmd[cmd.index("-ss") + 1])
                    dur = float(cmd[cmd.index("-t") + 1])
                    seen_ranges.append((ss, ss + dur))
                return _mock_runner(cmd)

            result = run_clips_stage(
                run_dir=run_dir,
                video=video,
                runner=runner,
            )
            self.assertAlmostEqual(seen_ranges[0][0], 15.5)
            self.assertAlmostEqual(seen_ranges[0][1], 50.5)
            reloaded = json.loads(result.candidates_json.read_text(encoding="utf-8"))
            self.assertEqual(reloaded["candidates"][0]["start"], 15.5)
            self.assertEqual(reloaded["candidates"][0]["duration_sec"], 35.0)

    def test_run_milestone3_orchestrator(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            video = root / "source.mp4"
            video.write_bytes(b"video")
            run_dir = root / "buzz"
            run_dir.mkdir()
            (run_dir / "candidates.json").write_text(
                json.dumps(_sample_candidates(video)), encoding="utf-8"
            )
            paths = PathsConfig(
                repo_root=root,
                outputs_root=root / "outputs",
                ffmpeg="ffmpeg",
                asr_models=None,
                input_media=None,
            )
            result = run_milestone3(paths, run_dir=run_dir, runner=_mock_runner)
            self.assertEqual(len(result.clip_paths), 2)
            self.assertTrue(all(p.is_file() for p in result.clip_paths))


class TestCliClips(unittest.TestCase):
    def test_cli_clips_help(self):
        from shorts_factory.cli import main

        with self.assertRaises(SystemExit) as ctx:
            main(["shorts", "clips", "--help"])
        self.assertEqual(ctx.exception.code, 0)

    def test_normalize_keeps_clips(self):
        from shorts_factory.cli import _normalize_argv

        self.assertEqual(
            _normalize_argv(["shorts", "clips", "out/foo"]),
            ["shorts", "clips", "out/foo"],
        )

    def test_cli_clips_invokes_m3(self):
        from shorts_factory.cli import main
        from shorts_factory.pipeline.extract_clips import Milestone3Result

        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "run"
            run_dir.mkdir()
            with mock.patch("shorts_factory.cli.run_milestone3") as mocked:
                mocked.return_value = Milestone3Result(
                    source_video=Path("/v.mp4"),
                    output_dir=run_dir,
                    candidates_json=run_dir / "candidates.json",
                    document={
                        "candidates": [
                            {
                                "id": "01-a",
                                "start": 1.0,
                                "end": 30.0,
                                "folder": "01-a/",
                                "clip_horizontal": "01-a/clip_horizontal.mp4",
                            }
                        ]
                    },
                    clip_paths=(run_dir / "01-a" / "clip_horizontal.mp4",),
                )
                code = main(["shorts", "clips", str(run_dir)])
                self.assertEqual(code, 0)
                mocked.assert_called_once()


if __name__ == "__main__":
    unittest.main()
