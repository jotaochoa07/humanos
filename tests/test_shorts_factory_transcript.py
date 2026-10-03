"""Unit tests: transcript.json schema shape + mocked ASR pipeline."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from shorts_factory.backends.transcription import (
    TranscriptionBackend,
    TranscriptionResult,
    TranscriptionSegment,
)
from shorts_factory.contracts import validate_transcript_shape
from shorts_factory.pipeline.captions import write_srt
from shorts_factory.pipeline.transcribe import result_to_document, write_transcript_json


class FakeBackend(TranscriptionBackend):
    def transcribe(self, audio_path, *, language="auto", model="small", device="auto", compute_type="auto"):
        return TranscriptionResult(
            language="es" if language == "auto" else language,
            segments=[
                TranscriptionSegment(id=1, start=0.0, end=1.2, text="Hola mundo"),
                TranscriptionSegment(id=2, start=1.2, end=2.5, text="de prueba"),
            ],
            engine="fake",
            model=model,
            device="cpu",
            compute_type="int8",
            duration_sec=2.5,
        )


class TestTranscriptSchema(unittest.TestCase):
    def test_valid_document(self):
        backend = FakeBackend()
        result = backend.transcribe(Path("dummy.wav"))
        doc = result_to_document(
            result,
            source_video="/tmp/video.mp4",
            duration_sec=10.0,
        )
        self.assertEqual(validate_transcript_shape(doc), [])
        self.assertEqual(doc["engine"], "fake")
        self.assertEqual(doc["model"], "small")
        self.assertEqual(len(doc["segments"]), 2)
        self.assertEqual(doc["segments"][0]["text"], "Hola mundo")

    def test_missing_keys(self):
        errors = validate_transcript_shape({"segments": []})
        self.assertTrue(any("source_video" in e for e in errors))
        self.assertTrue(any("duration_sec" in e for e in errors))

    def test_write_roundtrip(self):
        backend = FakeBackend()
        result = backend.transcribe(Path("dummy.wav"), model="small")
        doc = result_to_document(result, source_video="v.mp4", duration_sec=3.0)
        with tempfile.TemporaryDirectory() as tmp:
            tpath = Path(tmp) / "transcript.json"
            spath = Path(tmp) / "captions.srt"
            write_transcript_json(doc, tpath)
            write_srt(doc["segments"], spath)
            loaded = json.loads(tpath.read_text(encoding="utf-8"))
            self.assertEqual(validate_transcript_shape(loaded), [])
            self.assertTrue(spath.is_file())


class TestDeviceResolve(unittest.TestCase):
    def test_auto_cpu_when_no_cuda(self):
        from shorts_factory.backends.faster_whisper import resolve_device_and_compute

        with mock.patch(
            "shorts_factory.backends.faster_whisper.detect_cuda_available",
            return_value=False,
        ):
            device, compute = resolve_device_and_compute("auto", "auto")
        self.assertEqual(device, "cpu")
        self.assertEqual(compute, "int8")

    def test_auto_cuda_when_available(self):
        from shorts_factory.backends.faster_whisper import resolve_device_and_compute

        with mock.patch(
            "shorts_factory.backends.faster_whisper.detect_cuda_available",
            return_value=True,
        ):
            device, compute = resolve_device_and_compute("auto", "auto")
        self.assertEqual(device, "cuda")
        self.assertEqual(compute, "float16")


if __name__ == "__main__":
    unittest.main()
