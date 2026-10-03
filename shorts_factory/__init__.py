"""Shorts Factory — long video → transcript → span candidates → horizontal clips.

Milestone 1: validate → audio → ASR → transcript.json + captions.srt.
Milestone 2: transcript.json → candidates.json (m2-v4 semantic spans + scores).
Milestone 3: candidates.json spans → concat clip_horizontal.mp4 + meta.json.
Later (M4): 9:16 reframe, burn-in, NLE packaging — not started.
"""

__version__ = "0.4.0"

MILESTONE = 3
