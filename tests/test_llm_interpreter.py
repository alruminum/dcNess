"""test_llm_interpreter — Anthropic haiku interpreter 검증.

테스트 전략:
    실제 SDK 호출은 절대 안 함. mock client 주입으로 round-trip 검증.
    - 정상 응답 → allowed enum 매칭
    - UNKNOWN 응답 → MissingSignal('ambiguous')
    - allowed 외 응답 → MissingSignal('ambiguous')
    - empty content → MissingSignal('ambiguous')
    - API 예외 → RuntimeError
    - telemetry 기록 검증 (DCNESS_LLM_TELEMETRY=1)
    - telemetry 비활성 검증 (DCNESS_LLM_TELEMETRY=0)
    - signal_io.interpret_signal 통합 (interpreter= 주입)

대 원칙 정합:
    - 형식 강제 0: 시스템 prompt 가 *권고* 형식 (allowed enum) — agent prose 자유 emit
    - 작업 영역: 외부 API 호출. 실 호출 안 하고 mock 검증.
"""
from __future__ import annotations

import json
import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock

from harness.llm_interpreter import (
    DEFAULT_MODEL,
    MAX_PROSE_TAIL_CHARS,
    make_haiku_interpreter,
)
from harness.signal_io import MissingSignal, interpret_signal


def _make_mock_response(text: str, input_tokens: int = 80, output_tokens: int = 5):
    """Anthropic SDK 응답 객체 흉내."""
    block = MagicMock()
    block.type = "text"
    block.text = text

    response = MagicMock()
    response.content = [block]

    usage = MagicMock()
    usage.input_tokens = input_tokens
    usage.output_tokens = output_tokens
    response.usage = usage

    return response


def _make_mock_client(text: str, **usage_kwargs):
    client = MagicMock()
    client.messages.create.return_value = _make_mock_response(text, **usage_kwargs)
    return client


class HappyPathTests(unittest.TestCase):
    def setUp(self) -> None:
        self._td = TemporaryDirectory()
        self.tele = Path(self._td.name)

    def tearDown(self) -> None:
        self._td.cleanup()

    def test_returns_matched_label(self) -> None:
        client = _make_mock_client("PASS")
        fn = make_haiku_interpreter(client=client, telemetry_dir=self.tele)
        result = fn("검증 결과 모두 통과", ["PASS", "FAIL", "SPEC_MISSING"])
        self.assertEqual(result, "PASS")

    def test_lowercase_response_normalized(self) -> None:
        client = _make_mock_client("fail")
        fn = make_haiku_interpreter(client=client, telemetry_dir=self.tele)
        result = fn("스펙 위반", ["PASS", "FAIL"])
        self.assertEqual(result, "FAIL")

    def test_extra_punctuation_stripped(self) -> None:
        client = _make_mock_client("PASS.")
        fn = make_haiku_interpreter(client=client, telemetry_dir=self.tele)
        result = fn("ok", ["PASS", "FAIL"])
        self.assertEqual(result, "PASS")

    def test_first_word_only(self) -> None:
        client = _make_mock_client("PASS — verification complete")
        fn = make_haiku_interpreter(client=client, telemetry_dir=self.tele)
        result = fn("ok", ["PASS", "FAIL"])
        self.assertEqual(result, "PASS")


class AmbiguousResponseTests(unittest.TestCase):
    def setUp(self) -> None:
        self._td = TemporaryDirectory()
        self.tele = Path(self._td.name)

    def tearDown(self) -> None:
        self._td.cleanup()

    def test_unknown_raises_ambiguous(self) -> None:
        client = _make_mock_client("UNKNOWN")
        fn = make_haiku_interpreter(client=client, telemetry_dir=self.tele)
        with self.assertRaises(MissingSignal) as ctx:
            fn("모호한 prose", ["PASS", "FAIL"])
        self.assertEqual(ctx.exception.reason, "ambiguous")

    def test_out_of_allowed_raises_ambiguous(self) -> None:
        client = _make_mock_client("MAYBE")
        fn = make_haiku_interpreter(client=client, telemetry_dir=self.tele)
        with self.assertRaises(MissingSignal) as ctx:
            fn("?", ["PASS", "FAIL"])
        self.assertEqual(ctx.exception.reason, "ambiguous")
        self.assertIn("MAYBE", str(ctx.exception))

    def test_empty_content_raises_ambiguous(self) -> None:
        client = _make_mock_client("")
        fn = make_haiku_interpreter(client=client, telemetry_dir=self.tele)
        with self.assertRaises(MissingSignal) as ctx:
            fn("?", ["PASS"])
        self.assertEqual(ctx.exception.reason, "ambiguous")


class ApiFailureTests(unittest.TestCase):
    def setUp(self) -> None:
        self._td = TemporaryDirectory()
        self.tele = Path(self._td.name)

    def tearDown(self) -> None:
        self._td.cleanup()

    def test_api_exception_wrapped_runtime_error(self) -> None:
        client = MagicMock()
        client.messages.create.side_effect = RuntimeError("rate limit")
        fn = make_haiku_interpreter(client=client, telemetry_dir=self.tele)
        with self.assertRaises(RuntimeError) as ctx:
            fn("text", ["PASS"])
        self.assertIn("Anthropic API 호출 실패", str(ctx.exception))


class ValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self._td = TemporaryDirectory()
        self.tele = Path(self._td.name)

    def tearDown(self) -> None:
        self._td.cleanup()

    def test_empty_allowed_raises(self) -> None:
        client = _make_mock_client("PASS")
        fn = make_haiku_interpreter(client=client, telemetry_dir=self.tele)
        with self.assertRaises(ValueError):
            fn("text", [])


class TelemetryTests(unittest.TestCase):
    def setUp(self) -> None:
        self._td = TemporaryDirectory()
        self.tele = Path(self._td.name)

    def tearDown(self) -> None:
        self._td.cleanup()
        os.environ.pop("DCNESS_LLM_TELEMETRY", None)

    def test_records_jsonl_event(self) -> None:
        client = _make_mock_client("PASS", input_tokens=120, output_tokens=2)
        fn = make_haiku_interpreter(client=client, telemetry_dir=self.tele)
        fn("text", ["PASS", "FAIL"])

        log_path = self.tele / "meta-llm-calls.jsonl"
        self.assertTrue(log_path.exists())

        lines = log_path.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 1)
        event = json.loads(lines[0])

        self.assertEqual(event["model"], DEFAULT_MODEL)
        self.assertEqual(event["allowed"], ["PASS", "FAIL"])
        self.assertEqual(event["parsed"], "PASS")
        self.assertEqual(event["input_tokens"], 120)
        self.assertEqual(event["output_tokens"], 2)
        # 비용 = 120 * 1e-6 + 2 * 5e-6 = 1.3e-4
        self.assertAlmostEqual(event["cost_usd"], 0.00013, places=6)

    def test_telemetry_disabled_via_env(self) -> None:
        os.environ["DCNESS_LLM_TELEMETRY"] = "0"
        client = _make_mock_client("PASS")
        fn = make_haiku_interpreter(client=client, telemetry_dir=self.tele)
        fn("text", ["PASS"])
        log_path = self.tele / "meta-llm-calls.jsonl"
        self.assertFalse(log_path.exists())

    def test_records_cost_for_ambiguous_too(self) -> None:
        # ambiguous 도 호출은 발생 → 비용 기록은 남아야 (proposal R8)
        client = _make_mock_client("UNKNOWN", input_tokens=80, output_tokens=2)
        fn = make_haiku_interpreter(client=client, telemetry_dir=self.tele)
        with self.assertRaises(MissingSignal):
            fn("text", ["PASS"])
        log_path = self.tele / "meta-llm-calls.jsonl"
        self.assertTrue(log_path.exists())


class SignalIoIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self._td = TemporaryDirectory()
        self.tele = Path(self._td.name)

    def tearDown(self) -> None:
        self._td.cleanup()

    def test_interpret_signal_uses_haiku_interpreter(self) -> None:
        client = _make_mock_client("PASS")
        fn = make_haiku_interpreter(client=client, telemetry_dir=self.tele)
        result = interpret_signal("자유 prose", ["PASS", "FAIL"], interpreter=fn)
        self.assertEqual(result, "PASS")

    def test_interpret_signal_propagates_ambiguous(self) -> None:
        client = _make_mock_client("UNKNOWN")
        fn = make_haiku_interpreter(client=client, telemetry_dir=self.tele)
        with self.assertRaises(MissingSignal):
            interpret_signal("자유 prose", ["PASS", "FAIL"], interpreter=fn)


class PromptConstructionTests(unittest.TestCase):
    def setUp(self) -> None:
        self._td = TemporaryDirectory()
        self.tele = Path(self._td.name)

    def tearDown(self) -> None:
        self._td.cleanup()

    def test_long_prose_truncated_to_tail(self) -> None:
        client = _make_mock_client("PASS")
        fn = make_haiku_interpreter(client=client, telemetry_dir=self.tele)
        long_prose = "X" * 50_000 + " conclusion: PASS"
        fn(long_prose, ["PASS"])

        # mock client.messages.create 호출 시 user content 검사
        call = client.messages.create.call_args
        user_content = call.kwargs["messages"][0]["content"]
        self.assertLessEqual(len(user_content), MAX_PROSE_TAIL_CHARS + 200)
        self.assertIn("conclusion: PASS", user_content)

    def test_system_prompt_lists_allowed(self) -> None:
        client = _make_mock_client("PASS")
        fn = make_haiku_interpreter(client=client, telemetry_dir=self.tele)
        fn("text", ["PASS", "FAIL", "SPEC_MISSING"])
        call = client.messages.create.call_args
        system = call.kwargs["system"]
        self.assertIn("PASS", system)
        self.assertIn("FAIL", system)
        self.assertIn("SPEC_MISSING", system)
        self.assertIn("UNKNOWN", system)


if __name__ == "__main__":
    unittest.main()
