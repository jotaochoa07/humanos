# Shorts Factory (v0) — Milestones 1–2

Long horizontal video → timed transcript + SRT → ranked Shorts candidates.

**Staging rule (Jota):**

1. **Done (M1):** `video → transcript.json + captions.srt`
2. **This PR (M2):** `transcript → candidates.json` (no video cut)
3. Later: `candidates → clips`
4. Later: `9:16 + captions burn-in + previews`

## Milestone 1 — closed QA decisions (2026-10-03)

- QA approved: UTF-8 SRT OK; faster-whisper **`small`** good enough for MVP.
- Known ASR errors on tech terms (e.g. "agentes de IA"→"agentes de ella", "un solo agente"→"un solo gente") — **do NOT bump to `medium`**.
- Keep **`small`** as the default model.
- Future optional iteration (**not M2**): glossary / context prompt; post-processing of known terms; technical entity correction.

## What milestone 2 does

1. Load `transcript.json` (from M1 run dir or `--from-transcript`)
2. Ask a pluggable **`CandidateRanker`** (default: OpenRouter LLM) to propose moments
3. Deterministic post-steps:
   - Snap start/end to ASR segment boundaries
   - Filter by duration window (default 20–90 s)
   - NMS / dedupe by temporal overlap IoU
   - Sort by score, take top N (default 8)
4. Write deterministic-shape `candidates.json`

## What is NOT implemented yet

- Clip extraction / ffmpeg cut
- 9:16 reframe (center-crop)
- Burn-in caption preview
- Glossary / ASR post-correction
- Remotion / DaVinci / CapCut packaging
- UI

## Timestamp grounding rules

LLM timestamps are approximate. The pipeline always re-grounds them:

1. **Start snap** → start of the ASR segment containing (or nearest to) the proposed start  
2. **End snap** → end of the ASR segment containing (or nearest to) the proposed end  
3. Expand by whole following segments until `duration >= min`  
4. Trim trailing whole segments until `duration <= max`  
5. Reject if still outside the window  
6. Rebuild `transcript` text from the inclusive ASR span (never trust LLM copy for timing)

See `shorts_factory/pipeline/postprocess.py` docstring for the full rules (`snap_rules_version: m2-v1`).

## Requirements

- Python ≥ 3.10
- System **ffmpeg** + **ffprobe** on `PATH` (M1)
- `OPENROUTER_API_KEY` for live M2 ranking (unit tests mock the ranker)
- Python packages: see `requirements-shorts.txt` / `pyproject.toml`

```bash
pip install -r requirements-shorts.txt
pip install -e .
```

## How to run

### Full pipeline (M1 → M2)

```bash
humanos shorts path/to/long-video.mp4 --whisper-model small
# equivalent:
python -m shorts_factory shorts path/to/long-video.mp4
```

Reuses existing `transcript.json` under the source output dir unless `--force-transcribe`.  
M1 only: add `--skip-candidates`.

### Milestone 2 only (from prior M1 outputs)

```bash
humanos shorts candidates outputs/shorts_factory/<source_name>/
humanos shorts candidates --from-transcript outputs/shorts_factory/<source_name>/transcript.json
```

### Useful flags

| Flag | Default | Notes |
|------|---------|--------|
| `--whisper-model` | `small` | Locked; do not bump for tech-term ASR typos |
| `--min-duration` / `--max-duration` | `20` / `90` | Candidate duration window |
| `--count` | `8` | Target candidates (aim 5–10) |
| `--overlap-iou` | `0.45` | NMS near-duplicate threshold |
| `--ranker-model` | env / flash-lite | OpenRouter model id |
| `--skip-candidates` | off | M1 only |
| `--skip-transcribe` | off | Reuse transcript; run M2 |
| `--force-transcribe` | off | Re-run ASR |
| `--out` | `outputs/shorts_factory` | Output root |
| `--keep-audio` / `--no-keep-audio` | keep | Intermediate `audio.wav` |

## Output layout

```
outputs/shorts_factory/<source_name>/
  transcript.json
  captions.srt
  audio.wav              # intermediate; kept by default
  candidates.json        # M2
```

`outputs/` is gitignored. Per-candidate media folders (`01-<slug>/`, etc.) are **not** created in M2 (no clips yet). The `folder` field is reserved for M3+.

### `candidates.json` shape

```json
{
  "source_video": "/abs/path/to/video.mp4",
  "generated_at": "2026-10-03T12:00:00+00:00",
  "milestone": 2,
  "ranker": "OpenRouterCandidateRanker",
  "snap_rules_version": "m2-v1",
  "config": {
    "duration_min_sec": 20,
    "duration_max_sec": 90,
    "target_count": 8,
    "overlap_iou_threshold": 0.45
  },
  "candidates": [
    {
      "id": "01-example-slug",
      "start": 45.2,
      "end": 78.6,
      "duration_sec": 33.4,
      "transcript": "...",
      "hook": "...",
      "central_idea": "...",
      "selection_reason": "...",
      "score": 0.87,
      "suggested_title": "...",
      "folder": "01-example-slug/",
      "segment_id_start": 12,
      "segment_id_end": 20
    }
  ]
}
```

## Config / paths (SF7)

- Template: `config/paths.example.yaml` (includes `duration` + `ranking` knobs)
- Env: `HUMANOS_ROOT`, `HUMANOS_SHORTS_OUTPUTS`, `HUMANOS_FFMPEG`, `HUMANOS_ASR_MODELS`, `HUMANOS_PATHS_CONFIG`, `OPENROUTER_API_KEY`, `OPENROUTER_MODEL`
- **No hardcoded** machine paths in code.

## Architecture notes

- `TranscriptionBackend` + `FasterWhisperBackend` (M1)
- `CandidateRanker` + `OpenRouterCandidateRanker` (M2) — AI for comprehension/ranking only
- Deterministic post-steps in `pipeline/postprocess.py`
- Module at repo root `shorts_factory/` (not under `production_os/`)
- Does not import or modify editorial agents; OpenRouter client is local to this package

## Human evaluation (Buzz pilot)

When judging candidates on the Buzz / AI-agents source video, look for ideas such as: copying corporate org charts / bureaucracy; more agents ≠ more productivity; token usage / slowness; coordination/orchestration as the problem; “army of agents” vs a single agent. These themes are for **human QA only** — they are intentionally **not** hardcoded into the ranker.

## Tests

```bash
python -m unittest discover -s tests -p 'test_shorts_factory*.py'
```

ASR and LLM are mocked in unit tests (no GPU/API required). Optional smokes:

```bash
# M1
HUMANOS_SHORTS_SMOKE_VIDEO=/path/to/video.mp4 python -m unittest tests.test_shorts_factory_smoke

# M2 (needs OPENROUTER_API_KEY + transcript)
HUMANOS_SHORTS_SMOKE_TRANSCRIPT=/path/to/transcript.json \
  OPENROUTER_API_KEY=… \
  python -m unittest tests.test_shorts_factory_candidates_smoke
```
