"""test_routing_telemetry — issue #281 prose-only routing 측정 인프라.

Coverage:
    - record_agent_call: agent_call 1줄 append, prose tail-cap, 권장 필드.
    - record_cascade: cascade 1줄 append, reason 보존.
    - DCNESS_LLM_TELEMETRY=0 → 기록 0.
    - 잘못된 sub silent skip (hook 본 흐름 보호).
    - CLI: record-cascade subcommand JSONL 기록.
    - 다회 호출 시 jsonl append (덮어쓰기 X).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from harness.routing_telemetry import (
    ROUTING_TELEMETRY_FILE,
    record_agent_call,
    record_cascade,
)


class _Base(unittest.TestCase):
    def setUp(self) -> None:
        self._td = TemporaryDirectory()
        self.tele = Path(self._td.name)
        self.path = self.tele / ROUTING_TELEMETRY_FILE
        # telemetry 활성 — 외부 환경 무관 보장
        os.environ.pop("DCNESS_LLM_TELEMETRY", None)

    def tearDown(self) -> None:
        os.environ.pop("DCNESS_LLM_TELEMETRY", None)
        self._td.cleanup()

    def _read_events(self) -> list:
        if not self.path.exists():
            return []
        return [
            json.loads(line)
            for line in self.path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]


class RecordAgentCallTests(_Base):
    def test_records_event_with_required_fields(self) -> None:
        record_agent_call(
            sub="engineer",
            prose="## 결론\n\nIMPL_DONE — 수용 기준 통과\n",
            mode="IMPL",
            tool_use_id="toolu_abc",
            run_id="20260508-r1",
            session_id="sid_xy",
            base_dir=self.tele,
        )
        events = self._read_events()
        self.assertEqual(len(events), 1)
        e = events[0]
        self.assertEqual(e["event"], "agent_call")
        self.assertEqual(e["sub"], "engineer")
        self.assertEqual(e["mode"], "IMPL")
        self.assertEqual(e["tool_use_id"], "toolu_abc")
        self.assertEqual(e["run_id"], "20260508-r1")
        self.assertEqual(e["session_id"], "sid_xy")
        self.assertIn("IMPL_DONE", e["prose_tail"])
        self.assertIn("ts", e)

    def test_prose_tail_capped_at_1200(self) -> None:
        long = "x" * 5000 + "\n결론: PASS\n"
        record_agent_call(sub="pr-reviewer", prose=long, base_dir=self.tele)
        events = self._read_events()
        self.assertEqual(len(events), 1)
        # 마지막 1200 자만 보존 — 결론 부분이 포함됨
        self.assertLessEqual(len(events[0]["prose_tail"]), 1200)
        self.assertIn("결론: PASS", events[0]["prose_tail"])
        self.assertEqual(events[0]["prose_len"], len(long))

    def test_blank_sub_silent_skip(self) -> None:
        record_agent_call(sub="", prose="anything", base_dir=self.tele)
        record_agent_call(sub="   ", prose="anything", base_dir=self.tele)
        self.assertFalse(self.path.exists())

    def test_multiple_appends_jsonl(self) -> None:
        for i in range(3):
            record_agent_call(
                sub="engineer", prose=f"step{i}", base_dir=self.tele,
            )
        events = self._read_events()
        self.assertEqual(len(events), 3)


class RecordCascadeTests(_Base):
    def test_records_cascade_with_reason(self) -> None:
        record_cascade(
            "메인이 architect vs engineer 결정 못 함",
            sub="qa",
            mode="QA",
            run_id="r1",
            session_id="s1",
            base_dir=self.tele,
        )
        events = self._read_events()
        self.assertEqual(len(events), 1)
        e = events[0]
        self.assertEqual(e["event"], "cascade")
        self.assertEqual(e["sub"], "qa")
        self.assertEqual(e["mode"], "QA")
        self.assertEqual(e["reason"], "메인이 architect vs engineer 결정 못 함")
        self.assertIn("ts", e)

    def test_long_reason_capped_at_500(self) -> None:
        record_cascade("x" * 5000, base_dir=self.tele)
        events = self._read_events()
        self.assertEqual(len(events[0]["reason"]), 500)


class TelemetryToggleTests(_Base):
    def test_disabled_via_env(self) -> None:
        os.environ["DCNESS_LLM_TELEMETRY"] = "0"
        record_agent_call(sub="engineer", prose="x", base_dir=self.tele)
        record_cascade("y", base_dir=self.tele)
        self.assertFalse(self.path.exists())


class CliTests(_Base):
    def test_cli_record_cascade_appends(self) -> None:
        # 모듈을 subprocess 로 실행 — argparse 통합 점검
        env = {**os.environ, "PYTHONPATH": str(Path.cwd())}
        result = subprocess.run(
            [
                sys.executable, "-m", "harness.routing_telemetry",
                "record-cascade",
                "--reason", "사용자에게 위임",
                "--sub", "architect",
                "--mode", "MODULE_PLAN",
                "--base-dir", str(self.tele),
            ],
            capture_output=True,
            text=True,
            env=env,
            cwd=str(Path.cwd()),
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        events = self._read_events()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["event"], "cascade")
        self.assertEqual(events[0]["sub"], "architect")
        self.assertEqual(events[0]["mode"], "MODULE_PLAN")
        self.assertIn("위임", events[0]["reason"])


class WorktreeNormalizationTests(unittest.TestCase):
    """worktree 안 cwd → main repo root 정규화 (#306 개선점 5).

    base_dir 미지정 시 _telemetry_path 가 main repo root 기준 `.metrics/` 사용.
    ExitWorktree(remove) 후 누적분 손실 회피.
    """

    def test_default_path_uses_main_repo_root_when_in_worktree(self):
        from unittest.mock import patch
        from harness.routing_telemetry import _telemetry_path
        with TemporaryDirectory() as td:
            main_root = Path(td) / "main"
            worktree = main_root / ".claude" / "worktrees" / "wt1"
            main_root.mkdir(parents=True)
            worktree.mkdir(parents=True)
            with patch("pathlib.Path.cwd", return_value=worktree), \
                 patch(
                     "harness.session_state._resolve_project_root",
                     return_value=main_root,
                 ):
                p = _telemetry_path(None)
            self.assertTrue(
                str(p).startswith(str(main_root.resolve()) + os.sep),
                f"telemetry_path={p} 가 main_root={main_root} 안이 아님",
            )
            self.assertNotIn("worktrees/wt1", str(p))
            self.assertIn(".metrics", str(p))
            self.assertIn(ROUTING_TELEMETRY_FILE, str(p))

    def test_explicit_base_dir_overrides(self):
        """base_dir 명시 시 그대로 사용 (worktree 정규화 skip)."""
        from harness.routing_telemetry import _telemetry_path
        with TemporaryDirectory() as td:
            explicit = Path(td) / "custom-metrics"
            p = _telemetry_path(explicit)
            self.assertEqual(p.parent, explicit)
            self.assertEqual(p.name, ROUTING_TELEMETRY_FILE)


if __name__ == "__main__":
    unittest.main()
