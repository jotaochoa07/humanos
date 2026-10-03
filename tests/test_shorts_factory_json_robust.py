"""Unit tests for truncated OpenRouter JSON repair (no network)."""

from __future__ import annotations

import json
import unittest

from shorts_factory.backends.json_robust import loads_json_robust, repair_truncated_json
from shorts_factory.backends.openrouter_ranker import parse_ranker_payload


class TestJsonRobust(unittest.TestCase):
    def test_valid_json_passthrough(self):
        data = loads_json_robust('{"candidates":[{"start":1,"end":2,"score":0.5}]}')
        self.assertEqual(len(data["candidates"]), 1)

    def test_code_fence(self):
        raw = '```json\n{"candidates":[]}\n```'
        self.assertEqual(loads_json_robust(raw)["candidates"], [])

    def test_unterminated_string_repair_keeps_complete_objects(self):
        # Truncated mid-string on 2nd candidate
        truncated = (
            '{"candidates":['
            '{"start":10,"end":40,"hook":"ok","central_idea":"a",'
            '"selection_reason":"r","score":0.9,"suggested_title":"One"},'
            '{"start":50,"end":80,"hook":"cut mid str'
        )
        repaired = repair_truncated_json(truncated)
        self.assertIsNotNone(repaired)
        assert repaired is not None
        self.assertEqual(len(repaired["candidates"]), 1)
        cands = parse_ranker_payload(repaired)
        self.assertEqual(len(cands), 1)
        self.assertEqual(cands[0].suggested_title, "One")

    def test_loads_json_robust_raises_when_unusable(self):
        with self.assertRaises(json.JSONDecodeError):
            loads_json_robust("not-json-at-all{{{")


if __name__ == "__main__":
    unittest.main()
