"""test_hooks — Claude Code 훅 핸들러 검증 (`harness/hooks.py`).

Coverage matrix:
    handle_session_start:
        - 정상 sid 추출 + by-pid 작성 + live.json 초기화
        - 잘못된 sid → silent skip (return 0)
        - cc_pid invalid → silent skip
        - 빈 stdin → silent skip
        - 기존 live.json 보존 (재호출 안전)

    handle_pretooluse_agent:
        - HARNESS_ONLY_AGENTS — run 없으면 차단
        - HARNESS_ONLY_AGENTS — run 있으면 추가 검사
        - §2.3.1 — pr-reviewer 직전 CODE_VALIDATION 없으면 차단
        - §2.3.1 — engineer 변경 후 CODE_VALIDATION PASS 있으면 통과
        - §2.3.1 — BUGFIX_VALIDATION PASS 도 인정
        - §2.3.3 — engineer 직전 plan READY 없으면 차단
        - §2.3.3 — MODULE_PLAN READY_FOR_IMPL 있으면 통과
        - §2.3.3 — LIGHT_PLAN_READY 있으면 통과 (light path)
        - §2.3.3 — engineer POLISH 모드는 plan 검사 skip
        - §2.3.4 — PRD 변경 후 plan-reviewer 없으면 차단
        - §2.3.4 — ux-architect READY 없으면 차단
        - §2.3.4 — 둘 다 있으면 통과
        - 그 외 agent (architect MODULE_PLAN, qa 등) — run 외부에서도 통과
        - sid 없음 → silent allow
        - tool_input 비정상 → silent allow

    rid 결정:
        - by-pid-current-run 우선
        - 폴백: live.json 의 가장 최근 미완료 슬롯
        - 둘 다 없음 → ""
"""
from __future__ import annotations

import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from harness.hooks import (
    HARNESS_ONLY_AGENTS,
    handle_pretooluse_agent,
    handle_session_start,
)
from harness.session_state import (
    read_live,
    read_pid_session,
    run_dir,
    session_dir,
    start_run,
    update_live,
    write_pid_current_run,
    write_pid_session,
)


# ---------------------------------------------------------------------------
# handle_session_start
# ---------------------------------------------------------------------------


class HandleSessionStartTests(unittest.TestCase):
    def setUp(self) -> None:
        self._td = TemporaryDirectory()
        self.base = Path(self._td.name)

    def tearDown(self) -> None:
        self._td.cleanup()

    def test_happy_creates_by_pid_and_live(self) -> None:
        rc = handle_session_start(
            stdin_data={"sessionId": "abc-sid"},
            cc_pid=12345,
            base_dir=self.base,
        )
        self.assertEqual(rc, 0)
        self.assertEqual(read_pid_session(12345, base_dir=self.base), "abc-sid")
        live = read_live("abc-sid", base_dir=self.base)
        self.assertEqual(live["session_id"], "abc-sid")
        self.assertEqual(live["active_runs"], {})

    def test_session_id_3_variants(self) -> None:
        for key in ("session_id", "sessionId", "sessionid"):
            with TemporaryDirectory() as td:
                base = Path(td)
                rc = handle_session_start(
                    stdin_data={key: "test-sid"},
                    cc_pid=12345,
                    base_dir=base,
                )
                self.assertEqual(rc, 0)
                self.assertEqual(read_pid_session(12345, base_dir=base), "test-sid")

    def test_invalid_sid_silent(self) -> None:
        rc = handle_session_start(
            stdin_data={"sessionId": "../bad"},
            cc_pid=12345,
            base_dir=self.base,
        )
        self.assertEqual(rc, 0)
        # 아무것도 안 만들어짐
        self.assertFalse((self.base / ".by-pid" / "12345").exists())

    def test_missing_cc_pid_silent(self) -> None:
        rc = handle_session_start(
            stdin_data={"sessionId": "abc-sid"},
            cc_pid=None,
            base_dir=self.base,
        )
        self.assertEqual(rc, 0)
        self.assertFalse((self.base / ".by-pid").exists())

    def test_invalid_cc_pid_silent(self) -> None:
        rc = handle_session_start(
            stdin_data={"sessionId": "abc-sid"},
            cc_pid=0,
            base_dir=self.base,
        )
        self.assertEqual(rc, 0)

    def test_empty_payload_silent(self) -> None:
        rc = handle_session_start(stdin_data={}, cc_pid=12345, base_dir=self.base)
        self.assertEqual(rc, 0)

    def test_idempotent_preserves_live(self) -> None:
        # 1차 호출 + start_run
        handle_session_start(
            stdin_data={"sessionId": "abc-sid"},
            cc_pid=12345,
            base_dir=self.base,
        )
        start_run("abc-sid", "run-aaaaaaaa", "test", base_dir=self.base)
        # 2차 호출 — 기존 active_runs 보존되어야 함
        handle_session_start(
            stdin_data={"sessionId": "abc-sid"},
            cc_pid=12345,
            base_dir=self.base,
        )
        live = read_live("abc-sid", base_dir=self.base)
        self.assertIn("run-aaaaaaaa", live.get("active_runs", {}))


# ---------------------------------------------------------------------------
# handle_pretooluse_agent — base setup
# ---------------------------------------------------------------------------


class _PreToolBase(unittest.TestCase):
    sid = "test-sid"
    rid = "run-12345678"
    cc_pid = 99999

    def setUp(self) -> None:
        self._td = TemporaryDirectory()
        self.base = Path(self._td.name)
        # 기본 setup — session + run 활성
        write_pid_session(self.cc_pid, self.sid, base_dir=self.base)
        update_live(self.sid, base_dir=self.base)
        start_run(self.sid, self.rid, "test", base_dir=self.base)
        write_pid_current_run(self.cc_pid, self.rid, base_dir=self.base)
        self.run_path = run_dir(self.sid, self.rid, base_dir=self.base)

    def tearDown(self) -> None:
        self._td.cleanup()

    def _payload(self, subagent: str, mode: str = "") -> dict:
        return {
            "sessionId": self.sid,
            "tool_input": {
                "subagent_type": subagent,
                "mode": mode,
            },
        }


# ---------------------------------------------------------------------------
# HARNESS_ONLY_AGENTS
# ---------------------------------------------------------------------------


class HarnessOnlyAgentsTests(_PreToolBase):
    def test_constant_matches_spec(self) -> None:
        # orchestration.md §7.1 정합 확인
        self.assertIn(("engineer", None), HARNESS_ONLY_AGENTS)
        self.assertIn(("validator", "PLAN_VALIDATION"), HARNESS_ONLY_AGENTS)
        self.assertIn(("validator", "CODE_VALIDATION"), HARNESS_ONLY_AGENTS)
        self.assertIn(("validator", "BUGFIX_VALIDATION"), HARNESS_ONLY_AGENTS)

    def test_engineer_blocked_without_run(self) -> None:
        # 새 base — run 없음
        with TemporaryDirectory() as td:
            base = Path(td)
            update_live(self.sid, base_dir=base)  # live 만 있고 run 없음
            rc = handle_pretooluse_agent(
                stdin_data=self._payload("engineer", "IMPL"),
                cc_pid=88888,  # run 없는 cc_pid
                base_dir=base,
            )
            self.assertEqual(rc, 1)

    def test_validator_plan_blocked_without_run(self) -> None:
        with TemporaryDirectory() as td:
            base = Path(td)
            update_live(self.sid, base_dir=base)
            rc = handle_pretooluse_agent(
                stdin_data=self._payload("validator", "PLAN_VALIDATION"),
                cc_pid=88888,
                base_dir=base,
            )
            self.assertEqual(rc, 1)

    def test_non_harness_only_agent_allowed_without_run(self) -> None:
        with TemporaryDirectory() as td:
            base = Path(td)
            update_live(self.sid, base_dir=base)
            rc = handle_pretooluse_agent(
                stdin_data=self._payload("qa", ""),
                cc_pid=88888,
                base_dir=base,
            )
            self.assertEqual(rc, 0)


# ---------------------------------------------------------------------------
# §2.3.3 — engineer 직전 plan READY 검사
# ---------------------------------------------------------------------------


class CatastrophicEngineerTests(_PreToolBase):
    def test_blocked_without_plan(self) -> None:
        rc = handle_pretooluse_agent(
            stdin_data=self._payload("engineer", "IMPL"),
            cc_pid=self.cc_pid,
            base_dir=self.base,
        )
        self.assertEqual(rc, 1)

    def test_allowed_with_module_plan_ready(self) -> None:
        (self.run_path / "architect-MODULE_PLAN.md").write_text(
            "## 계획\n...\n## 결론\nREADY_FOR_IMPL\n", encoding="utf-8",
        )
        rc = handle_pretooluse_agent(
            stdin_data=self._payload("engineer", "IMPL"),
            cc_pid=self.cc_pid,
            base_dir=self.base,
        )
        self.assertEqual(rc, 0)

    def test_allowed_with_light_plan_ready(self) -> None:
        (self.run_path / "architect-LIGHT_PLAN.md").write_text(
            "LIGHT_PLAN_READY", encoding="utf-8",
        )
        rc = handle_pretooluse_agent(
            stdin_data=self._payload("engineer", "IMPL"),
            cc_pid=self.cc_pid,
            base_dir=self.base,
        )
        self.assertEqual(rc, 0)

    def test_polish_mode_skips_plan_check(self) -> None:
        rc = handle_pretooluse_agent(
            stdin_data=self._payload("engineer", "POLISH"),
            cc_pid=self.cc_pid,
            base_dir=self.base,
        )
        self.assertEqual(rc, 0)


# ---------------------------------------------------------------------------
# §2.3.1 — pr-reviewer 직전 validator PASS 검사
# ---------------------------------------------------------------------------


class CatastrophicPrReviewerTests(_PreToolBase):
    def test_no_engineer_write_allows(self) -> None:
        # engineer 호출 흔적 없으면 통과
        rc = handle_pretooluse_agent(
            stdin_data=self._payload("pr-reviewer", ""),
            cc_pid=self.cc_pid,
            base_dir=self.base,
        )
        self.assertEqual(rc, 0)

    def test_engineer_write_without_validator_blocks(self) -> None:
        (self.run_path / "engineer-IMPL.md").write_text("IMPL_DONE", encoding="utf-8")
        rc = handle_pretooluse_agent(
            stdin_data=self._payload("pr-reviewer", ""),
            cc_pid=self.cc_pid,
            base_dir=self.base,
        )
        self.assertEqual(rc, 1)

    def test_engineer_write_with_code_validation_pass_allows(self) -> None:
        (self.run_path / "engineer-IMPL.md").write_text("IMPL_DONE", encoding="utf-8")
        (self.run_path / "validator-CODE_VALIDATION.md").write_text(
            "PASS", encoding="utf-8",
        )
        rc = handle_pretooluse_agent(
            stdin_data=self._payload("pr-reviewer", ""),
            cc_pid=self.cc_pid,
            base_dir=self.base,
        )
        self.assertEqual(rc, 0)

    def test_engineer_write_with_bugfix_validation_pass_allows(self) -> None:
        (self.run_path / "engineer-IMPL.md").write_text("IMPL_DONE", encoding="utf-8")
        (self.run_path / "validator-BUGFIX_VALIDATION.md").write_text(
            "PASS", encoding="utf-8",
        )
        rc = handle_pretooluse_agent(
            stdin_data=self._payload("pr-reviewer", ""),
            cc_pid=self.cc_pid,
            base_dir=self.base,
        )
        self.assertEqual(rc, 0)


# ---------------------------------------------------------------------------
# §2.3.4 — architect SD/TD 직전 PRD 변경 후 검토 검사
# ---------------------------------------------------------------------------


class CatastrophicArchitectTests(_PreToolBase):
    def test_no_prd_change_allows(self) -> None:
        rc = handle_pretooluse_agent(
            stdin_data=self._payload("architect", "SYSTEM_DESIGN"),
            cc_pid=self.cc_pid,
            base_dir=self.base,
        )
        self.assertEqual(rc, 0)

    def test_prd_change_without_review_blocks(self) -> None:
        (self.run_path / "product-planner.md").write_text(
            "PRODUCT_PLAN_READY", encoding="utf-8",
        )
        rc = handle_pretooluse_agent(
            stdin_data=self._payload("architect", "SYSTEM_DESIGN"),
            cc_pid=self.cc_pid,
            base_dir=self.base,
        )
        self.assertEqual(rc, 1)

    def test_prd_change_with_plan_review_no_ux_blocks(self) -> None:
        (self.run_path / "product-planner.md").write_text(
            "PRODUCT_PLAN_READY", encoding="utf-8",
        )
        (self.run_path / "plan-reviewer.md").write_text(
            "PLAN_REVIEW_PASS", encoding="utf-8",
        )
        rc = handle_pretooluse_agent(
            stdin_data=self._payload("architect", "SYSTEM_DESIGN"),
            cc_pid=self.cc_pid,
            base_dir=self.base,
        )
        self.assertEqual(rc, 1)

    def test_prd_change_full_review_allows(self) -> None:
        (self.run_path / "product-planner.md").write_text(
            "PRODUCT_PLAN_READY", encoding="utf-8",
        )
        (self.run_path / "plan-reviewer.md").write_text(
            "PLAN_REVIEW_PASS", encoding="utf-8",
        )
        (self.run_path / "ux-architect.md").write_text(
            "UX_FLOW_READY", encoding="utf-8",
        )
        rc = handle_pretooluse_agent(
            stdin_data=self._payload("architect", "SYSTEM_DESIGN"),
            cc_pid=self.cc_pid,
            base_dir=self.base,
        )
        self.assertEqual(rc, 0)

    def test_architect_module_plan_skips_prd_check(self) -> None:
        # MODULE_PLAN 은 §2.3.4 미적용
        (self.run_path / "product-planner.md").write_text(
            "PRODUCT_PLAN_READY", encoding="utf-8",
        )
        rc = handle_pretooluse_agent(
            stdin_data=self._payload("architect", "MODULE_PLAN"),
            cc_pid=self.cc_pid,
            base_dir=self.base,
        )
        self.assertEqual(rc, 0)


# ---------------------------------------------------------------------------
# rid 폴백 (by-pid-current-run 없을 때 live.json 에서 추정)
# ---------------------------------------------------------------------------


class RidResolutionTests(unittest.TestCase):
    def setUp(self) -> None:
        self._td = TemporaryDirectory()
        self.base = Path(self._td.name)
        self.sid = "test-sid"
        update_live(self.sid, base_dir=self.base)

    def tearDown(self) -> None:
        self._td.cleanup()

    def test_falls_back_to_most_recent_uncompleted(self) -> None:
        # 두 run 존재. by-pid-current-run 없음.
        start_run(self.sid, "run-aaaaaaaa", "older", base_dir=self.base)
        # 약간 기다리지 않아도 ISO 같은 sec 단위 — 둘 다 같은 ts 가능
        # 강제로 서로 다른 ts 박기
        from harness.session_state import read_live as _rl
        live = _rl(self.sid, base_dir=self.base) or {}
        active = live.get("active_runs", {}) or {}
        if "run-aaaaaaaa" in active:
            active["run-aaaaaaaa"]["started_at"] = "2026-04-29T11:00:00+00:00"
        update_live(self.sid, base_dir=self.base, active_runs=active)
        start_run(self.sid, "run-bbbbbbbb", "newer", base_dir=self.base)
        live = _rl(self.sid, base_dir=self.base) or {}
        active = live.get("active_runs", {}) or {}
        active["run-bbbbbbbb"]["started_at"] = "2026-04-29T12:00:00+00:00"
        update_live(self.sid, base_dir=self.base, active_runs=active)

        rd_b = run_dir(self.sid, "run-bbbbbbbb", base_dir=self.base)
        # newer 의 run_dir 에 plan READY 박음
        rd_b.mkdir(parents=True, exist_ok=True)
        (rd_b / "architect-MODULE_PLAN.md").write_text(
            "READY_FOR_IMPL", encoding="utf-8",
        )

        # by-pid 없이 호출 → live.json 의 newer 슬롯 선택 → READY 있어 통과
        rc = handle_pretooluse_agent(
            stdin_data={
                "sessionId": self.sid,
                "tool_input": {"subagent_type": "engineer", "mode": "IMPL"},
            },
            cc_pid=None,
            base_dir=self.base,
        )
        self.assertEqual(rc, 0)


# ---------------------------------------------------------------------------
# 비정상 입력 — silent allow
# ---------------------------------------------------------------------------


class SilentAllowTests(_PreToolBase):
    def test_no_session_id_silent(self) -> None:
        rc = handle_pretooluse_agent(
            stdin_data={"tool_input": {"subagent_type": "engineer", "mode": "IMPL"}},
            cc_pid=self.cc_pid,
            base_dir=self.base,
        )
        self.assertEqual(rc, 0)

    def test_no_tool_input_silent(self) -> None:
        rc = handle_pretooluse_agent(
            stdin_data={"sessionId": self.sid},
            cc_pid=self.cc_pid,
            base_dir=self.base,
        )
        self.assertEqual(rc, 0)

    def test_non_dict_stdin_silent(self) -> None:
        rc = handle_pretooluse_agent(
            stdin_data="invalid",  # type: ignore[arg-type]
            cc_pid=self.cc_pid,
            base_dir=self.base,
        )
        self.assertEqual(rc, 0)


if __name__ == "__main__":
    unittest.main()
