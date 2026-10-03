# Shorts Factory (v0) — Milestones 1–3

Long horizontal video → timed transcript + SRT → ranked Shorts candidates → horizontal clips.

**Staging rule (Jota):**

1. **Done (M1):** `video → transcript.json + captions.srt`
2. **Done (M2):** `transcript → candidates.json` (editorial QA approved; see fixes below)
3. **This PR (M3):** `candidates → horizontal clips` (no reframe yet)
4. Later: `9:16 + captions burn-in + previews`

## Milestone 1 — closed QA decisions (2026-10-03)

- QA approved: UTF-8 SRT OK; faster-whisper **`small`** good enough for MVP.
- Known ASR errors on tech terms (e.g. "agentes de IA"→"agentes de ella", "un solo agente"→"un solo gente") — **do NOT bump to `medium`**.
- Keep **`small`** as the default model.
- Future optional iteration (**not M2/M3**): glossary / context prompt; post-processing of known terms; technical entity correction.

## Milestone 2 — editorial approval + required fixes

Jota approved M2 editorially (Buzz pilot human eval: **4 strong / 2 recoverable / 2 redundant**).

Required post-approval fixes (same ranking **model** and **prompt** — unchanged):

1. **Boundary refinement (`m2-v2`):** after ranking, avoid mid-sentence starts/ends. Expand by **at most 1 ASR segment** backward/forward when segment text heuristics say the cut is mid-thought / incomplete, and duration still fits the max window. Rules documented in `pipeline/postprocess.py`.
2. **OpenRouter JSON robustness:** truncated JSON (`Unterminated string`, etc.) → safe repair of complete candidate objects + re-request. See `backends/json_robust.py`.

## What each milestone does

| Stage | Input | Output |
|-------|--------|--------|
| M1 | video | `transcript.json`, `captions.srt` |
| M2 | `transcript.json` | `candidates.json` |
| M3 | `candidates.json` + source video | `01-<slug>/meta.json` + `clip_horizontal.mp4` |

## What is NOT implemented yet

- 9:16 reframe (center-crop) / face tracking / saliency
- Burn-in caption preview
- Glossary / ASR post-correction / medium model bump
- Remotion / DaVinci / CapCut packaging
- UI

## Timestamp grounding + boundary rules (`m2-v2`)

LLM timestamps are approximate. Pipeline re-grounds them:

1. Snap start/end to ASR segment boundaries  
2. Expand/trim whole segments to fit duration window  
3. **Boundary refine (±1 segment):**  
   - Start mid-sentence (lowercase / mid-thought cue like `y`, `pero`, `porque`…) → expand **one** segment back if ≤ max duration  
   - End without terminal punctuation (`.?!…`) → expand **one** segment forward if ≤ max duration  
4. Rebuild transcript text from the inclusive ASR span  
5. Duration filter → NMS by IoU → top N  

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

### `candidates.json` shape (M2/M3)

```json
{
  "source_video": "/abs/path/to/video.mp4",
  "generated_at": "2026-10-03T12:00:00+00:00",
  "milestone": 3,
  "ranker": "OpenRouterCandidateRanker",
  "snap_rules_version": "m2-v2",
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
      "segment_id_end": 20,
      "boundary_refined": true,
      "clip_horizontal": "01-example-slug/clip_horizontal.mp4"
    }
  ]
}
```

## Architecture notes

- `TranscriptionBackend` + `FasterWhisperBackend` (M1)
- `CandidateRanker` + `OpenRouterCandidateRanker` (M2) — AI for ranking only; **prompt/model locked** after editorial QA
- Deterministic post-steps: snap, boundary refine, NMS (`pipeline/postprocess.py`)
- M3: ffmpeg stream-copy cut only (`pipeline/extract_clips.py`) — no face tracking / 9:16
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
