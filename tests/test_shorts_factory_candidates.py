"""M2 pipeline + CLI tests with mocked CandidateRanker (CI-safe)."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from typing import Any, Mapping, Sequence
from unittest import mock

from shorts_factory.backends.ranking import (
    CandidateRanker,
    RankingConfig,
    RawCandidate,
    ScoreDimensions,
)
from shorts_factory.config import PathsConfig, resolve_paths
from shorts_factory.contracts import validate_candidates_shape
from shorts_factory.pipeline.analyze import analyze_transcript, run_candidates_stage
from shorts_factory.pipeline.run import run_milestone2

FIXTURE = Path(__file__).parent / "fixtures" / "shorts_factory" / "transcript.json"


def _dims(x: float = 0.85) -> ScoreDimensions:
    return ScoreDimensions(x, x, x, x, x)


class MockRanker(CandidateRanker):
    name = "MockRanker"

    def __init__(self, raw: Sequence[RawCandidate] | None = None) -> None:
        self.raw = list(
            raw
            or [
                RawCandidate(
                    20, 55, "Más agentes ≠ productividad", "Más agentes no dan más output",
                    "Tesis clara y autocontenida", 0.93, "Más agentes no es mejor",
                    minimum_context="empresas apilan agentes",
                    idea_development="cada agente suma fricción",
                    payoff="productividad no escala con headcount de agentes",
                    scores=_dims(0.9),
                ),
                RawCandidate(
                    36, 72, "El cuello es la orquestación", "Coordinar es el problema",
                    "Punchline fuerte", 0.88, "Orquestacion cara",
                    minimum_context="multi-agente",
                    idea_development="orquestar es caro",
                    payoff="el cuello es coordinación",
                    scores=_dims(0.88),
                ),
                RawCandidate(
                    4, 40, "Copian el organigrama", "Burocracia digital",
                    "Escena memorable", 0.86, "Organigrama de agentes",
                    minimum_context="copian org chart",
                    idea_development="burocracia en software",
                    payoff="teatro de eficiencia",
                    scores=_dims(0.86),
                ),
                RawCandidate(
                    52, 90, "Un solo agente gana", "Ejército vs uno",
                    "Contraste útil", 0.84, "Un solo agente",
                    minimum_context="tropa vs uno",
                    idea_development="un agente cierra el loop",
                    payoff="mejor uno bien diseñado",
                    scores=_dims(0.84),
                ),
                RawCandidate(
                    60, 100, "Tokens y lentitud", "Costo de tokens",
                    "Consecuencia concreta", 0.82, "Tokens lentos",
                    minimum_context="uso de tokens",
                    idea_development="latencia y costo",
                    payoff="el sistema se vuelve lento",
                    scores=_dims(0.82),
                ),
                RawCandidate(
                    100, 140, "Contexto saturado", "Saturación de contexto",
                    "Idea secundaria", 0.70, "Contexto saturado",
                    minimum_context="contexto",
                    idea_development="se satura",
                    payoff="cortar ideas autocontenidas",
                    scores=_dims(0.7),
                ),
                RawCandidate(
                    22, 58, "Near dup organigrama", "Dup",
                    "Debería caer por NMS", 0.75, "Organigrama dup",
                    scores=_dims(0.75),
                ),
            ]
        )
        self.calls = 0

    def propose_candidates(
        self,
        transcript: Mapping[str, Any],
        *,
        config: RankingConfig,
    ) -> Sequence[RawCandidate]:
        self.calls += 1
        self.assert_transcript = transcript
        return list(self.raw)


class TestAnalyze(unittest.TestCase):
    def test_analyze_writes_valid_shape(self):
        doc = json.loads(FIXTURE.read_text(encoding="utf-8"))
        ranker = MockRanker()
        cfg = RankingConfig(duration_min_sec=20, duration_max_sec=90, target_count=5)
        out = analyze_transcript(
            doc,
            ranker=ranker,
            config=cfg,
            generated_at="2026-10-03T00:00:00+00:00",
        )
        self.assertEqual(validate_candidates_shape(out), [])
        self.assertEqual(out["milestone"], 2)
        self.assertEqual(out["snap_rules_version"], "m2-v3")
        self.assertEqual(out["config"]["target_count"], 5)
        self.assertLessEqual(len(out["candidates"]), 5)
        self.assertGreaterEqual(len(out["candidates"]), 3)
        for cand in out["candidates"]:
            for key in (
                "start",
                "end",
                "duration_sec",
                "transcript",
                "hook",
                "central_idea",
                "selection_reason",
                "score",
                "suggested_title",
                "scores",
            ):
                self.assertIn(key, cand)
            for dim in (
                "hook_strength",
                "context_completeness",
                "conceptual_completeness",
                "standalone_clarity",
                "payoff_strength",
            ):
                self.assertIn(dim, cand["scores"])
            starts = {float(s["start"]) for s in doc["segments"]}
            ends = {float(s["end"]) for s in doc["segments"]}
            self.assertIn(float(cand["start"]), starts)
            self.assertIn(float(cand["end"]), ends)
            self.assertTrue(cand["transcript"])

    def test_run_candidates_stage_writes_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "sample"
            run_dir.mkdir()
            transcript_path = run_dir / "transcript.json"
            transcript_path.write_text(FIXTURE.read_text(encoding="utf-8"), encoding="utf-8")
            ranker = MockRanker()
            cfg = RankingConfig(target_count=4)
            result = run_candidates_stage(
                ranker=ranker,
                config=cfg,
                run_dir=run_dir,
            )
            self.assertTrue(result["candidates_path"].is_file())
            loaded = json.loads(result["candidates_path"].read_text(encoding="utf-8"))
            self.assertEqual(validate_candidates_shape(loaded), [])
            self.assertEqual(ranker.calls, 1)


class TestMilestone2Orchestrator(unittest.TestCase):
    def test_run_milestone2_with_injected_ranker(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            run_dir = tmp_path / "buzz"
            run_dir.mkdir()
            (run_dir / "transcript.json").write_text(
                FIXTURE.read_text(encoding="utf-8"), encoding="utf-8"
            )
            paths = PathsConfig(
                repo_root=tmp_path,
                outputs_root=tmp_path / "outputs",
                ffmpeg="ffmpeg",
                asr_models=None,
                input_media=None,
                target_count=5,
            )
            result = run_milestone2(paths, run_dir=run_dir, ranker=MockRanker())
            self.assertTrue(result.candidates_json.is_file())
            self.assertEqual(validate_candidates_shape(result.document), [])


class TestCliCandidates(unittest.TestCase):
    def test_cli_candidates_help(self):
        from shorts_factory.cli import main

        with self.assertRaises(SystemExit) as ctx:
            main(["shorts", "candidates", "--help"])
        self.assertEqual(ctx.exception.code, 0)

    def test_cli_candidates_from_run_dir(self):
        from shorts_factory.cli import main

        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "run"
            run_dir.mkdir()
            (run_dir / "transcript.json").write_text(
                FIXTURE.read_text(encoding="utf-8"), encoding="utf-8"
            )

            with mock.patch(
                "shorts_factory.cli.run_milestone2",
            ) as mocked:
                from shorts_factory.pipeline.run import Milestone2Result

                mocked.return_value = Milestone2Result(
                    source_video="x",
                    output_dir=run_dir,
                    transcript_json=run_dir / "transcript.json",
                    candidates_json=run_dir / "candidates.json",
                    document={
                        "source_video": "x",
                        "candidates": [
                            {
                                "id": "01-a",
                                "start": 1.0,
                                "end": 30.0,
                                "score": 0.9,
                                "suggested_title": "A",
                            }
                        ],
                    },
                )
                code = main(["shorts", "candidates", str(run_dir), "--count", "5"])
                self.assertEqual(code, 0)
                mocked.assert_called_once()

    def test_normalize_shorts_video_shorthand(self):
        from shorts_factory.cli import _normalize_argv

        self.assertEqual(
            _normalize_argv(["shorts", "video.mp4", "--count", "6"]),
            ["shorts", "run", "video.mp4", "--count", "6"],
        )
        self.assertEqual(
            _normalize_argv(["shorts", "candidates", "out/foo"]),
            ["shorts", "candidates", "out/foo"],
        )


class TestRankingConfigResolve(unittest.TestCase):
    def test_resolve_paths_ranking_knobs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "AGENTS.md").write_text("x", encoding="utf-8")
            (root / "package.json").write_text("{}", encoding="utf-8")
            cfg_dir = root / "config"
            cfg_dir.mkdir()
            (cfg_dir / "paths.example.yaml").write_text(
                "outputs: outputs/shorts_factory\n"
                "duration:\n  min_sec: 25\n  max_sec: 80\n"
                "ranking:\n  target_count: 6\n  overlap_iou_threshold: 0.5\n",
                encoding="utf-8",
            )
            paths = resolve_paths(
                config_path=cfg_dir / "paths.example.yaml",
                cwd=root,
                cli_overrides={"repo_root": str(root)},
            )
            self.assertEqual(paths.duration_min_sec, 25)
            self.assertEqual(paths.duration_max_sec, 80)
            self.assertEqual(paths.target_count, 6)
            self.assertEqual(paths.overlap_iou_threshold, 0.5)


if __name__ == "__main__":
    unittest.main()
