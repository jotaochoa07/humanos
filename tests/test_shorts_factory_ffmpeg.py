"""Integration: validate + extract_audio with real ffmpeg (no Whisper)."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from shorts_factory.pipeline.extract_audio import extract_audio
from shorts_factory.pipeline.validate import validate_video


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "ffmpeg/ffprobe required")
class TestFfmpegIngest(unittest.TestCase):
    def test_validate_and_extract(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            video = tmp_path / "tiny.mp4"
            # 1s color + sine tone
            cmd = [
                "ffmpeg",
                "-y",
                "-f",
                "lavfi",
                "-i",
                "color=c=black:s=320x240:d=1",
                "-f",
                "lavfi",
                "-i",
                "sine=frequency=440:duration=1",
                "-c:v",
                "libx264",
                "-c:a",
                "aac",
                "-shortest",
                str(video),
            ]
            proc = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stderr)

            info = validate_video(video)
            self.assertGreater(info.duration_sec, 0.5)
            self.assertTrue(info.has_audio)

            audio = tmp_path / "audio.wav"
            extract_audio(video, audio)
            self.assertTrue(audio.is_file())
            self.assertGreater(audio.stat().st_size, 100)


if __name__ == "__main__":
    unittest.main()
