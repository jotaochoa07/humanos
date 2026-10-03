"""Shared ASR-text heuristics for boundary refinement and scoring."""

from __future__ import annotations

import re

_TERMINAL_END_RE = re.compile(r'[.!?…]+["\'”’»)\]\}]*\s*$')
_OPEN_STRIP_RE = re.compile(r'^[\s"\'“”‘’¿¡(\[]+')

_MID_THOUGHT_STARTERS = frozenset(
    {
        "y",
        "e",
        "o",
        "u",
        "pero",
        "porque",
        "que",
        "sino",
        "aunque",
        "entonces",
        "ademas",
        "además",
        "tambien",
        "también",
        "luego",
        "asi",
        "así",
        "and",
        "but",
        "because",
        "so",
        "then",
        "which",
        "where",
        "when",
    }
)


def looks_like_sentence_end(text: str) -> bool:
    """True if *text* ends with terminal punctuation (complete thought)."""
    t = (text or "").strip()
    if not t:
        return False
    return bool(_TERMINAL_END_RE.search(t))


def looks_like_mid_sentence_start(text: str) -> bool:
    """True if *text* likely begins mid-thought (bad clip start)."""
    t = (text or "").strip()
    if not t:
        return True
    stripped = _OPEN_STRIP_RE.sub("", t)
    if not stripped:
        return True
    first = stripped[0]
    if first.isalpha() and first == first.lower() and first != first.upper():
        return True
    first_word = re.split(r"\s+", stripped, maxsplit=1)[0]
    first_word = re.sub(r"[^\wáéíóúñüÁÉÍÓÚÑÜ]+$", "", first_word, flags=re.UNICODE)
    if first_word.lower() in _MID_THOUGHT_STARTERS:
        return True
    return False
