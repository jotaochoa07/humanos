"""Unit tests for deterministic M2 post-processing (no API)."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from shorts_factory.backends.ranking import RankingConfig, RawCandidate
from shorts_factory.pipeline.postprocess import (
    nms_by_iou,
    postprocess_candidates,
    snap_candidate_to_segments,
    temporal_iou,
)

FIXTURE = Path(__file__).parent / "fixtures" / "shorts_factory" / "transcript.json"


class TestTemporalIoU(unittest.TestCase):
    def test_no_overlap(self):
        self.assertEqual(temporal_iou(0, 10, 10, 20), 0.0)

    def test_full_overlap(self):
        self.assertAlmostEqual(temporal_iou(0, 10, 0, 10), 1.0)

    def test_partial(self):
        # [0,10] ∩ [5,15] = 5; union = 15 → 1/3
        self.assertAlmostEqual(temporal_iou(0, 10, 5, 15), 5 / 15)


class TestSnap(unittest.TestCase):
    def setUp(self):
        self.doc = json.loads(FIXTURE.read_text(encoding="utf-8"))
        self.segments = self.doc["segments"]
        self.cfg = RankingConfig(
            duration_min_sec=20,
            duration_max_sec=90,
            target_count=8,
            overlap_iou_threshold=0.45,
        )

    def test_snap_to_segment_boundaries(self):
        raw = RawCandidate(
            start=21.5,
            end=50.0,
            hook="hook",
            central_idea="idea",
            selection_reason="reason",
            score=0.9,
            suggested_title="Más agentes no es mejor",
        )
        out = snap_candidate_to_segments(raw, self.segments, config=self.cfg)
        self.assertIsNotNone(out)
        assert out is not None
        # start nearest/containing seg id 4 starts at 20; end expands/trim within window
        self.assertEqual(out["start"], 20.0)
        self.assertGreaterEqual(out["duration_sec"], 20.0)
        self.assertLessEqual(out["duration_sec"], 90.0)
        self.assertIn("más agentes", out["transcript"].lower())
        # must be exact segment boundary values from fixture
        starts = {float(s["start"]) for s in self.segments}
        ends = {float(s["end"]) for s in self.segments}
        self.assertIn(out["start"], starts)
        self.assertIn(out["end"], ends)

    def test_reject_too_short_when_cannot_expand(self):
        # Use tiny window that still allows a short clip, then ask for huge min
        cfg = RankingConfig(duration_min_sec=200, duration_max_sec=300, target_count=3)
        raw = RawCandidate(
            start=0.0,
            end=5.0,
            hook="h",
            central_idea="i",
            selection_reason="r",
            score=0.5,
            suggested_title="x",
        )
        self.assertIsNone(snap_candidate_to_segments(raw, self.segments, config=cfg))


class TestNmsAndPipeline(unittest.TestCase):
    def setUp(self):
        self.doc = json.loads(FIXTURE.read_text(encoding="utf-8"))
        self.cfg = RankingConfig(
            duration_min_sec=20,
            duration_max_sec=90,
            target_count=5,
            overlap_iou_threshold=0.45,
        )

    def test_nms_drops_near_duplicates(self):
        cands = [
            {"start": 0.0, "end": 40.0, "score": 0.9},
            {"start": 5.0, "end": 45.0, "score": 0.8},
            {"start": 100.0, "end": 140.0, "score": 0.7},
        ]
        kept = nms_by_iou(cands, iou_threshold=0.45)
        self.assertEqual(len(kept), 2)
        self.assertEqual(kept[0]["score"], 0.9)
        self.assertEqual(kept[1]["start"], 100.0)

    def test_postprocess_top_n_and_ids(self):
        raw = [
            RawCandidate(20, 55, "h1", "c1", "r1", 0.95, "Organigrama corporativo"),
            RawCandidate(22, 58, "h2", "c2", "r2", 0.90, "Organigrama casi igual"),
            RawCandidate(44, 80, "h3", "c3", "r3", 0.85, "Ejercito de agentes"),
            RawCandidate(100, 140, "h4", "c4", "r4", 0.80, "Contexto saturado"),
            RawCandidate(116, 160, "h5", "c5", "r5", 0.70, "Orquestacion mala"),
            RawCandidate(4, 36, "h6", "c6", "r6", 0.60, "Burocracia de agentes"),
        ]
        out = postprocess_candidates(raw, self.doc, config=self.cfg)
        self.assertLessEqual(len(out), 5)
        self.assertGreaterEqual(len(out), 2)
        ids = [c["id"] for c in out]
        self.assertEqual(ids[0][:3], "01-")
        # scores descending
        scores = [c["score"] for c in out]
        self.assertEqual(scores, sorted(scores, reverse=True))
        for c in out:
            self.assertTrue(20 <= c["duration_sec"] <= 90)
            self.assertTrue(c["folder"].endswith("/"))


if __name__ == "__main__":
    unittest.main()
