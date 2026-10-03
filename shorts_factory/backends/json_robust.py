"""Robust JSON parsing helpers for truncated / messy LLM responses.

Does not change model or prompt — only post-parse recovery + retry signals.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Optional

logger = logging.getLogger(__name__)


def strip_code_fence(content: str) -> str:
    text = content.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


def _close_brackets(text: str) -> str:
    """Append missing } / ] closers based on a simple stack (strings ignored)."""
    stack: list[str] = []
    in_string = False
    escape = False
    for ch in text:
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch in "{[":
            stack.append("}" if ch == "{" else "]")
        elif ch in "}]":
            if stack and stack[-1] == ch:
                stack.pop()
    if in_string:
        text = text + '"'
        # recompute stack after closing string — cheap second pass
        return _close_brackets(text)
    return text + "".join(reversed(stack))


def _truncate_to_last_complete_candidate_array(text: str) -> Optional[str]:
    """If truncated inside candidates[], keep only complete objects and close JSON."""
    key_match = re.search(r'"candidates"\s*:\s*\[', text)
    if not key_match:
        return None
    array_start = key_match.end() - 1  # points at '['
    i = array_start + 1
    n = len(text)
    objects: list[str] = []
    while i < n:
        while i < n and text[i] in " \t\r\n,":
            i += 1
        if i >= n:
            break
        if text[i] == "]":
            break
        if text[i] != "{":
            # garbage / truncated mid-token
            break
        depth = 0
        in_string = False
        escape = False
        start = i
        complete = False
        while i < n:
            ch = text[i]
            if in_string:
                if escape:
                    escape = False
                elif ch == "\\":
                    escape = True
                elif ch == '"':
                    in_string = False
            else:
                if ch == '"':
                    in_string = True
                elif ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        objects.append(text[start : i + 1])
                        i += 1
                        complete = True
                        break
            i += 1
        if not complete:
            break

    if not objects:
        # empty array still valid
        prefix = text[: array_start + 1]
        repaired = prefix + "]"
        # close any outer object
        return _close_brackets(repaired)

    prefix = text[: array_start + 1]
    repaired = prefix + ",".join(objects) + "]"
    return _close_brackets(repaired)


def repair_truncated_json(text: str) -> Optional[dict[str, Any]]:
    """Best-effort repair of truncated JSON. Returns None if unsafe/unusable."""
    cleaned = strip_code_fence(text)
    if not cleaned:
        return None

    # Prefer truncating to complete candidate objects (avoids resurrecting
    # a half-written last object by naively closing quotes).
    attempts: list[str] = [cleaned]
    truncated = _truncate_to_last_complete_candidate_array(cleaned)
    if truncated:
        attempts.append(truncated)
    attempts.append(_close_brackets(cleaned))

    for attempt in attempts:
        try:
            data = json.loads(attempt)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict):
            return data
    return None


def loads_json_robust(content: str) -> dict[str, Any]:
    """Parse JSON content; on failure try safe repair; else raise JSONDecodeError."""
    cleaned = strip_code_fence(content)
    try:
        data = json.loads(cleaned)
        if isinstance(data, dict):
            return data
        raise ValueError("JSON root must be an object")
    except json.JSONDecodeError as exc:
        logger.warning("JSON parse failed (%s); attempting repair", exc)
        repaired = repair_truncated_json(cleaned)
        if repaired is not None:
            logger.info("Repaired truncated JSON successfully")
            return repaired
        raise
