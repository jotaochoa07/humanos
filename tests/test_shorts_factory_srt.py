"""Unit tests: SRT generation for Shorts Factory milestone 1."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from shorts_factory.pipeline.captions import (
    format_srt_timestamp,
    segments_to_srt,
    write_srt,
)


class TestSrtTimestamps(unittest.TestCase):
    def test_zero(self):
        self.assertEqual(format_srt_timestamp(0), "00:00:00,000")

    def test_fractional(self):
        self.assertEqual(format_srt_timestamp(1.5), "00:00:01,500")

    def test_hours(self):
        self.assertEqual(format_srt_timestamp(3661.234), "01:01:01,234")

    def test_negative_clamped(self):
        self.assertEqual(format_srt_timestamp(-1), "00:00:00,000")


class TestSegmentsToSrt(unittest.TestCase):
    def test_basic_blocks(self):
        segments = [
            {"id": 1, "start": 0.0, "end": 1.0, "text": "Hola"},
            {"id": 2, "start": 1.5, "end": 3.25, "text": "mundo"},
        ]
        srt = segments_to_srt(segments)
        self.assertIn("1\n00:00:00,000 --> 00:00:01,000\nHola", srt)
        self.assertIn("2\n00:00:01,500 --> 00:00:03,250\nmundo", srt)

    def test_skips_empty_text(self):
        segments = [
            {"id": 1, "start": 0.0, "end": 1.0, "text": "  "},
            {"id": 2, "start": 1.0, "end": 2.0, "text": "ok"},
        ]
        srt = segments_to_srt(segments)
        self.assertNotIn("--> 00:00:01,000", srt.split("ok")[0] if False else srt)
        self.assertIn("ok", srt)
        self.assertEqual(srt.count("-->"), 1)

    def test_write_srt_file(self):
        segments = [{"id": 1, "start": 0.0, "end": 0.5, "text": "x"}]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "captions.srt"
            write_srt(segments, path)
            self.assertTrue(path.is_file())
            self.assertIn("x", path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
