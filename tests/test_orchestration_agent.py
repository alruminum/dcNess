"""test_orchestration_agent — sequence 동적 갱신 메타 LLM 검증.

Coverage:
    Step dataclass validation:
        - happy / invalid agent / unknown agent / empty enums / invalid mode

    parse_sequence_json:
        - happy / fenced ```json / invalid JSON / non-array
        - schema 위반 (agent 미허용 / mode 형식 / enum 형식)
        - 빈 리스트 (escalate 종결)

    decide_next_sequence:
        - mock client → JSON 응답 → list[Step]
        - decision_table_path 미존재 → FileNotFoundError
        - 빈 응답 → MissingSignal('ambiguous')
        - parse 실패 → MissingSignal('ambiguous') + telemetry outcome=parse_failed
        - DCNESS_LLM_TELEMETRY=0 → 기록 0
        - prompt 안에 결정표 + last_step 포함 (system/user 검사)
"""
from __future__ import annotations

import json
import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock

from harness.orchestration_agent import (
    ALLOWED_AGENTS,
    ESCALATE_ENUMS,
    Step,
    decide_next_sequence,
    parse_sequence_json,
)
from harness.signal_io import MissingSignal


class _FakeBlock:
    def __init__(self, text: str) -> None:
        self.type = "text"
        self.text = text


class _FakeUsage:
    def __init__(self, input_tokens: int = 10, output_tokens: int = 20) -> None:
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens


class _FakeResponse:
    def __init__(
        self,
        text: str,
        input_tokens: int = 10,
        output_tokens: int = 20,
    ) -> None:
        self.content = [_FakeBlock(text)]
        self.usage = _FakeUsage(input_tokens, output_tokens)


def _fake_client(response_text: str) -> MagicMock:
    client = MagicMock()
    client.messages = MagicMock()
    client.messages.create = MagicMock(return_value=_FakeResponse(response_text))
    return client


# ---------------------------------------------------------------------------
# Step dataclass
# ---------------------------------------------------------------------------


class StepValidationTests(unittest.TestCase):
    def test_happy_step(self) -> None:
        s = Step("validator", "PLAN_VALIDATION", ("PASS", "FAIL", "SPEC_MISSING"))
        self.assertEqual(s.agent, "validator")
        self.assertEqual(s.mode, "PLAN_VALIDATION")
        self.assertEqual(s.allowed_enums, ("PASS", "FAIL", "SPEC_MISSING"))

    def test_step_without_mode(self) -> None:
        s = Step("pr-reviewer", None, ("LGTM", "CHANGES_REQUESTED"))
        self.assertIsNone(s.mode)

    def test_step_normalizes_list_to_tuple(self) -> None:
        s = Step("engineer", "IMPL", ["IMPL_DONE", "TESTS_FAIL"])
        self.assertIsInstance(s.allowed_enums, tuple)

    def test_invalid_agent_format(self) -> None:
        with self.assertRaises(ValueError):
            Step("Validator", "PLAN_VALIDATION", ("PASS",))  # uppercase agent

    def test_unknown_agent_rejected(self) -> None:
        # signal_io agent regex 통과하지만 ALLOWED_AGENTS 미포함
        with self.assertRaises(ValueError):
            Step("foo-bar", None, ("OK",))

    def test_empty_allowed_enums(self) -> None:
        with self.assertRaises(ValueError):
            Step("validator", "PLAN_VALIDATION", ())

    def test_invalid_mode_format(self) -> None:
        with self.assertRaises(ValueError):
            Step("validator", "lower_case_mode", ("PASS",))

    def test_invalid_enum_format(self) -> None:
        with self.assertRaises(ValueError):
            Step("validator", "PLAN_VALIDATION", ("pass",))

    def test_to_dict_round_trip(self) -> None:
        s = Step("engineer", "IMPL", ("IMPL_DONE", "TESTS_FAIL"))
        d = s.to_dict()
        self.assertEqual(d["agent"], "engineer")
        self.assertEqual(d["mode"], "IMPL")
        self.assertEqual(d["allowed_enums"], ["IMPL_DONE", "TESTS_FAIL"])

    def test_all_allowed_agents_constructible(self) -> None:
        # 13 agent 정합 체크 (orchestration.md §4)
        for agent in ALLOWED_AGENTS:
            Step(agent, None, ("DUMMY_ENUM",))  # mode None 허용


# ---------------------------------------------------------------------------
# parse_sequence_json
# ---------------------------------------------------------------------------


class ParseSequenceJsonTests(unittest.TestCase):
    def test_happy_array(self) -> None:
        raw = json.dumps([
            {"agent": "validator", "mode": "PLAN_VALIDATION",
             "allowed_enums": ["PASS", "FAIL"]},
            {"agent": "engineer", "mode": "IMPL",
             "allowed_enums": ["IMPL_DONE"]},
        ])
        steps = parse_sequence_json(raw)
        self.assertEqual(len(steps), 2)
        self.assertEqual(steps[0].agent, "validator")
        self.assertEqual(steps[1].agent, "engineer")

    def test_fenced_json_stripped(self) -> None:
        raw = (
            "```json\n"
            '[{"agent": "qa", "mode": null, "allowed_enums": ["FUNCTIONAL_BUG"]}]\n'
            "```"
        )
        steps = parse_sequence_json(raw)
        self.assertEqual(len(steps), 1)
        self.assertEqual(steps[0].agent, "qa")

    def test_empty_array_returns_empty(self) -> None:
        self.assertEqual(parse_sequence_json("[]"), [])

    def test_invalid_json_ambiguous(self) -> None:
        with self.assertRaises(MissingSignal) as ctx:
            parse_sequence_json("not json")
        self.assertEqual(ctx.exception.reason, "ambiguous")

    def test_non_array_ambiguous(self) -> None:
        with self.assertRaises(MissingSignal):
            parse_sequence_json('{"agent": "validator"}')

    def test_step_object_required(self) -> None:
        with self.assertRaises(MissingSignal):
            parse_sequence_json('["not an object"]')

    def test_unknown_agent_ambiguous(self) -> None:
        raw = json.dumps([{"agent": "unknown-agent", "allowed_enums": ["X"]}])
        with self.assertRaises(MissingSignal):
            parse_sequence_json(raw)

    def test_invalid_mode_ambiguous(self) -> None:
        raw = json.dumps([
            {"agent": "validator", "mode": "lower", "allowed_enums": ["PASS"]},
        ])
        with self.assertRaises(MissingSignal):
            parse_sequence_json(raw)

    def test_empty_enums_ambiguous(self) -> None:
        raw = json.dumps([{"agent": "validator", "allowed_enums": []}])
        with self.assertRaises(MissingSignal):
            parse_sequence_json(raw)


# ---------------------------------------------------------------------------
# decide_next_sequence (mock client)
# ---------------------------------------------------------------------------


class DecideNextSequenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self._td = TemporaryDirectory()
        self.tmp = Path(self._td.name)
        self.decision_table = self.tmp / "orchestration.md"
        self.decision_table.write_text(
            "# Orchestration\n## 4. 결정표\n- validator PASS → engineer\n"
        )
        self.tele = self.tmp / "metrics"
        self.last_step = Step(
            "validator", "PLAN_VALIDATION", ("PASS", "FAIL", "SPEC_MISSING"),
        )

    def tearDown(self) -> None:
        self._td.cleanup()
        os.environ.pop("DCNESS_LLM_TELEMETRY", None)

    def test_happy_returns_parsed_sequence(self) -> None:
        response = json.dumps([
            {"agent": "engineer", "mode": "IMPL",
             "allowed_enums": ["IMPL_DONE", "TESTS_FAIL"]},
        ])
        client = _fake_client(response)
        result = decide_next_sequence(
            self.last_step,
            "PASS",
            "## 검증 결과\nPASS\n",
            remaining_sequence=[],
            decision_table_path=self.decision_table,
            client=client,
            telemetry_dir=self.tele,
        )
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].agent, "engineer")

        # client 호출 검증 — system 안에 결정표 포함, user 안에 last_step / parsed_enum 포함
        kwargs = client.messages.create.call_args.kwargs
        self.assertIn("결정표", kwargs["system"])
        self.assertIn("PLAN_VALIDATION", kwargs["messages"][0]["content"])
        self.assertIn("PASS", kwargs["messages"][0]["content"])

    def test_decision_table_missing_raises(self) -> None:
        client = _fake_client("[]")
        with self.assertRaises(FileNotFoundError):
            decide_next_sequence(
                self.last_step,
                "PASS",
                "p",
                remaining_sequence=[],
                decision_table_path=self.tmp / "missing.md",
                client=client,
            )

    def test_empty_response_ambiguous(self) -> None:
        client = _fake_client("")
        with self.assertRaises(MissingSignal):
            decide_next_sequence(
                self.last_step,
                "PASS",
                "p",
                remaining_sequence=[],
                decision_table_path=self.decision_table,
                client=client,
                telemetry_dir=self.tele,
            )

    def test_parse_failure_recorded_in_telemetry(self) -> None:
        client = _fake_client("not valid json")
        with self.assertRaises(MissingSignal):
            decide_next_sequence(
                self.last_step,
                "PASS",
                "p",
                remaining_sequence=[],
                decision_table_path=self.decision_table,
                client=client,
                telemetry_dir=self.tele,
            )
        log = (self.tele / "orchestration-calls.jsonl").read_text(encoding="utf-8")
        events = [json.loads(l) for l in log.strip().splitlines()]
        self.assertEqual(events[-1]["outcome"], "parse_failed")

    def test_telemetry_disabled_via_env(self) -> None:
        os.environ["DCNESS_LLM_TELEMETRY"] = "0"
        client = _fake_client("[]")
        result = decide_next_sequence(
            self.last_step,
            "PASS",
            "p",
            remaining_sequence=[],
            decision_table_path=self.decision_table,
            client=client,
            telemetry_dir=self.tele,
        )
        self.assertEqual(result, [])
        self.assertFalse((self.tele / "orchestration-calls.jsonl").exists())

    def test_empty_array_means_terminal(self) -> None:
        client = _fake_client("[]")
        result = decide_next_sequence(
            self.last_step,
            "IMPLEMENTATION_ESCALATE",
            "loop done",
            remaining_sequence=[],
            decision_table_path=self.decision_table,
            client=client,
            telemetry_dir=self.tele,
        )
        self.assertEqual(result, [])

    def test_telemetry_records_token_usage(self) -> None:
        client = _fake_client("[]")
        decide_next_sequence(
            self.last_step,
            "PASS",
            "p",
            remaining_sequence=[],
            decision_table_path=self.decision_table,
            client=client,
            telemetry_dir=self.tele,
        )
        log = (self.tele / "orchestration-calls.jsonl").read_text()
        event = json.loads(log.strip().splitlines()[-1])
        self.assertEqual(event["outcome"], "ok")
        self.assertEqual(event["last_agent"], "validator")
        self.assertEqual(event["last_enum"], "PASS")
        self.assertIn("input_tokens", event)
        self.assertIn("output_tokens", event)


class EscalateEnumsConstantTests(unittest.TestCase):
    def test_escalate_enums_match_orchestration_md_section_6(self) -> None:
        # orchestration.md §6 8 enum (직접 인용 정합)
        expected = {
            "IMPLEMENTATION_ESCALATE",
            "UX_FLOW_ESCALATE",
            "DESIGN_LOOP_ESCALATE",
            "SCOPE_ESCALATE",
            "PRODUCT_PLANNER_ESCALATION_NEEDED",
            "TECH_CONSTRAINT_CONFLICT",
            "UX_REDESIGN_SHORTLIST",
            "CLARITY_INSUFFICIENT",
        }
        self.assertEqual(set(ESCALATE_ENUMS), expected)


if __name__ == "__main__":
    unittest.main()
