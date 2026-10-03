"""Shorts Factory — long video → transcript → candidates → horizontal clips.

Milestone 1: validate → audio → ASR → transcript.json + captions.srt.
Milestone 2: transcript.json → candidates.json (rank + deterministic post-steps).
Milestone 3: candidates.json → per-candidate clip_horizontal.mp4 + meta.json.
Later: 9:16 reframe, burn-in, NLE packaging.
"""

__version__ = "0.3.0"

MILESTONE = 3
