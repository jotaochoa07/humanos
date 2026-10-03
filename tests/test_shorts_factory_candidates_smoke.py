"""Optional M2 smoke — skipped unless transcript path + OPENROUTER_API_KEY are set."""

from __future__ import annotations

import os
import unittest
from pathlib import Path

from shorts_factory.config import resolve_paths
from shorts_factory.contracts import validate_candidates_shape
from shorts_factory.pipeline.run import run_milestone2


@unittest.skipUnless(
    os.environ.get("HUMANOS_SHORTS_SMOKE_TRANSCRIPT")
    and os.environ.get("OPENROUTER_API_KEY"),
    "Set HUMANOS_SHORTS_SMOKE_TRANSCRIPT and OPENROUTER_API_KEY to run M2 smoke",
)
class TestShortsFactoryCandidatesSmoke(unittest.TestCase):
    def test_milestone2_live_ranker(self):
        transcript = Path(os.environ["HUMANOS_SHORTS_SMOKE_TRANSCRIPT"])
        self.assertTrue(transcript.is_file(), f"transcript not found: {transcript}")
        paths = resolve_paths(
            cli_overrides={
                "target_count": int(os.environ.get("HUMANOS_SHORTS_SMOKE_COUNT", "5")),
            }
        )
        result = run_milestone2(paths, from_transcript=transcript)
        self.assertTrue(result.candidates_json.is_file())
        self.assertEqual(validate_candidates_shape(result.document), [])
        self.assertGreaterEqual(len(result.document["candidates"]), 1)


if __name__ == "__main__":
    unittest.main()
