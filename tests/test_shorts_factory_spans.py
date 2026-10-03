"""Unit tests for m2-v4 semantic spans."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from shorts_factory.backends.ranking import RankingConfig, RawCandidate, RawSpan, ScoreDimensions
from shorts_factory.contracts import validate_candidates_shape
from shorts_factory.pipeline.postprocess import postprocess_candidates, snap_candidate_to_segments
from shorts_factory.pipeline.spans import validate_and_snap_spans

FIXTURE = Path(__file__).parent / "fixtures" / "shorts_factory" / "transcript.json"
BOUNDARY = Path(__file__).parent / "fixtures" / "shorts_factory" / "boundary_segments.json"


class TestSpanValidation(unittest.TestCase):
    def setUp(self):
        self.segments = json.loads(BOUNDARY.read_text(encoding="utf-8"))["segments"]
        self.cfg = RankingConfig(
            duration_min_sec=16,
            duration_max_sec=90,
            preferred_duration_min_sec=30,
            preferred_duration_max_sec=60,
        )

    def test_invalid_order_rejected(self):
        spans = [
            RawSpan("payoff", 40, 48),
            RawSpan("hook", 0, 8),
        ]
        snapped, errors = validate_and_snap_spans(spans, self.segments, config=self.cfg)
        self.assertEqual(snapped, [])
        self.assertTrue(any("order" in e for e in errors))

    def test_multi_span_within_max_total(self):
        spans = [
            RawSpan("hook", 0, 8),
            RawSpan("development", 24, 40),
            RawSpan("payoff", 48, 64),
        ]
        snapped, errors = validate_and_snap_spans(spans, self.segments, config=self.cfg)
        self.assertEqual(errors, [])
        self.assertEqual(len(snapped), 3)
        total = sum(s["duration_sec"] for s in snapped)
        self.assertGreaterEqual(total, 16)
        self.assertLessEqual(total, 90)
        # gap between first and second
        self.assertGreater(snapped[1]["start"], snapped[0]["end"])

    def test_single_span_passthrough(self):
        raw = RawCandidate(
            24, 48, "h", "c", "r", 0.9, "Title",
            payoff="p",
            scores=ScoreDimensions(0.85, 0.85, 0.85, 0.85, 0.85),
            spans=[RawSpan("development", 24, 48)],
        )
        out = snap_candidate_to_segments(raw, self.segments, config=self.cfg)
        self.assertIsNotNone(out)
        assert out is not None
        self.assertEqual(out["span_count"], 1)
        self.assertEqual(out["spans"][0]["role"], "development")
        self.assertAlmostEqual(out["duration_sec"], out["envelope_duration_sec"])


class TestPostprocessSpans(unittest.TestCase):
    def test_prefers_spoken_sum_duration(self):
        doc = json.loads(FIXTURE.read_text(encoding="utf-8"))
        cfg = RankingConfig(
            duration_min_sec=20,
            duration_max_sec=90,
            preferred_duration_min_sec=30,
            preferred_duration_max_sec=60,
            target_count=3,
        )
        d = ScoreDimensions(0.9, 0.9, 0.9, 0.9, 0.9)
        raw = [
            RawCandidate(
                0, 60, "h", "organigrama to architecture", "r", 0.95, "Org chart",
                payoff="mejor arquitectura",
                scores=d,
                spans=[
                    RawSpan("hook", 4, 20),
                    RawSpan("payoff", 44, 60),
                ],
            ),
        ]
        out = postprocess_candidates(raw, doc, config=cfg)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["span_count"], 2)
        # spoken < envelope when gap exists
        self.assertLess(out[0]["duration_sec"], out[0]["envelope_duration_sec"])


class TestSchemaM2V4(unittest.TestCase):
    def test_requires_spans(self):
        doc = {
            "source_video": "x",
            "generated_at": "t",
            "snap_rules_version": "m2-v4",
            "config": {"duration_min_sec": 20, "duration_max_sec": 90, "target_count": 5},
            "candidates": [
                {
                    "id": "01-a",
                    "start": 1,
                    "end": 40,
                    "duration_sec": 39,
                    "transcript": "t",
                    "hook": "h",
                    "central_idea": "c",
                    "selection_reason": "r",
                    "score": 0.8,
                    "suggested_title": "A",
                    "scores": {
                        "hook_strength": 0.8,
                        "context_completeness": 0.8,
                        "conceptual_completeness": 0.8,
                        "standalone_clarity": 0.8,
                        "payoff_strength": 0.8,
                    },
                }
            ],
        }
        errors = validate_candidates_shape(doc)
        self.assertTrue(any("spans" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
