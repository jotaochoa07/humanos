"""Fail-closed helpers for episode-declared recovery writing."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

RECOVERY_DIR = "01_RESEARCH_RECOVERY"
FORBIDDEN_DIR = "01_RESEARCH"
MANIFEST_NAME = "panel_recovery_manifest.json"
CONFIG_NAME = "episode_config.json"
GATE_EVIDENCE_NAME = "gate_2d_evidence_pack.json"
REQUIRED_RECOVERY_FILES = frozenset(
    {
        GATE_EVIDENCE_NAME,
        "claims_recovered.json",
        "timeline_recovered.json",
        "creative_lock.json",
        "human_evidence_bridge.json",
    }
)


class RecoveryPreflightError(ValueError):
    """Raised when a recovery episode is not safe to execute."""


def _json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RecoveryPreflightError(f"invalid JSON: {path.name}") from error
    if not isinstance(value, dict):
        raise RecoveryPreflightError(f"JSON object required: {path.name}")
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_relative(root: Path, value: str) -> Path:
    """Resolve a manifest path without allowing traversal or legacy research."""
    if not isinstance(value, str) or not value or "\x00" in value:
        raise RecoveryPreflightError("manifest path must be a non-empty string")

    # Treat Windows separators as separators even when tests run on POSIX.
    portable = value.replace("\\", "/")
    if portable.startswith("/") or Path(portable).drive:
        raise RecoveryPreflightError(f"path must be relative to recovery root: {value}")
    parts = tuple(part for part in portable.split("/") if part not in {"", "."})
    if FORBIDDEN_DIR in parts:
        raise RecoveryPreflightError(f"forbidden path referenced: {value}")

    candidate = (root / Path(*parts)).resolve()
    if candidate == root or root not in candidate.parents:
        raise RecoveryPreflightError(f"path escapes recovery root: {value}")
    return candidate


def _config_path(episode: Path, recovery_root: Path) -> Path:
    """Use the episode config, with a recovery-local fallback for isolated episodes."""
    episode_config = episode / CONFIG_NAME
    if episode_config.is_file():
        return episode_config
    recovery_config = recovery_root / CONFIG_NAME
    if recovery_config.is_file():
        return recovery_config
    raise RecoveryPreflightError(f"episode config missing: {CONFIG_NAME}")


def _required_entries(entries: Iterable[Any]) -> dict[str, str]:
    normalized: dict[str, str] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            raise RecoveryPreflightError("invalid required file entry")
        raw_path = entry.get("path")
        digest = entry.get("sha256")
        if not isinstance(raw_path, str) or not isinstance(digest, str):
            raise RecoveryPreflightError("invalid required file entry")
        portable = raw_path.replace("\\", "/")
        if portable in normalized:
            raise RecoveryPreflightError(f"duplicate required file: {raw_path}")
        if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest.lower()):
            raise RecoveryPreflightError(f"invalid sha256: {raw_path}")
        normalized[portable] = digest.lower()
    return normalized


def validate_recovery_episode(episode_path: str | Path) -> dict[str, Any]:
    """Validate declared recovery inputs without opening the legacy research tree."""
    episode = Path(episode_path).resolve()
    recovery_root = (episode / RECOVERY_DIR).resolve()
    if not recovery_root.is_dir() or episode not in recovery_root.parents:
        raise RecoveryPreflightError("invalid recovery root")

    config_path = _config_path(episode, recovery_root)
    config = _json(config_path)
    if config.get("input_mode") != "recovery":
        raise RecoveryPreflightError("episode is not declared as recovery input")

    manifest_path = recovery_root / MANIFEST_NAME
    manifest = _json(manifest_path)
    forbidden_paths = manifest.get("forbidden_paths", [manifest.get("forbidden_path")])
    if (
        manifest.get("input_mode") != "recovery"
        or manifest.get("research_source") != RECOVERY_DIR
        or FORBIDDEN_DIR not in forbidden_paths
        or manifest.get("manifest_version") != 1
    ):
        raise RecoveryPreflightError("manifest does not declare recovery isolation")
    gate = manifest.get("gate_2d", {})
    if gate.get("status") != "PASS" or gate.get("evidence_file") != GATE_EVIDENCE_NAME:
        raise RecoveryPreflightError("Gate 2D PASS evidence is missing")
    files = manifest.get("required_files")
    if not isinstance(files, list) or not files:
        raise RecoveryPreflightError("manifest required_files is missing")
    entries = _required_entries(files)
    if not REQUIRED_RECOVERY_FILES.issubset(entries):
        missing = sorted(REQUIRED_RECOVERY_FILES - entries.keys())
        raise RecoveryPreflightError(f"required recovery files missing: {', '.join(missing)}")

    loaded: dict[str, dict[str, Any]] = {}
    normalized_manifest_files: list[dict[str, str]] = []
    for relative_path, expected_hash in entries.items():
        file_path = _safe_relative(recovery_root, relative_path)
        if not file_path.is_file():
            raise RecoveryPreflightError(f"required file missing: {relative_path}")
        if sha256_file(file_path) != expected_hash:
            raise RecoveryPreflightError(f"hash mismatch: {relative_path}")
        loaded[relative_path] = _json(file_path)
        normalized_manifest_files.append({"path": relative_path, "sha256": expected_hash})

    gate_data = loaded.get(GATE_EVIDENCE_NAME)
    if gate_data is None:
        raise RecoveryPreflightError("Gate 2D evidence file is not loaded")
    if gate_data.get("status") != "PASS" or gate_data.get("gate") != "2D":
        raise RecoveryPreflightError("Gate 2D evidence does not pass")
    normalized_manifest = dict(manifest)
    normalized_manifest["forbidden_paths"] = [FORBIDDEN_DIR]
    normalized_manifest["required_files"] = sorted(normalized_manifest_files, key=lambda item: item["path"])
    return {
        "episode": episode,
        "config": config,
        "config_path": config_path,
        "root": recovery_root,
        "manifest": normalized_manifest,
        "files": loaded,
        "legacy_research_excluded": True,
        "research_source": RECOVERY_DIR,
    }


def recovery_inputs(preflight: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Normalize recovery evidence into existing Gabo inputs plus immutable context."""
    files = preflight.get("files")
    if not isinstance(files, dict):
        raise RecoveryPreflightError("validated recovery files are missing")
    try:
        claims = files["claims_recovered.json"]
        timeline = files["timeline_recovered.json"]
        bridge = files["human_evidence_bridge.json"]
        lock = files["creative_lock.json"]
    except KeyError as error:
        raise RecoveryPreflightError(f"cannot normalize missing recovery input: {error.args[0]}") from error

    claim_items = claims.get("claims", [])
    timeline_items = timeline.get("events", [])
    if not isinstance(claim_items, list) or not isinstance(timeline_items, list):
        raise RecoveryPreflightError("recovery claims and timeline must be lists")
    normalized_claims = [claim for claim in claim_items if isinstance(claim, dict)]
    normalized_events = [event for event in timeline_items if isinstance(event, dict)]
    summary = bridge.get("summary", "")
    if not isinstance(summary, str):
        raise RecoveryPreflightError("human evidence summary must be text")
    subject = claims.get("subject") or bridge.get("subject")
    research = {
        "recovery_mode": True,
        "input_mode": "recovery",
        "research_source": RECOVERY_DIR,
        "legacy_research_excluded": True,
        "subject": subject,
        "human_evidence": summary,
        "claims": normalized_claims,
    }
    approved = {
        "approved_claims": [claim for claim in normalized_claims if str(claim.get("status", "")).startswith("RECOVERED")],
        "rejected_or_blocked_claims": claims.get("claims_excluded", []),
    }
    timeline = {**timeline, "events": normalized_events, "input_mode": "recovery"}
    lock = {**lock, "input_mode": "recovery"}
    bridge = {**bridge, "input_mode": "recovery"}
    return research, timeline, approved, lock, bridge


def recovery_start_plan(episode_path: str | Path) -> dict[str, Any]:
    preflight = validate_recovery_episode(episode_path)
    return {
        "stage": "recovery",
        "episode_path": str(preflight["episode"]),
        "authorized": bool(preflight["config"].get("execution_authorized")),
        "status": preflight["config"].get("panel_status", "recovery_ready"),
        "research_source": RECOVERY_DIR,
        "legacy_research_excluded": True,
        "gabo_ready": False,
    }
