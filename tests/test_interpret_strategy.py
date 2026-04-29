"""test_interpret_strategy — heuristic-only enum 추출 검증.

DCN-CHG-20260430-04: LLM fallback 폐기, heuristic-only 정착.

Coverage:
    - heuristic_hit             : 휴리스틱 단일 매칭
    - heuristic_ambiguous       : 휴리스틱 0/2+ hit → MissingSignal propagate
    - heuristic_not_found       : 휴리스틱이 not_found 예외 propagate
    - telemetry on/off          : DCNESS_LLM_TELEMETRY=0 시 기록 0
    - allowed empty             : 즉시 ValueError
"""
from __future__ import annotations

import json
import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from harness.interpret_strategy import (
    HEURISTIC_TELEMETRY_FILE,
    interpret_with_fallback,
)
from harness.signal_io import MissingSignal


class HeuristicHitTests(unittest.TestCase):
    def setUp(self) -> None:
        self._td = TemporaryDirectory()
        self.tele = Path(self._td.name)

    def tearDown(self) -> None:
        self._td.cleanup()

    def test_heuristic_hit_records_outcome(self) -> None:
        result = interpret_with_fallback(
            "## 결론\n\nPASS\n",
            ["PASS", "FAIL"],
            telemetry_dir=self.tele,
        )
        self.assertEqual(result, "PASS")

        log = (self.tele / HEURISTIC_TELEMETRY_FILE).read_text(encoding="utf-8")
        events = [json.loads(line) for line in log.strip().splitlines()]
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["outcome"], "heuristic_hit")
        self.assertEqual(events[0]["parsed"], "PASS")
        self.assertEqual(events[0]["allowed"], ["PASS", "FAIL"])


class HeuristicAmbiguousTests(unittest.TestCase):
    def setUp(self) -> None:
        self._td = TemporaryDirectory()
        self.tele = Path(self._td.name)

    def tearDown(self) -> None:
        self._td.cleanup()

    def test_ambiguous_propagates_missing_signal(self) -> None:
        with self.assertRaises(MissingSignal) as ctx:
            interpret_with_fallback(
                "no clear label here",
                ["PASS", "FAIL"],
                telemetry_dir=self.tele,
            )
        self.assertEqual(ctx.exception.reason, "ambiguous")

        events = [
            json.loads(line)
            for line in (self.tele / HEURISTIC_TELEMETRY_FILE)
            .read_text(encoding="utf-8")
            .strip()
            .splitlines()
        ]
        self.assertEqual(events[-1]["outcome"], "heuristic_ambiguous")

    def test_empty_prose_propagates_missing_signal(self) -> None:
        # 빈 prose 도 휴리스틱이 ambiguous (no enum found) 로 처리
        with self.assertRaises(MissingSignal):
            interpret_with_fallback(
                "",
                ["PASS", "FAIL"],
                telemetry_dir=self.tele,
            )


class TelemetryToggleTests(unittest.TestCase):
    def setUp(self) -> None:
        self._td = TemporaryDirectory()
        self.tele = Path(self._td.name)

    def tearDown(self) -> None:
        self._td.cleanup()
        os.environ.pop("DCNESS_LLM_TELEMETRY", None)

    def test_telemetry_disabled_via_env(self) -> None:
        os.environ["DCNESS_LLM_TELEMETRY"] = "0"
        interpret_with_fallback(
            "PASS",
            ["PASS"],
            telemetry_dir=self.tele,
        )
        self.assertFalse((self.tele / HEURISTIC_TELEMETRY_FILE).exists())


class ValidationTests(unittest.TestCase):
    def test_empty_allowed_raises(self) -> None:
        with self.assertRaises(ValueError):
            interpret_with_fallback("text", [])


if __name__ == "__main__":
    unittest.main()
