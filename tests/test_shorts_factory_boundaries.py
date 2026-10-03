"""Unit tests for light boundary refine (±1) used inside span snap."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from shorts_factory.backends.ranking import RankingConfig, RawCandidate, RawSpan, ScoreDimensions
from shorts_factory.pipeline.postprocess import (
    complete_narrative_unit,
    refine_boundaries,
    snap_candidate_to_segments,
)
from shorts_factory.pipeline.text_heuristics import (
    looks_like_mid_sentence_start,
    looks_like_sentence_end,
)

FIXTURE = Path(__file__).parent / "fixtures" / "shorts_factory" / "boundary_segments.json"


class TestSentenceHeuristics(unittest.TestCase):
    def test_sentence_end(self):
        self.assertTrue(looks_like_sentence_end("Más productividad."))
        self.assertFalse(looks_like_sentence_end("porque la orquestación"))

    def test_mid_sentence_start(self):
        self.assertTrue(looks_like_mid_sentence_start("y entonces copian"))
        self.assertFalse(looks_like_mid_sentence_start("Más agentes no significa"))


class TestLightRefine(unittest.TestCase):
    def setUp(self):
        self.segments = json.loads(FIXTURE.read_text(encoding="utf-8"))["segments"]
        self.cfg = RankingConfig(
            duration_min_sec=16,
            duration_max_sec=90,
            preferred_duration_min_sec=30,
            preferred_duration_max_sec=60,
        )

    def test_expand_start_back_at_most_one(self):
        i0, i1, flags = refine_boundaries(1, 2, self.segments, duration_max_sec=90)
        self.assertEqual(i0, 0)
        self.assertTrue(flags["expanded_start_back"])

    def test_expand_end_forward_at_most_one(self):
        i0, i1, flags = refine_boundaries(6, 6, self.segments, duration_max_sec=90)
        self.assertEqual(i1, 7)
        self.assertTrue(flags["expanded_end_forward"])

    def test_complete_narrative_unit_is_light_only(self):
        # m2-v4: no multi-expand toward max — completeness via spans/gaps
        a, b, counts = complete_narrative_unit(1, 4, self.segments, duration_max_sec=90)
        self.assertEqual(a, 0)  # ±1 back
        self.assertLessEqual(counts["expanded_start_segments"], 1)
        self.assertLessEqual(counts["expanded_end_segments"], 1)
        # end may grow +1 for incomplete seg5
        self.assertLessEqual(b - 4, 1)

    def test_single_span_snap(self):
        raw = RawCandidate(
            9.0, 39.0, "h", "c", "r", 0.9, "Organigrama",
            payoff="p",
            scores=ScoreDimensions(0.8, 0.8, 0.8, 0.8, 0.9),
            spans=[RawSpan("development", 9.0, 39.0)],
        )
        out = snap_candidate_to_segments(raw, self.segments, config=self.cfg)
        self.assertIsNotNone(out)
        assert out is not None
        self.assertEqual(out["span_count"], 1)
        self.assertIn("scores", out)


if __name__ == "__main__":
    unittest.main()
