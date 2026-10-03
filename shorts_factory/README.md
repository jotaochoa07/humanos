# Shorts Factory (v0) — Milestones 1–3

Long horizontal video → timed transcript + SRT → ranked Shorts candidates → horizontal clips.

**Staging rule (Jota):**

1. **Done (M1):** `video → transcript.json + captions.srt`
2. **Done (M2 → m2-v3):** `transcript → candidates.json` as **self-contained narrative units**
3. **Done (M3):** `candidates → horizontal clips` (no reframe yet)
4. Later (M4): `9:16 + captions burn-in + previews` — **not started**

## Milestone 1 — closed QA decisions (2026-10-03)

- QA approved: UTF-8 SRT OK; faster-whisper **`small`** good enough for MVP.
- Known ASR errors on tech terms (e.g. "agentes de IA"→"agentes de ella", "un solo agente"→"un solo gente") — **do NOT bump to `medium`**.
- Keep **`small`** as the default model.
- Future optional iteration (**not M2/M3**): glossary / context prompt; post-processing of known terms; technical entity correction.

## Milestone 2 — editorial evolution (`m2-v3`)

Earlier M2 picked smart moments; several failed as **independent conceptual units**.

**m2-v3 rule:** each short must be understandable without the long video. A candidate must contain (explicitly or implicitly):

1. **Hook** — why keep watching  
2. **Minimum context** — what problem/situation  
3. **Idea / development** — what is being explained  
4. **Payoff / conclusion** — what the viewer takes away (the idea must close)

Output philosophy: **fewer clips, more self-contained** (default `--count` 5). Prefer a well-closed ~45–60s idea over an incomplete ~22s clip.

### Score dimensions (in `candidates.json`)

`hook_strength`, `context_completeness`, `conceptual_completeness`, `standalone_clarity`, `payoff_strength`, plus final `score` with heavy deterministic penalties for: pronoun/reference starts without context; ending before conclusion; depending on a prior sentence; observation without resolution; duplicating a better-resolved idea.

### Prior M2 notes

- Buzz human eval (pre-v3): **4 strong / 2 recoverable / 2 redundant** — approved with fixes, then criteria upgraded to m2-v3.
- `m2-v2` boundary ±1 segment + OpenRouter JSON robustness remain (v3 expands **multi-segment** within max duration).
- Whisper stays **`small`**. Ranking **prompt updated** for narrative units. OpenRouter model still via env/config override.

## What each milestone does

| Stage | Input | Output |
|-------|--------|--------|
| M1 | video | `transcript.json`, `captions.srt` |
| M2 | `transcript.json` | `candidates.json` + `candidates.m2-v3.json` |
| M3 | `candidates.json` + source video | `01-<slug>/meta.json` + `clip_horizontal.mp4` |

## What is NOT implemented yet

- **M4:** 9:16 reframe / face tracking / burn-in captions
- Glossary / ASR post-correction / medium model bump
- Remotion / DaVinci / CapCut packaging
- UI

## Timestamp grounding + narrative completion (`m2-v3`)

1. Snap start/end to ASR segment boundaries  
2. Expand/trim whole segments to fit hard duration window (20–90s)  
3. **Multi-segment narrative completion** (within max duration):  
   - Expand **backward** while start looks mid-sentence / pronoun-deictic / continuation  
   - Expand **forward** while end looks incomplete (no terminal punctuation / trailing connector)  
   - Soft prefer ~45–60s closed units (scoring bonus; hard cap still max)  
4. Rebuild transcript from inclusive ASR span; attach score dimensions + penalties  
5. Duration filter → sort by final score → NMS / near-duplicate idea drop → top N  

## Requirements

```bash
pip install -r requirements-shorts.txt
pip install -e .
```

- Python ≥ 3.10, system **ffmpeg** + **ffprobe**
- `OPENROUTER_API_KEY` for live M2 ranking (unit tests mock the ranker)

## How to run

### Full pipeline

```bash
# M1 + M2
humanos shorts path/to/long-video.mp4 --whisper-model small

# M1 + M2 + M3 clips
humanos shorts path/to/long-video.mp4 --with-clips
```

### Per milestone

```bash
humanos shorts candidates outputs/shorts_factory/<source_name>/
humanos shorts candidates --from-transcript …/transcript.json

# M3 — re-reads possibly hand-edited start/end from candidates.json
humanos shorts clips outputs/shorts_factory/<source_name>/
humanos shorts clips outputs/shorts_factory/<source_name>/ --video /path/to/source.mp4
```

### Useful flags

| Flag | Default | Notes |
|------|---------|--------|
| `--whisper-model` | `small` | Locked; do not bump for tech-term ASR typos |
| `--min-duration` / `--max-duration` | `20` / `90` | Candidate duration window |
| `--count` | `8` | Target candidates (aim 5–10) |
| `--overlap-iou` | `0.45` | NMS near-duplicate threshold |
| `--with-clips` | off | Continue to M3 after M2 |
| `--skip-candidates` | off | M1 only |
| `--force-transcribe` | off | Re-run ASR |

## Output layout

```
outputs/shorts_factory/<source_name>/
  transcript.json
  captions.srt
  audio.wav
  candidates.json
  01-<slug>/
    meta.json
    clip_horizontal.mp4
  02-<slug>/
    meta.json
    clip_horizontal.mp4
```

### `candidates.json` shape (m2-v3 / M3)

```json
{
  "source_video": "/abs/path/to/video.mp4",
  "generated_at": "2026-10-03T12:00:00+00:00",
  "milestone": 2,
  "ranker": "OpenRouterCandidateRanker",
  "snap_rules_version": "m2-v3",
  "config": {
    "duration_min_sec": 20,
    "duration_max_sec": 90,
    "preferred_duration_min_sec": 45,
    "preferred_duration_max_sec": 60,
    "target_count": 5,
    "overlap_iou_threshold": 0.45,
    "editorial_criteria": "self_contained_narrative_unit"
  },
  "candidates": [
    {
      "id": "01-example-slug",
      "start": 45.2,
      "end": 98.6,
      "duration_sec": 53.4,
      "transcript": "...",
      "hook": "...",
      "minimum_context": "...",
      "central_idea": "...",
      "idea_development": "...",
      "payoff": "...",
      "selection_reason": "...",
      "suggested_title": "...",
      "scores": {
        "hook_strength": 0.9,
        "context_completeness": 0.85,
        "conceptual_completeness": 0.88,
        "standalone_clarity": 0.9,
        "payoff_strength": 0.87
      },
      "score": 0.86,
      "score_penalty": 0.05,
      "penalty_reasons": [],
      "folder": "01-example-slug/",
      "segment_id_start": 12,
      "segment_id_end": 28,
      "boundary_refined": true,
      "expanded_start_segments": 2,
      "expanded_end_segments": 1,
      "clip_horizontal": "01-example-slug/clip_horizontal.mp4"
    }
  ]
}
```

### Re-run m2-v3 on an existing Buzz run (local)

```bash
humanos shorts candidates outputs/shorts_factory/<buzz-source>/
# Writes candidates.json + candidates.m2-v3.json
# Previous candidates.json backed up once → candidates.prev.json
```

## Architecture notes

- `TranscriptionBackend` + `FasterWhisperBackend` (M1); Whisper default remains **`small`**
- `CandidateRanker` + `OpenRouterCandidateRanker` (M2) — **prompt updated for m2-v3** narrative units; OpenRouter model via env/config
- Deterministic post-steps: multi-segment completion, score penalties, NMS (`pipeline/postprocess.py`, `pipeline/scoring.py`)
- M3: ffmpeg stream-copy cut only — no face tracking / 9:16
- Local OpenRouter client inside `shorts_factory/` (editorial agents untouched)

## Human evaluation (Buzz pilot)

Themes for human QA only (not hardcoded in the ranker): bureaucracy / org chart copying; more agents ≠ productivity; tokens / slowness; orchestration; army vs single agent.

## Tests

```bash
python -m unittest discover -s tests -p 'test_shorts_factory*.py'
```

ASR, LLM, and ffmpeg are mocked in unit tests. Optional smokes:

```bash
HUMANOS_SHORTS_SMOKE_VIDEO=/path/to/video.mp4 python -m unittest tests.test_shorts_factory_smoke
HUMANOS_SHORTS_SMOKE_TRANSCRIPT=/path/to/transcript.json OPENROUTER_API_KEY=… \
  python -m unittest tests.test_shorts_factory_candidates_smoke
```
