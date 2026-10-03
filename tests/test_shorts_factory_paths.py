"""Unit tests: path resolution and source_name sanitization."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from shorts_factory.config import (
    DEFAULT_WHISPER_MODEL,
    detect_repo_root,
    resolve_paths,
    sanitize_source_name,
)


class TestSanitizeSourceName(unittest.TestCase):
    def test_stem_from_path(self):
        self.assertEqual(sanitize_source_name("C:/Videos/My Talk!.mp4"), "My-Talk")

    def test_spaces_and_unicode_stripped_to_dashes(self):
        name = sanitize_source_name("buzz agents 2026")
        self.assertEqual(name, "buzz-agents-2026")

    def test_empty_fallback(self):
        self.assertEqual(sanitize_source_name("!!!"), "untitled-source")

    def test_collapse_dashes(self):
        self.assertEqual(sanitize_source_name("a---b"), "a-b")


class TestResolvePaths(unittest.TestCase):
    def test_defaults_whisper_small(self):
        root = detect_repo_root()
        paths = resolve_paths(cwd=root)
        self.assertEqual(paths.whisper_model, DEFAULT_WHISPER_MODEL)
        self.assertEqual(paths.language, "auto")
        self.assertEqual(paths.device, "auto")
        self.assertEqual(paths.compute_type, "auto")
        self.assertTrue(str(paths.outputs_root).endswith("shorts_factory") or "shorts_factory" in str(paths.outputs_root))

    def test_cli_overrides_win(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "custom_out"
            paths = resolve_paths(
                cli_overrides={
                    "outputs": str(out),
                    "whisper_model": "medium",
                    "language": "es",
                    "device": "cpu",
                    "compute_type": "int8",
                    "ffmpeg": "/usr/bin/ffmpeg",
                }
            )
            self.assertEqual(paths.outputs_root, out.resolve())
            self.assertEqual(paths.whisper_model, "medium")
            self.assertEqual(paths.language, "es")
            self.assertEqual(paths.device, "cpu")
            self.assertEqual(paths.ffmpeg_bin(), "/usr/bin/ffmpeg")

    def test_env_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            env_out = str(Path(tmp) / "env_out")
            with mock.patch.dict(os.environ, {"HUMANOS_SHORTS_OUTPUTS": env_out}):
                paths = resolve_paths(cli_overrides={})
            self.assertEqual(paths.outputs_root, Path(env_out).resolve())

    def test_no_hardcoded_windows_user_paths_in_example_config(self):
        example = detect_repo_root() / "config" / "paths.example.yaml"
        text = example.read_text(encoding="utf-8")
        self.assertNotIn("C:\\Users\\", text)
        self.assertNotIn("Antigravity", text)


if __name__ == "__main__":
    unittest.main()
