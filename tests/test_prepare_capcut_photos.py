import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "prepare_capcut_photos.py"
SPEC = importlib.util.spec_from_file_location("prepare_capcut_photos", MODULE_PATH)
prep = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = prep
assert SPEC.loader is not None
SPEC.loader.exec_module(prep)


class PrepareCapcutPhotosTests(unittest.TestCase):
    def test_discovery_only_applies_mechanical_exclusions(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary)
            (source / "historical.jpg").write_bytes(b"x")
            (source / "Character_card_horizontal.png").write_bytes(b"x")
            (source / "kling").mkdir()
            (source / "kling" / "scene.png").write_bytes(b"x")

            candidates = dict((path.name, reason) for path, reason in prep.discover_images(source))

            self.assertEqual(candidates["historical.jpg"], "")
            self.assertTrue(candidates["Character_card_horizontal.png"])
            self.assertTrue(candidates["scene.png"])

    def test_visual_decision_creates_descriptive_numbered_plan(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary)
            (source / "portrait.jpg").write_bytes(b"x")
            decisions = {
                "portrait.jpg": prep.Decision(
                    source="portrait.jpg",
                    status="INCLUDE",
                    asset_name="Ferruccio portrait",
                    movement="ZOOM_IN",
                    subject="Ferruccio face and torso",
                    crop_notes="Centered 16:9 crop keeps the face intact.",
                )
            }
            plan = prep.build_plan(prep.discover_images(source), source, decisions)

            self.assertEqual(plan[0]["master_clip"], "01_CLIPS/001_FERRUCCIO_PORTRAIT__ZOOM_IN.mp4")
            self.assertEqual(plan[0]["status"], "PLANNED")

    def test_pan_direction_is_passed_to_ffmpeg_skill_helper(self):
        arguments = prep.insert_arguments(
            Path("source.jpg"), Path("output.mp4"), "PAN_RIGHT_ZOOM", 5.0
        )

        self.assertIn("--pan", arguments)
        self.assertEqual(arguments[arguments.index("--pan") + 1], "right")
        self.assertEqual(arguments[arguments.index("--zoom") + 1], "in")
    def test_dry_run_creates_no_episode_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            episode = Path(temporary) / "EP0005"
            source = episode / "04_IMAGES"
            source.mkdir(parents=True)
            (source / "photo.jpg").write_bytes(b"x")

            self.assertEqual(prep.main(["--episode", str(episode), "--dry-run"]), 0)
            self.assertFalse((episode / prep.OUTPUT_RELATIVE).exists())


if __name__ == "__main__":
    unittest.main()
