import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from recovery_pipeline import RecoveryPreflightError, validate_recovery_episode


class RecoveryPipelineTests(unittest.TestCase):
    def _episode(self):
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name) / "EP0001_Test"
        recovery = root / "01_RESEARCH_RECOVERY"
        recovery.mkdir(parents=True)
        (root / "episode_config.json").write_text(json.dumps({"input_mode": "recovery"}), encoding="utf-8")
        files = {
            "gate_2d_evidence_pack.json": {"gate": "2D", "status": "PASS"},
            "claims_recovered.json": {"claims": []},
            "timeline_recovered.json": {"events": []},
            "creative_lock.json": {"status": "LOCKED"},
            "human_evidence_bridge.json": {"summary": "verified"},
        }
        entries = []
        for name, value in files.items():
            path = recovery / name
            path.write_text(json.dumps(value), encoding="utf-8")
            entries.append({"path": name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
        (recovery / "panel_recovery_manifest.json").write_text(json.dumps({
            "manifest_version": 1,
            "input_mode": "recovery",
            "research_source": "01_RESEARCH_RECOVERY",
            "forbidden_paths": ["01_RESEARCH"],
            "gate_2d": {"status": "PASS", "evidence_file": "gate_2d_evidence_pack.json"},
            "required_files": entries,
        }), encoding="utf-8")
        return temp, root

    def test_valid_recovery_isolated(self):
        temp, root = self._episode()
        self.addCleanup(temp.cleanup)
        result = validate_recovery_episode(root)
        self.assertTrue(result["legacy_research_excluded"])
        self.assertEqual(result["research_source"], "01_RESEARCH_RECOVERY")

    def test_legacy_source_declaration_fails_closed(self):
        temp, root = self._episode()
        self.addCleanup(temp.cleanup)
        manifest = root / "01_RESEARCH_RECOVERY/panel_recovery_manifest.json"
        data = json.loads(manifest.read_text())
        data["research_source"] = "01_RESEARCH"
        manifest.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaises(RecoveryPreflightError):
            validate_recovery_episode(root)


if __name__ == "__main__":
    unittest.main()
