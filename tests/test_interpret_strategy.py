"""test_interpret_strategy — issue #284 폐기 진행: telemetry 중단 검증.

이슈 #280 epic 정착 후 동작:
    - `interpret_with_fallback` 휴리스틱 자체는 legacy 호환 (외부 skill `--allowed-enums`).
    - 단 `.metrics/heuristic-calls.jsonl` 에 신규 append 0.
    - prose-only routing telemetry 는 `harness/routing_telemetry.py` 가 대체 (#281).

Coverage:
    - heuristic 결과 자체는 legacy 호환 (PASS / AMBIGUOUS / not_found 동일).
    - 모든 outcome 에서 heuristic-calls.jsonl 신규 기록 0 (이슈 #284 acceptance).
    - allowed empty → ValueError.
"""
from __future__ import annotations

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

    def test_heuristic_hit_returns_enum(self) -> None:
        result = interpret_with_fallback(
            "## 결론\n\nPASS\n",
            ["PASS", "FAIL"],
            telemetry_dir=self.tele,
        )
        self.assertEqual(result, "PASS")

    def test_no_heuristic_calls_jsonl_written(self) -> None:
        # 이슈 #284 acceptance — 어떤 outcome 에서도 신규 기록 0.
        interpret_with_fallback("PASS", ["PASS"], telemetry_dir=self.tele)
        try:
            interpret_with_fallback(
                "no enum here", ["PASS", "FAIL"], telemetry_dir=self.tele,
            )
        except MissingSignal:
            pass
        self.assertFalse((self.tele / HEURISTIC_TELEMETRY_FILE).exists())


class HeuristicAmbiguousTests(unittest.TestCase):
    def test_ambiguous_propagates_missing_signal(self) -> None:
        with self.assertRaises(MissingSignal) as ctx:
            interpret_with_fallback(
                "no clear label here",
                ["PASS", "FAIL"],
            )
        self.assertEqual(ctx.exception.reason, "ambiguous")

    def test_empty_prose_propagates_missing_signal(self) -> None:
        with self.assertRaises(MissingSignal):
            interpret_with_fallback("", ["PASS", "FAIL"])


class ValidationTests(unittest.TestCase):
    def test_empty_allowed_raises(self) -> None:
        with self.assertRaises(ValueError):
            interpret_with_fallback("text", [])


if __name__ == "__main__":
    unittest.main()
