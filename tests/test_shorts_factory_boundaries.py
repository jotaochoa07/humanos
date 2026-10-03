"""Unit tests for M2 sentence-boundary refinement (±1 ASR segment)."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from shorts_factory.backends.ranking import RankingConfig, RawCandidate
from shorts_factory.pipeline.postprocess import (
    looks_like_mid_sentence_start,
    looks_like_sentence_end,
    refine_boundaries,
    snap_candidate_to_segments,
)

FIXTURE = Path(__file__).parent / "fixtures" / "shorts_factory" / "boundary_segments.json"


class TestSentenceHeuristics(unittest.TestCase):
    def test_sentence_end(self):
        self.assertTrue(looks_like_sentence_end("Más productividad."))
        self.assertTrue(looks_like_sentence_end("¿De verdad?"))
        self.assertTrue(looks_like_sentence_end('dijo "basta".'))
        self.assertFalse(looks_like_sentence_end("porque la orquestación"))
        self.assertFalse(looks_like_sentence_end("Un solo agente bien diseñado"))

    def test_mid_sentence_start(self):
        self.assertTrue(looks_like_mid_sentence_start("y entonces copian"))
        self.assertTrue(looks_like_mid_sentence_start("porque la orquestación"))
        self.assertTrue(looks_like_mid_sentence_start("but the cost rises"))
        self.assertFalse(looks_like_mid_sentence_start("Más agentes no significa"))
        self.assertFalse(looks_like_mid_sentence_start("Primera idea completa"))


class TestRefineBoundaries(unittest.TestCase):
    def setUp(self):
        self.doc = json.loads(FIXTURE.read_text(encoding="utf-8"))
        self.segments = self.doc["segments"]
        self.cfg = RankingConfig(
            duration_min_sec=16,
            duration_max_sec=90,
            target_count=5,
        )

    def test_expand_start_back_when_lowercase_and(self):
        # Start at seg 2 ("y entonces…") → should pull seg 1
        i0, i1, flags = refine_boundaries(1, 2, self.segments, duration_max_sec=90)
        self.assertEqual(i0, 0)
        self.assertTrue(flags["expanded_start_back"])
        # End seg 3 ends with "." → no forward expand needed
        self.assertFalse(flags["expanded_end_forward"])

    def test_expand_end_forward_when_incomplete(self):
        # Seg 7 incomplete → pull seg 8
        i0, i1, flags = refine_boundaries(6, 6, self.segments, duration_max_sec=90)
        self.assertEqual(i1, 7)
        self.assertTrue(flags["expanded_end_forward"])

    def test_at_most_one_segment_each_side(self):
        # Mid start at 2 and incomplete end at 5 ("porque…") spanning 2..5
        i0, i1, flags = refine_boundaries(1, 4, self.segments, duration_max_sec=90)
        self.assertEqual(i0, 0)  # only -1
        self.assertEqual(i1, 5)  # only +1
        self.assertTrue(flags["expanded_start_back"])
        self.assertTrue(flags["expanded_end_forward"])

    def test_no_expand_when_would_exceed_max(self):
        # Tiny max: cannot expand
        i0, i1, flags = refine_boundaries(1, 2, self.segments, duration_max_sec=16.0)
        # span 1..2 is 16s already; expanding back would be 24s > 16
        self.assertEqual(i0, 1)
        self.assertFalse(flags["expanded_start_back"])

    def test_snap_applies_boundary_refinement(self):
        # Raw proposes mid-sentence start (seg2) through incomplete end (seg5)
        raw = RawCandidate(
            start=9.0,
            end=39.0,
            hook="h",
            central_idea="c",
            selection_reason="r",
            score=0.9,
            suggested_title="Organigrama",
        )
        out = snap_candidate_to_segments(raw, self.segments, config=self.cfg)
        self.assertIsNotNone(out)
        assert out is not None
        # Should expand back to seg1 start 0.0 and forward to seg6 end 48.0
        self.assertEqual(out["start"], 0.0)
        self.assertEqual(out["end"], 48.0)
        self.assertTrue(out["boundary_refined"])
        self.assertTrue(out["transcript"].startswith("Primera idea"))
        self.assertTrue(out["transcript"].rstrip().endswith("."))


if __name__ == "__main__":
    unittest.main()
