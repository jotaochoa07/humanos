"""Shorts Factory — long video → transcript → candidates (+ later clips → 9:16).

Milestone 1: validate → audio → ASR → transcript.json + captions.srt.
Milestone 2: transcript.json → candidates.json (rank + deterministic post-steps).
Later: clip extract, reframe, burn-in, NLE packaging.
"""

__version__ = "0.2.0"

MILESTONE = 2
