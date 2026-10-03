"""Unit tests for m2-v3 multi-segment narrative-unit completion."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from shorts_factory.backends.ranking import RankingConfig, RawCandidate, ScoreDimensions
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


class TestCompleteNarrativeUnit(unittest.TestCase):
    def setUp(self):
        self.doc = json.loads(FIXTURE.read_text(encoding="utf-8"))
        self.segments = self.doc["segments"]
        self.cfg = RankingConfig(
            duration_min_sec=16,
            duration_max_sec=90,
            preferred_duration_min_sec=45,
            preferred_duration_max_sec=60,
            target_count=5,
        )

    def test_expand_start_back_when_lowercase_and(self):
        i0, i1, flags = refine_boundaries(1, 2, self.segments, duration_max_sec=90)
        self.assertEqual(i0, 0)
        self.assertTrue(flags["expanded_start_back"])
        self.assertFalse(flags["expanded_end_forward"])

    def test_expand_end_forward_when_incomplete(self):
        i0, i1, flags = refine_boundaries(6, 6, self.segments, duration_max_sec=90)
        self.assertEqual(i1, 7)
        self.assertTrue(flags["expanded_end_forward"])

    def test_multi_segment_expand_within_max(self):
        # Start at incomplete chain: seg2 ("y entonces…") through seg5 incomplete
        # Should expand back multiple if needed and forward until punctuation
        a, b, counts = complete_narrative_unit(
            1, 4, self.segments, duration_max_sec=90
        )
        self.assertEqual(a, 0)
        self.assertGreaterEqual(b, 5)  # at least through "tokens…lentitud."
        self.assertGreaterEqual(counts["expanded_start_segments"], 1)
        self.assertGreaterEqual(counts["expanded_end_segments"], 1)
        # Must stay within max
        dur = float(self.segments[b]["end"]) - float(self.segments[a]["start"])
        self.assertLessEqual(dur, 90)

    def test_no_expand_when_would_exceed_max(self):
        i0, i1, flags = refine_boundaries(1, 2, self.segments, duration_max_sec=16.0)
        self.assertEqual(i0, 1)
        self.assertFalse(flags["expanded_start_back"])

    def test_snap_applies_multi_expand(self):
        raw = RawCandidate(
            start=9.0,
            end=39.0,
            hook="h",
            central_idea="c",
            selection_reason="r",
            score=0.9,
            suggested_title="Organigrama",
            payoff="mejor pensar la arquitectura del trabajo",
            scores=ScoreDimensions(
                hook_strength=0.8,
                context_completeness=0.8,
                conceptual_completeness=0.85,
                standalone_clarity=0.85,
                payoff_strength=0.9,
            ),
        )
        out = snap_candidate_to_segments(raw, self.segments, config=self.cfg)
        self.assertIsNotNone(out)
        assert out is not None
        self.assertEqual(out["start"], 0.0)
        self.assertGreaterEqual(out["end"], 48.0)
        self.assertTrue(out["boundary_refined"])
        self.assertIn("scores", out)
        self.assertIn("hook_strength", out["scores"])
        self.assertTrue(out["transcript"].startswith("Primera idea"))


if __name__ == "__main__":
    unittest.main()
