# Shorts Factory (v0) — Milestone 1

Long horizontal video → timed transcript + SRT sidecar.

**Staging rule (Jota):**

1. **This PR:** `video → transcript.json + captions.srt`
2. Later: `transcript → candidates`
3. Later: `candidates → clips`
4. Later: `9:16 + captions burn-in + previews`

## What milestone 1 does

1. Validate input video (exists, has video+audio streams, duration via ffprobe)
2. Extract mono 16 kHz WAV with **ffmpeg**
3. Transcribe with **faster-whisper** behind `TranscriptionBackend`
4. Write `transcript.json` (segments with timestamps)
5. Write `captions.srt`

## What is NOT implemented yet

- AI candidate selection / ranking
- Clip extraction
- 9:16 reframe (center-crop)
- Burn-in caption preview
- Remotion / DaVinci / CapCut packaging
- UI

## Requirements

- Python ≥ 3.10
- System **ffmpeg** + **ffprobe** on `PATH` (or set `HUMANOS_FFMPEG` / `config.ffmpeg`)
- Python packages: see `requirements-shorts.txt` / `pyproject.toml`

```bash
pip install -r requirements-shorts.txt
# optional: install console script `humanos`
pip install -e .
```

## How to run

Preferred (after `pip install -e .`):

```bash
humanos shorts path/to/long-video.mp4 --whisper-model small
```

Equivalents (no install of the entry point):

```bash
python -m shorts_factory shorts path/to/long-video.mp4 --whisper-model small
python -m shorts_factory.cli shorts path/to/long-video.mp4
```

### Useful flags

| Flag | Default | Notes |
|------|---------|--------|
| `--whisper-model` | `small` | Locked default; also `tiny` / `base` / `medium` / `large-v3` |
| `--language` | `auto` | e.g. `es`, `en` |
| `--device` | `auto` | CUDA if compatible GPU detected, else CPU |
| `--compute-type` | `auto` | `float16` on CUDA, `int8` on CPU |
| `--out` | `outputs/shorts_factory` | Override output root |
| `--ffmpeg` | PATH | Absolute path to ffmpeg if needed |
| `--config` | `config/paths.example.yaml` | Path config (SF7) |
| `--keep-audio` / `--no-keep-audio` | keep | Intermediate `audio.wav` |

## Output layout

```
outputs/shorts_factory/<source_name>/
  transcript.json
  captions.srt
  audio.wav          # intermediate; kept by default
```

`outputs/` is gitignored. Candidate folders (`01-<slug>/`, etc.) are **not** created in milestone 1.

### `transcript.json` shape

```json
{
  "source_video": "/abs/path/to/video.mp4",
  "duration_sec": 360.0,
  "language": "es",
  "engine": "faster-whisper",
  "model": "small",
  "device": "cpu",
  "compute_type": "int8",
  "segments": [
    { "id": 1, "start": 12.4, "end": 18.1, "text": "..." }
  ]
}
```

## Config / paths (SF7)

- Template: `config/paths.example.yaml`
- Env overrides: `HUMANOS_ROOT`, `HUMANOS_SHORTS_OUTPUTS`, `HUMANOS_FFMPEG`, `HUMANOS_ASR_MODELS`, `HUMANOS_PATHS_CONFIG`
- **No hardcoded** `C:\Users\…` or Antigravity paths in code. Working path on Jota’s machine is conceptually `C:\Workspace\Projects\humanos`; runtime resolves from repo/cwd/config.

## Architecture notes

- `TranscriptionBackend` ABC + `FasterWhisperBackend` — ready for medium / large-v3 / API backends later without rewriting the pipeline.
- Module lives at repo root `shorts_factory/` (not under `production_os/`).
- Remotion / npm tooling is untouched.

## Tests

```bash
python -m unittest discover -s tests -p 'test_shorts_factory*.py'
```

ASR is mocked in unit tests (no GPU/models required). Optional smoke:

```bash
HUMANOS_SHORTS_SMOKE_VIDEO=/path/to/video.mp4 python -m unittest tests.test_shorts_factory_smoke
```
