"""test_interpret_strategy — heuristic-first + LLM-fallback 합성 검증.

Coverage:
    - heuristic_hit                : 휴리스틱 단일 매칭, LLM 미호출
    - llm_fallback_hit             : 휴리스틱 ambiguous → LLM 호출 → 결론
    - llm_fallback_unknown         : LLM 도 ambiguous propagate
    - heuristic_ambiguous_no_fallback : LLM 미주입 + 휴리스틱 ambiguous
    - heuristic_not_found          : 휴리스틱이 not_found 예외 (raise without LLM)
    - telemetry on/off             : DCNESS_LLM_TELEMETRY=0 시 기록 0
    - llm_returns_invalid          : LLM contract 위반 시 ValueError
    - allowed empty                : 즉시 ValueError
"""
from __future__ import annotations

import json
import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock

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

    def test_heuristic_hits_skips_llm(self) -> None:
        llm = MagicMock()
        result = interpret_with_fallback(
            "## 결론\n\nPASS\n",
            ["PASS", "FAIL"],
            llm_interpreter=llm,
            telemetry_dir=self.tele,
        )
        self.assertEqual(result, "PASS")
        llm.assert_not_called()

        log = (self.tele / HEURISTIC_TELEMETRY_FILE).read_text(encoding="utf-8")
        events = [json.loads(l) for l in log.strip().splitlines()]
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["outcome"], "heuristic_hit")
        self.assertEqual(events[0]["parsed"], "PASS")
        self.assertEqual(events[0]["allowed"], ["PASS", "FAIL"])


class LlmFallbackTests(unittest.TestCase):
    def setUp(self) -> None:
        self._td = TemporaryDirectory()
        self.tele = Path(self._td.name)

    def tearDown(self) -> None:
        self._td.cleanup()

    def test_llm_fallback_when_heuristic_ambiguous(self) -> None:
        # 휴리스틱이 0 hit → ambiguous
        llm = MagicMock(return_value="FAIL")
        result = interpret_with_fallback(
            "결과: 모호함, 명확한 라벨 없음",
            ["PASS", "FAIL"],
            llm_interpreter=llm,
            telemetry_dir=self.tele,
        )
        self.assertEqual(result, "FAIL")
        llm.assert_called_once()

        events = [json.loads(l) for l in (self.tele / HEURISTIC_TELEMETRY_FILE).read_text().strip().splitlines()]
        self.assertEqual(events[-1]["outcome"], "llm_fallback_hit")
        self.assertEqual(events[-1]["parsed"], "FAIL")

    def test_llm_returns_ambiguous_propagates(self) -> None:
        def llm(prose, allowed):
            raise MissingSignal("ambiguous", "model returned UNKNOWN")
        with self.assertRaises(MissingSignal):
            interpret_with_fallback(
                "no clear label here",
                ["PASS", "FAIL"],
                llm_interpreter=llm,
                telemetry_dir=self.tele,
            )
        events = [json.loads(l) for l in (self.tele / HEURISTIC_TELEMETRY_FILE).read_text().strip().splitlines()]
        self.assertEqual(events[-1]["outcome"], "llm_fallback_unknown")

    def test_no_fallback_propagates_heuristic_ambiguous(self) -> None:
        with self.assertRaises(MissingSignal) as ctx:
            interpret_with_fallback(
                "no label",
                ["PASS", "FAIL"],
                llm_interpreter=None,
                telemetry_dir=self.tele,
            )
        self.assertEqual(ctx.exception.reason, "ambiguous")
        events = [json.loads(l) for l in (self.tele / HEURISTIC_TELEMETRY_FILE).read_text().strip().splitlines()]
        self.assertEqual(events[-1]["outcome"], "heuristic_ambiguous_no_fallback")

    def test_llm_returning_out_of_allowed_raises_value_error(self) -> None:
        # defensive — llm_interpreter contract 위반
        def llm(prose, allowed):
            return "MAYBE"
        with self.assertRaises(ValueError):
            interpret_with_fallback(
                "no label",
                ["PASS", "FAIL"],
                llm_interpreter=llm,
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
