# Shorts Factory (v0) — Milestones 1–3

Long horizontal video → timed transcript + SRT → ranked Shorts candidates → horizontal clips.

**Staging rule (Jota):**

1. **Done (M1):** `video → transcript.json + captions.srt`
2. **Done (M2 → m2-v4):** `transcript → candidates.json` as **self-contained narrative units** assembled with **1–3 semantic spans**
3. **Done (M3):** span concat → `clip_horizontal.mp4` (no reframe yet)
4. Later (M4): `9:16 + captions burn-in + previews` — **not started**

## Milestone 1 — closed QA decisions (2026-10-03)

- QA approved: UTF-8 SRT OK; faster-whisper **`small`** good enough for MVP.
- Known ASR errors on tech terms (e.g. "agentes de IA"→"agentes de ella", "un solo agente"→"un solo gente") — **do NOT bump to `medium`**.
- Keep **`small`** as the default model.
- Future optional iteration (**not M2/M3**): glossary / context prompt; post-processing of known terms; technical entity correction.

## Milestone 2 — editorial evolution (`m2-v3` → `m2-v4` spans)

**m2-v3:** each short must be a self-contained narrative unit (hook → context → idea → payoff) with score dimensions. Jota confirmed the criterion works, but expanding one continuous range to 80–90s is the wrong fix.

**m2-v4 (`snap_rules_version: m2-v4`):** semantic editing with **spans**.

### Span schema

```
role ∈ { hook, context, development, payoff }
```

- **1–3 spans** per short, original temporal order  
- **Gaps allowed** (cut filler; never invent/re-record speech)  
- If the unit already works continuously → **1 span** (`role: development`)  
- Prefer **30–60s total spoken** duration (`sum(span durations)`); hard max still 90s on the sum  
- Do **not** solve completeness by bloating one continuous window  

### Score dimensions (retained from m2-v3)

`hook_strength`, `context_completeness`, `conceptual_completeness`, `standalone_clarity`, `payoff_strength` + final `score` with heavy penalties (pronoun starts, incomplete payoff, prior-context dependency, observation without resolution, weaker duplicates). Soft penalty for oversized single continuous spans; bonus when multi-span cuts interstitial gaps.

Whisper stays **`small`**. Ranking prompt updated for multi-span assembly.

## What each milestone does

| Stage | Input | Output |
|-------|--------|--------|
| M1 | video | `transcript.json`, `captions.srt` |
| M2 | `transcript.json` | `candidates.json` + `candidates.m2-v4.json` |
| M3 | `candidates.json` (+ spans) | `01-<slug>/meta.json` + concat `clip_horizontal.mp4` |

## What is NOT implemented yet

- **M4:** 9:16 reframe / face tracking / burn-in captions
- Glossary / ASR post-correction / medium model bump
- Remotion / DaVinci / CapCut packaging
- UI

## Timestamp grounding (`m2-v4`)

1. Each span snaps independently to ASR boundaries (light ±1 sentence refine only)  
2. Overlaps from refine are trimmed (earlier span yields); gaps preserved  
3. `duration_sec` = **sum of span durations**; `start`/`end` = envelope  
4. Score dimensions + penalties → NMS / near-duplicate drop → top N  
5. M3 extracts each span then **ffmpeg concat** → one horizontal clip 

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

### `candidates.json` shape (m2-v4 / M3)

```json
{
  "snap_rules_version": "m2-v4",
  "config": {
    "duration_min_sec": 20,
    "duration_max_sec": 90,
    "preferred_duration_min_sec": 30,
    "preferred_duration_max_sec": 60,
    "target_count": 5,
    "max_spans": 3,
    "editorial_criteria": "self_contained_narrative_unit_spans"
  },
  "candidates": [
    {
      "id": "01-example-slug",
      "start": 45.2,
      "end": 120.0,
      "duration_sec": 52.0,
      "envelope_duration_sec": 74.8,
      "interstitial_gap_sec": 22.8,
      "span_count": 3,
      "spans": [
        {"role": "hook", "start": 45.2, "end": 58.0, "duration_sec": 12.8, "transcript": "..."},
        {"role": "development", "start": 70.0, "end": 95.0, "duration_sec": 25.0, "transcript": "..."},
        {"role": "payoff", "start": 105.0, "end": 120.0, "duration_sec": 15.0, "transcript": "..."}
      ],
      "hook": "...",
      "minimum_context": "...",
      "central_idea": "...",
      "idea_development": "...",
      "payoff": "...",
      "scores": {
        "hook_strength": 0.9,
        "context_completeness": 0.85,
        "conceptual_completeness": 0.88,
        "standalone_clarity": 0.9,
        "payoff_strength": 0.87
      },
      "score": 0.86,
      "clip_horizontal": "01-example-slug/clip_horizontal.mp4"
    }
  ]
}
```

### Re-run m2-v4 + clips (local)

```bash
humanos shorts candidates outputs/shorts_factory/<buzz-source>/
# → candidates.json + candidates.m2-v4.json (+ candidates.prev.json backup)

humanos shorts clips outputs/shorts_factory/<buzz-source>/
# Re-reads spans (or legacy start/end); concats → clip_horizontal.mp4 + meta.json
```

## Architecture notes

- `TranscriptionBackend` + `FasterWhisperBackend` (M1); Whisper default remains **`small`**
- `CandidateRanker` + `OpenRouterCandidateRanker` (M2) — prompt for **m2-v4 multi-span** assembly; OpenRouter model via env/config
- Span snap/validate: `pipeline/spans.py`; scores: `pipeline/scoring.py` (m2-v3 dimensions retained)
- M3: per-span cut + ffmpeg concat → one `clip_horizontal.mp4` — no face tracking / 9:16 / burn-in
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
