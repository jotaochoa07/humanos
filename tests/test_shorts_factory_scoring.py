"""Unit tests for m2-v3 score dimensions and standalone penalties."""

from __future__ import annotations

import unittest

from shorts_factory.backends.ranking import ScoreDimensions
from shorts_factory.contracts import validate_candidates_shape
from shorts_factory.pipeline.scoring import (
    compose_final_score,
    parse_score_dimensions,
    standalone_penalties,
    weighted_dimension_score,
)


class TestScoreDimensions(unittest.TestCase):
    def test_parse_flat_and_nested(self):
        dims = parse_score_dimensions(
            {
                "score": 0.7,
                "hook_strength": 0.9,
                "scores": {"payoff_strength": 0.8},
            }
        )
        self.assertAlmostEqual(dims.hook_strength, 0.9)
        self.assertAlmostEqual(dims.payoff_strength, 0.8)
        # missing keys seeded from score
        self.assertAlmostEqual(dims.context_completeness, 0.7)

    def test_weighted_base(self):
        dims = ScoreDimensions(0.5, 0.5, 0.5, 0.5, 0.5)
        self.assertAlmostEqual(weighted_dimension_score(dims), 0.5)


class TestPenalties(unittest.TestCase):
    def test_pronoun_start_penalized(self):
        p, reasons = standalone_penalties(
            start_text="Esto no escala en producción",
            end_text="Por eso hay que rediseñar.",
            full_transcript="Esto no escala en producción. Por eso hay que rediseñar.",
            payoff_text="hay que rediseñar",
            dims=ScoreDimensions(0.8, 0.8, 0.8, 0.8, 0.8),
        )
        self.assertGreater(p, 0.15)
        self.assertIn("pronoun_start_without_context", reasons)

    def test_incomplete_end_penalized(self):
        p, reasons = standalone_penalties(
            start_text="Más agentes no dan más productividad",
            end_text="porque la orquestación",
            full_transcript="Más agentes no dan más productividad porque la orquestación",
            payoff_text="",
            dims=ScoreDimensions(0.7, 0.7, 0.7, 0.7, 0.2),
        )
        self.assertGreater(p, 0.3)
        self.assertTrue(
            "incomplete_sentence_end" in reasons
            or "observation_without_resolution" in reasons
        )

    def test_prior_context_dependency(self):
        p, reasons = standalone_penalties(
            start_text="Como dije antes, el costo sube",
            end_text="Y por eso falla.",
            full_transcript="Como dije antes, el costo sube. Y por eso falla.",
            payoff_text="falla",
            dims=ScoreDimensions(0.8, 0.8, 0.8, 0.8, 0.8),
        )
        self.assertIn("depends_on_prior_context", reasons)
        self.assertGreater(p, 0.1)

    def test_compose_final_heavy_penalty(self):
        dims = ScoreDimensions(0.9, 0.9, 0.9, 0.9, 0.9)
        score, penalty, reasons = compose_final_score(
            dims,
            start_text="y entonces copian el organigrama",
            end_text="porque la orquestación",
            full_transcript="y entonces copian el organigrama porque la orquestación",
            payoff_text="",
            duration_sec=22,
        )
        self.assertGreaterEqual(penalty, 0.35)
        # Heavy penalty: even strong dims (~0.9) should drop below ~0.65
        self.assertLess(score, 0.65)


class TestCandidatesSchemaM2V3(unittest.TestCase):
    def test_requires_scores_when_m2_v3(self):
        doc = {
            "source_video": "x",
            "generated_at": "t",
            "snap_rules_version": "m2-v3",
            "config": {
                "duration_min_sec": 20,
                "duration_max_sec": 90,
                "target_count": 5,
            },
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
                }
            ],
        }
        errors = validate_candidates_shape(doc)
        self.assertTrue(any("scores" in e for e in errors))

    def test_valid_m2_v3_shape(self):
        doc = {
            "source_video": "x",
            "generated_at": "t",
            "snap_rules_version": "m2-v3",
            "config": {
                "duration_min_sec": 20,
                "duration_max_sec": 90,
                "target_count": 5,
            },
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
        self.assertEqual(validate_candidates_shape(doc), [])


if __name__ == "__main__":
    unittest.main()
