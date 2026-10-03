"""Pipeline milestone 1 with mocked ffmpeg / ASR (CI-safe)."""

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
from shorts_factory.config import PathsConfig
from shorts_factory.contracts import validate_transcript_shape
from shorts_factory.pipeline.run import run_milestone1
from shorts_factory.pipeline.validate import VideoInfo


class MockBackend(TranscriptionBackend):
    def transcribe(self, audio_path, *, language="auto", model="small", device="auto", compute_type="auto"):
        return TranscriptionResult(
            language="en",
            segments=[
                TranscriptionSegment(id=1, start=0.0, end=2.0, text="Hello"),
                TranscriptionSegment(id=2, start=2.0, end=4.0, text="world"),
            ],
            engine="mock-whisper",
            model=model,
            device="cpu",
            compute_type="int8",
            duration_sec=4.0,
        )


class TestMilestone1Pipeline(unittest.TestCase):
    def test_run_writes_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            video = tmp_path / "sample-talk.mp4"
            video.write_bytes(b"fake")  # not opened by mocked validate
            outputs = tmp_path / "outputs" / "shorts_factory"
            paths = PathsConfig(
                repo_root=tmp_path,
                outputs_root=outputs,
                ffmpeg="ffmpeg",
                asr_models=None,
                input_media=None,
                whisper_model="small",
                language="auto",
                device="cpu",
                compute_type="int8",
            )

            video_info = VideoInfo(
                path=video.resolve(),
                duration_sec=4.0,
                width=1920,
                height=1080,
                has_audio=True,
            )

            def fake_extract(video_path, audio_out, *, ffmpeg_bin="ffmpeg", sample_rate=16000):
                audio_out = Path(audio_out)
                audio_out.parent.mkdir(parents=True, exist_ok=True)
                audio_out.write_bytes(b"RIFF")
                return audio_out

            with mock.patch(
                "shorts_factory.pipeline.run.validate_video",
                return_value=video_info,
            ), mock.patch(
                "shorts_factory.pipeline.run.extract_audio",
                side_effect=fake_extract,
            ):
                result = run_milestone1(
                    video,
                    paths,
                    backend=MockBackend(),
                    keep_audio=True,
                )

            self.assertTrue(result.transcript_json.is_file())
            self.assertTrue(result.captions_srt.is_file())
            self.assertTrue(result.audio_wav.is_file())
            self.assertEqual(result.source_name, "sample-talk")
            doc = json.loads(result.transcript_json.read_text(encoding="utf-8"))
            self.assertEqual(validate_transcript_shape(doc), [])
            self.assertEqual(doc["model"], "small")
            srt = result.captions_srt.read_text(encoding="utf-8")
            self.assertIn("Hello", srt)
            self.assertIn("world", srt)


class TestCliHelp(unittest.TestCase):
    def test_cli_shorts_help(self):
        from shorts_factory.cli import main

        with self.assertRaises(SystemExit) as ctx:
            main(["shorts", "--help"])
        self.assertEqual(ctx.exception.code, 0)

    def test_cli_no_command(self):
        from shorts_factory.cli import main

        code = main([])
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
