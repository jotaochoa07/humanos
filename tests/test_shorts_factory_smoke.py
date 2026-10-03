"""Optional smoke test — skipped unless HUMANOS_SHORTS_SMOKE_VIDEO is set.

Requires: ffmpeg, faster-whisper, and a real video path.
"""

from __future__ import annotations

import os
import unittest
from pathlib import Path

from shorts_factory.config import resolve_paths
from shorts_factory.contracts import validate_transcript_shape
from shorts_factory.pipeline.run import run_milestone1


@unittest.skipUnless(
    os.environ.get("HUMANOS_SHORTS_SMOKE_VIDEO"),
    "Set HUMANOS_SHORTS_SMOKE_VIDEO to a real video path to run smoke test",
)
class TestShortsFactorySmoke(unittest.TestCase):
    def test_milestone1_end_to_end(self):
        video = Path(os.environ["HUMANOS_SHORTS_SMOKE_VIDEO"])
        self.assertTrue(video.is_file(), f"Smoke video not found: {video}")
        paths = resolve_paths(
            cli_overrides={
                "whisper_model": os.environ.get("HUMANOS_SHORTS_SMOKE_MODEL", "tiny"),
                "device": "cpu",
            }
        )
        result = run_milestone1(video, paths, keep_audio=True)
        self.assertTrue(result.transcript_json.is_file())
        self.assertTrue(result.captions_srt.is_file())
        self.assertEqual(validate_transcript_shape(result.transcript), [])


if __name__ == "__main__":
    unittest.main()
