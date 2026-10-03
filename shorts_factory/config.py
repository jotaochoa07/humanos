"""Path resolution and source-name sanitization for Shorts Factory (SF7).

Never hardcode machine-specific absolute paths (Windows or otherwise).
Resolve from: CLI overrides → env → config YAML → repo-relative defaults.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Mapping, MutableMapping, Optional

try:
    import yaml
except ImportError:  # pragma: no cover - optional until PyYAML installed
    yaml = None  # type: ignore


# Env overrides (SF7)
ENV_REPO_ROOT = "HUMANOS_ROOT"
ENV_OUTPUTS = "HUMANOS_SHORTS_OUTPUTS"
ENV_FFMPEG = "HUMANOS_FFMPEG"
ENV_ASR_MODELS = "HUMANOS_ASR_MODELS"
ENV_PATHS_CONFIG = "HUMANOS_PATHS_CONFIG"

DEFAULT_OUTPUTS_REL = "outputs/shorts_factory"
DEFAULT_WHISPER_MODEL = "small"
DEFAULT_LANGUAGE = "auto"
DEFAULT_DEVICE = "auto"
DEFAULT_COMPUTE_TYPE = "auto"

_SOURCE_NAME_RE = re.compile(r"[^a-zA-Z0-9._-]+")


def detect_repo_root(start: Optional[Path] = None) -> Path:
    """Walk upward from *start* (or this file) looking for repo markers."""
    here = (start or Path(__file__)).resolve()
    if here.is_file():
        here = here.parent
    for candidate in [here, *here.parents]:
        if (candidate / "AGENTS.md").is_file() and (candidate / "package.json").is_file():
            return candidate
        if (candidate / ".git").exists() and (candidate / "AGENTS.md").is_file():
            return candidate
    # Fallback: parent of shorts_factory/
    return Path(__file__).resolve().parent.parent


def sanitize_source_name(path_or_name: str | Path) -> str:
    """Derive a filesystem-safe folder name from a video path or stem."""
    raw = Path(path_or_name).stem if Path(str(path_or_name)).suffix else str(path_or_name)
    raw = raw.strip().replace(" ", "-")
    cleaned = _SOURCE_NAME_RE.sub("-", raw).strip(".-_")
    if not cleaned:
        cleaned = "untitled-source"
    # Collapse repeated dashes
    cleaned = re.sub(r"-{2,}", "-", cleaned)
    return cleaned[:120]


def load_paths_yaml(config_path: Optional[Path] = None) -> dict[str, Any]:
    """Load `config/paths.example.yaml` or override path; empty dict if missing."""
    if config_path is None:
        env = os.environ.get(ENV_PATHS_CONFIG)
        if env:
            config_path = Path(env)
        else:
            config_path = detect_repo_root() / "config" / "paths.example.yaml"
    path = Path(config_path)
    if not path.is_file():
        return {}
    if yaml is None:
        return {}
    with path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    if not isinstance(data, dict):
        raise ValueError(f"paths config must be a mapping: {path}")
    return data


def _as_optional_path(value: Any, base: Path) -> Optional[Path]:
    if value is None or value == "" or value == "null":
        return None
    p = Path(str(value))
    if not p.is_absolute():
        p = (base / p).resolve()
    return p


class PathsConfig:
    """Resolved runtime paths + transcription defaults for milestone 1."""

    def __init__(
        self,
        *,
        repo_root: Path,
        outputs_root: Path,
        ffmpeg: Optional[str],
        asr_models: Optional[Path],
        input_media: Optional[Path],
        whisper_model: str = DEFAULT_WHISPER_MODEL,
        language: str = DEFAULT_LANGUAGE,
        device: str = DEFAULT_DEVICE,
        compute_type: str = DEFAULT_COMPUTE_TYPE,
        transcription_backend: str = "faster_whisper",
    ) -> None:
        self.repo_root = repo_root
        self.outputs_root = outputs_root
        self.ffmpeg = ffmpeg  # None → "ffmpeg" on PATH
        self.asr_models = asr_models
        self.input_media = input_media
        self.whisper_model = whisper_model
        self.language = language
        self.device = device
        self.compute_type = compute_type
        self.transcription_backend = transcription_backend

    def source_output_dir(self, source_name: str) -> Path:
        return self.outputs_root / sanitize_source_name(source_name)

    def ffmpeg_bin(self) -> str:
        return self.ffmpeg or "ffmpeg"


def resolve_paths(
    *,
    cli_overrides: Optional[Mapping[str, Any]] = None,
    config_path: Optional[Path] = None,
    cwd: Optional[Path] = None,
) -> PathsConfig:
    """Merge YAML + env + CLI into a PathsConfig. CLI wins over env over YAML."""
    overrides: MutableMapping[str, Any] = dict(cli_overrides or {})
    yaml_data = load_paths_yaml(config_path)

    env_root = os.environ.get(ENV_REPO_ROOT)
    yaml_root = yaml_data.get("repo_root")
    if overrides.get("repo_root"):
        repo_root = Path(overrides["repo_root"]).resolve()
    elif env_root:
        repo_root = Path(env_root).resolve()
    elif yaml_root:
        repo_root = Path(str(yaml_root)).resolve()
    else:
        repo_root = detect_repo_root(cwd)

    # outputs
    if overrides.get("outputs"):
        outputs = Path(overrides["outputs"])
    elif os.environ.get(ENV_OUTPUTS):
        outputs = Path(os.environ[ENV_OUTPUTS])
    else:
        outputs_val = yaml_data.get("outputs") or DEFAULT_OUTPUTS_REL
        outputs = Path(str(outputs_val))
    if not outputs.is_absolute():
        outputs = (repo_root / outputs).resolve()

    # ffmpeg
    if overrides.get("ffmpeg"):
        ffmpeg = str(overrides["ffmpeg"])
    elif os.environ.get(ENV_FFMPEG):
        ffmpeg = os.environ[ENV_FFMPEG]
    else:
        ffmpeg_val = yaml_data.get("ffmpeg")
        ffmpeg = str(ffmpeg_val) if ffmpeg_val not in (None, "", "null") else None

    # asr models cache
    if overrides.get("asr_models"):
        asr_models = Path(overrides["asr_models"]).resolve()
    elif os.environ.get(ENV_ASR_MODELS):
        asr_models = Path(os.environ[ENV_ASR_MODELS]).resolve()
    else:
        asr_models = _as_optional_path(yaml_data.get("asr_models"), repo_root)

    input_media = _as_optional_path(
        overrides.get("input_media", yaml_data.get("input_media")),
        repo_root,
    )

    tx = yaml_data.get("transcription") or {}
    if not isinstance(tx, dict):
        tx = {}

    whisper_model = str(
        overrides.get("whisper_model")
        or tx.get("model")
        or DEFAULT_WHISPER_MODEL
    )
    language = str(overrides.get("language") or tx.get("language") or DEFAULT_LANGUAGE)
    device = str(overrides.get("device") or tx.get("device") or DEFAULT_DEVICE)
    compute_type = str(
        overrides.get("compute_type") or tx.get("compute_type") or DEFAULT_COMPUTE_TYPE
    )
    backend = str(tx.get("backend") or "faster_whisper")

    return PathsConfig(
        repo_root=repo_root,
        outputs_root=outputs,
        ffmpeg=ffmpeg,
        asr_models=asr_models,
        input_media=input_media,
        whisper_model=whisper_model,
        language=language,
        device=device,
        compute_type=compute_type,
        transcription_backend=backend,
    )
