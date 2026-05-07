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
from typing import Optional

from harness.hooks import (
    HARNESS_ONLY_AGENTS,
    handle_posttooluse_agent,
    handle_posttooluse_file_op,
    handle_pretooluse_agent,
    handle_pretooluse_file_op,
    handle_session_start,
)
from harness.agent_trace import append as trace_append
from harness.agent_trace import read_all as read_trace
from harness.redo_log import read_all as read_redos
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
# §2.3.5 — architect TASK_DECOMPOSE 직전 DESIGN_VALIDATION PASS (DCN-CHG-20260430-05)
# ---------------------------------------------------------------------------


class CatastrophicDesignValidationTests(_PreToolBase):
    """architect TASK_DECOMPOSE 직전 validator DESIGN_VALIDATION DESIGN_REVIEW_PASS 필수.

    조건: SYSTEM_DESIGN.md 가 존재할 때만 발동 (시스템 설계 단계가 있었음). 단순
    MODULE_PLAN 진입은 미적용.
    """

    def _setup_full_review(self) -> None:
        """SD 까지의 정합 prose 들 박기 (§2.3.4 통과 + §2.3.5 검사 발동 조건)."""
        (self.run_path / "product-planner.md").write_text(
            "PRODUCT_PLAN_READY", encoding="utf-8",
        )
        (self.run_path / "plan-reviewer.md").write_text(
            "PLAN_REVIEW_PASS", encoding="utf-8",
        )
        (self.run_path / "ux-architect.md").write_text(
            "UX_FLOW_READY", encoding="utf-8",
        )
        (self.run_path / "architect-SYSTEM_DESIGN.md").write_text(
            "SYSTEM_DESIGN_READY", encoding="utf-8",
        )

    def test_td_blocked_without_design_review_pass(self) -> None:
        self._setup_full_review()
        # validator-DESIGN_VALIDATION.md 부재 → 차단
        rc = handle_pretooluse_agent(
            stdin_data=self._payload("architect", "TASK_DECOMPOSE"),
            cc_pid=self.cc_pid,
            base_dir=self.base,
        )
        self.assertEqual(rc, 1)

    def test_td_blocked_with_design_review_fail(self) -> None:
        self._setup_full_review()
        (self.run_path / "validator-DESIGN_VALIDATION.md").write_text(
            "DESIGN_REVIEW_FAIL — 인터페이스 미정의", encoding="utf-8",
        )
        rc = handle_pretooluse_agent(
            stdin_data=self._payload("architect", "TASK_DECOMPOSE"),
            cc_pid=self.cc_pid,
            base_dir=self.base,
        )
        self.assertEqual(rc, 1)

    def test_td_passes_with_design_review_pass(self) -> None:
        self._setup_full_review()
        (self.run_path / "validator-DESIGN_VALIDATION.md").write_text(
            "DESIGN_REVIEW_PASS — 3 계층 모두 통과", encoding="utf-8",
        )
        rc = handle_pretooluse_agent(
            stdin_data=self._payload("architect", "TASK_DECOMPOSE"),
            cc_pid=self.cc_pid,
            base_dir=self.base,
        )
        self.assertEqual(rc, 0)

    def test_sd_passes_without_design_review(self) -> None:
        """architect SYSTEM_DESIGN 호출 자체는 §2.3.5 미적용 (TD 만 검사)."""
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

    def test_td_skipped_when_no_system_design(self) -> None:
        """SYSTEM_DESIGN.md 부재 시 §2.3.5 발동 X — 단순 TASK_DECOMPOSE 직접 호출 케이스."""
        (self.run_path / "product-planner.md").write_text(
            "PRODUCT_PLAN_READY", encoding="utf-8",
        )
        (self.run_path / "plan-reviewer.md").write_text(
            "PLAN_REVIEW_PASS", encoding="utf-8",
        )
        (self.run_path / "ux-architect.md").write_text(
            "UX_FLOW_READY", encoding="utf-8",
        )
        # SYSTEM_DESIGN 없으면 §2.3.5 검사 skip — §2.3.4 만 적용 (이미 통과)
        rc = handle_pretooluse_agent(
            stdin_data=self._payload("architect", "TASK_DECOMPOSE"),
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


# ---------------------------------------------------------------------------
# §2.3.6~§2.3.8 — impl-task-loop 3-commit 구조 catastrophic gate (DCN-CHG-20260502-05)
# ---------------------------------------------------------------------------


class _ImplPreToolBase(unittest.TestCase):
    """impl loop (entry_point='impl') 컨텍스트 — 3-commit gate 발동 조건."""

    sid = "test-sid-impl"
    rid = "run-12345678"
    cc_pid = 77777

    def setUp(self) -> None:
        self._td = TemporaryDirectory()
        self.base = Path(self._td.name)
        write_pid_session(self.cc_pid, self.sid, base_dir=self.base)
        update_live(self.sid, base_dir=self.base)
        start_run(self.sid, self.rid, "impl", base_dir=self.base)  # entry_point="impl"
        write_pid_current_run(self.cc_pid, self.rid, base_dir=self.base)
        self.run_path = run_dir(self.sid, self.rid, base_dir=self.base)

    def tearDown(self) -> None:
        self._td.cleanup()

    def _payload(self, subagent: str, mode: str = "") -> dict:
        return {
            "sessionId": self.sid,
            "tool_input": {"subagent_type": subagent, "mode": mode},
        }

    def _set_stage_commit(self, stage: str, hash_: str = "abc12345") -> None:
        live = read_live(self.sid, base_dir=self.base) or {}
        active = live.get("active_runs", {})
        slot = dict(active[self.rid])
        sc = dict(slot.get("stage_commits") or {})
        sc[stage] = hash_
        slot["stage_commits"] = sc
        active[self.rid] = slot
        update_live(self.sid, base_dir=self.base, active_runs=active)


class StageCommitTestEngineerGateTests(_ImplPreToolBase):
    """§2.3.6 — test-engineer 호출 전 commit1(docs) 필수."""

    def test_test_engineer_blocked_without_docs_commit(self) -> None:
        rc = handle_pretooluse_agent(
            stdin_data=self._payload("test-engineer"),
            cc_pid=self.cc_pid,
            base_dir=self.base,
        )
        self.assertEqual(rc, 1)

    def test_test_engineer_allowed_with_docs_commit(self) -> None:
        self._set_stage_commit("docs")
        rc = handle_pretooluse_agent(
            stdin_data=self._payload("test-engineer"),
            cc_pid=self.cc_pid,
            base_dir=self.base,
        )
        self.assertEqual(rc, 0)

    def test_test_engineer_gate_skipped_for_non_impl_loop(self) -> None:
        """quick 루프 (entry_point='quick') 는 gate 미적용."""
        from harness.session_state import start_run as _sr, write_pid_current_run as _wpc
        with TemporaryDirectory() as td:
            base = Path(td)
            sid, rid, cc_pid = "sid-quick", "run-aaaabbbb", 66666
            write_pid_session(cc_pid, sid, base_dir=base)
            update_live(sid, base_dir=base)
            _sr(sid, rid, "quick", base_dir=base)  # entry_point="quick" → gate 비적용
            _wpc(cc_pid, rid, base_dir=base)
            rc = handle_pretooluse_agent(
                stdin_data={"sessionId": sid, "tool_input": {"subagent_type": "test-engineer", "mode": ""}},
                cc_pid=cc_pid,
                base_dir=base,
            )
            self.assertEqual(rc, 0)


class StageCommitEngineerImplGateTests(_ImplPreToolBase):
    """§2.3.7 — engineer IMPL 호출 전 commit2(tests) 필수."""

    def test_impl_blocked_without_tests_commit(self) -> None:
        (self.run_path / "architect-MODULE_PLAN.md").write_text("READY_FOR_IMPL", encoding="utf-8")
        self._set_stage_commit("docs")  # docs OK, tests 누락
        rc = handle_pretooluse_agent(
            stdin_data=self._payload("engineer", "IMPL"),
            cc_pid=self.cc_pid,
            base_dir=self.base,
        )
        self.assertEqual(rc, 1)

    def test_impl_allowed_with_tests_commit(self) -> None:
        (self.run_path / "architect-MODULE_PLAN.md").write_text("READY_FOR_IMPL", encoding="utf-8")
        self._set_stage_commit("docs")
        self._set_stage_commit("tests")
        rc = handle_pretooluse_agent(
            stdin_data=self._payload("engineer", "IMPL"),
            cc_pid=self.cc_pid,
            base_dir=self.base,
        )
        self.assertEqual(rc, 0)

    def test_polish_mode_skips_tests_gate(self) -> None:
        """POLISH 모드는 plan 검사 + tests gate 모두 skip."""
        rc = handle_pretooluse_agent(
            stdin_data=self._payload("engineer", "POLISH"),
            cc_pid=self.cc_pid,
            base_dir=self.base,
        )
        self.assertEqual(rc, 0)


class StageCommitPrReviewerGateTests(_ImplPreToolBase):
    """§2.3.8 — pr-reviewer 호출 전 commit3(src) 필수."""

    def test_pr_reviewer_blocked_without_src_commit(self) -> None:
        (self.run_path / "engineer-IMPL.md").write_text("IMPL_DONE", encoding="utf-8")
        (self.run_path / "validator-CODE_VALIDATION.md").write_text("PASS", encoding="utf-8")
        # src commit 누락
        rc = handle_pretooluse_agent(
            stdin_data=self._payload("pr-reviewer"),
            cc_pid=self.cc_pid,
            base_dir=self.base,
        )
        self.assertEqual(rc, 1)

    def test_pr_reviewer_allowed_with_src_commit(self) -> None:
        (self.run_path / "engineer-IMPL.md").write_text("IMPL_DONE", encoding="utf-8")
        (self.run_path / "validator-CODE_VALIDATION.md").write_text("PASS", encoding="utf-8")
        self._set_stage_commit("src")
        rc = handle_pretooluse_agent(
            stdin_data=self._payload("pr-reviewer"),
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


# ---------------------------------------------------------------------------
# DCN-CHG-20260501-01 — handle_pretooluse_file_op + handle_posttooluse_agent
# ---------------------------------------------------------------------------


class FileOpAgentRecordTests(_PreToolBase):
    """PreToolUse Agent 통과 시 live.json.active_agent 기록 확인."""

    def test_active_agent_recorded_on_pass(self) -> None:
        # qa = HARNESS_ONLY 외 + run 컨텍스트 있음 → 통과
        rc = handle_pretooluse_agent(
            stdin_data=self._payload("qa"),
            cc_pid=self.cc_pid,
            base_dir=self.base,
        )
        self.assertEqual(rc, 0)
        live = read_live(self.sid, base_dir=self.base)
        self.assertEqual(live.get("active_agent"), "qa")

    def test_active_agent_with_mode(self) -> None:
        # validator + DESIGN_VALIDATION = HARNESS_ONLY 아님 (DESIGN_VALIDATION 미포함)
        rc = handle_pretooluse_agent(
            stdin_data=self._payload("validator", mode="DESIGN_VALIDATION"),
            cc_pid=self.cc_pid,
            base_dir=self.base,
        )
        self.assertEqual(rc, 0)
        live = read_live(self.sid, base_dir=self.base)
        self.assertEqual(live.get("active_agent"), "validator")
        self.assertEqual(live.get("active_mode"), "DESIGN_VALIDATION")


class FileOpHookTests(_PreToolBase):
    """PreToolUse Edit/Write/Read/Bash agent_boundary 강제."""

    def setUp(self) -> None:
        super().setUp()
        # 모든 infra 신호 해제 — user 프로젝트 시뮬레이션.
        self._old_env = {}
        for k in ("DCNESS_INFRA", "CLAUDE_PLUGIN_ROOT"):
            self._old_env[k] = os.environ.get(k)
            os.environ.pop(k, None)
        # cwd 도 whitelist 외로 임시 이동.
        self._old_cwd = os.getcwd()
        os.chdir(str(self.base))

    def tearDown(self) -> None:
        os.chdir(self._old_cwd)
        for k, v in self._old_env.items():
            if v is not None:
                os.environ[k] = v
        super().tearDown()

    def _file_op_payload(self, tool_name: str, **tool_input) -> dict:
        return {
            "sessionId": self.sid,
            "tool_name": tool_name,
            "tool_input": tool_input,
        }

    def test_main_claude_passes(self) -> None:
        # active_agent 미설정 → 통과.
        rc = handle_pretooluse_file_op(
            stdin_data=self._file_op_payload("Edit", file_path="hooks/x.sh"),
            cc_pid=self.cc_pid,
            base_dir=self.base,
        )
        self.assertEqual(rc, 0)

    def test_engineer_blocked_on_infra_edit(self) -> None:
        update_live(self.sid, base_dir=self.base, active_agent="engineer")
        rc = handle_pretooluse_file_op(
            stdin_data=self._file_op_payload(
                "Edit", file_path="hooks/catastrophic-gate.sh"
            ),
            cc_pid=self.cc_pid,
            base_dir=self.base,
        )
        self.assertEqual(rc, 1)

    def test_engineer_allowed_on_src_edit(self) -> None:
        update_live(self.sid, base_dir=self.base, active_agent="engineer")
        rc = handle_pretooluse_file_op(
            stdin_data=self._file_op_payload("Edit", file_path="src/foo.ts"),
            cc_pid=self.cc_pid,
            base_dir=self.base,
        )
        self.assertEqual(rc, 0)

    def test_engineer_blocked_on_random_path(self) -> None:
        update_live(self.sid, base_dir=self.base, active_agent="engineer")
        rc = handle_pretooluse_file_op(
            stdin_data=self._file_op_payload("Write", file_path="README.md"),
            cc_pid=self.cc_pid,
            base_dir=self.base,
        )
        self.assertEqual(rc, 1)

    def test_product_planner_blocked_on_src_read(self) -> None:
        update_live(self.sid, base_dir=self.base, active_agent="product-planner")
        rc = handle_pretooluse_file_op(
            stdin_data=self._file_op_payload("Read", file_path="src/main.ts"),
            cc_pid=self.cc_pid,
            base_dir=self.base,
        )
        self.assertEqual(rc, 1)

    def test_engineer_bash_sed_blocks_infra(self) -> None:
        update_live(self.sid, base_dir=self.base, active_agent="engineer")
        rc = handle_pretooluse_file_op(
            stdin_data=self._file_op_payload(
                "Bash", command="sed -i 's/x/y/' hooks/foo.sh"
            ),
            cc_pid=self.cc_pid,
            base_dir=self.base,
        )
        self.assertEqual(rc, 1)

    def test_bash_no_indicator_passes(self) -> None:
        update_live(self.sid, base_dir=self.base, active_agent="engineer")
        rc = handle_pretooluse_file_op(
            stdin_data=self._file_op_payload("Bash", command="ls -la docs/"),
            cc_pid=self.cc_pid,
            base_dir=self.base,
        )
        self.assertEqual(rc, 0)

    def test_mcp_tool_passes_boundary_and_records_trace(self) -> None:
        # #255 W5 — mcp__* 도구는 boundary 검사 skip + trace pre append.
        # designer / qa false positive (prose-only 의심) 차단 의도.
        from harness.session_state import (
            start_run, generate_run_id, write_pid_current_run, write_pid_session,
        )
        from harness.agent_trace import histogram as _hist
        update_live(self.sid, base_dir=self.base, active_agent="designer")
        rid = generate_run_id()
        start_run(self.sid, rid, "designer", base_dir=self.base)
        write_pid_session(self.cc_pid, self.sid, base_dir=self.base)
        write_pid_current_run(self.cc_pid, rid, base_dir=self.base)
        rc = handle_pretooluse_file_op(
            stdin_data={
                "sessionId": self.sid,
                "tool_name": "mcp__pencil__batch_design",
                "tool_input": {"operations": "..."},
            },
            cc_pid=self.cc_pid,
            base_dir=self.base,
        )
        self.assertEqual(rc, 0, "mcp__* 도구는 boundary 차단 X — trace 만 기록")
        hist = _hist(self.sid, rid, base_dir=self.base)
        self.assertEqual(
            hist.get("mcp__pencil__batch_design", 0), 1,
            "mcp__* 도구가 histogram 에 1 카운트되어야 함",
        )


class PostToolUseAgentClearTests(_PreToolBase):
    def test_clears_active_agent(self) -> None:
        update_live(
            self.sid, base_dir=self.base,
            active_agent="engineer", active_mode="IMPL",
        )
        rc = handle_posttooluse_agent(
            stdin_data={"sessionId": self.sid},
            cc_pid=self.cc_pid,
            base_dir=self.base,
        )
        self.assertEqual(rc, 0)
        live = read_live(self.sid, base_dir=self.base)
        self.assertNotIn("active_agent", live)
        self.assertNotIn("active_mode", live)

    def test_invalid_sid_silent(self) -> None:
        rc = handle_posttooluse_agent(
            stdin_data={"sessionId": "!"},
            cc_pid=self.cc_pid,
            base_dir=self.base,
        )
        self.assertEqual(rc, 0)


# ---------------------------------------------------------------------------
# DCN-CHG-20260501-11 — sub 행동 trace append (Pre + Post)
# ---------------------------------------------------------------------------


class FileOpTraceTests(_PreToolBase):
    """handle_pretooluse_file_op 통과 시 agent-trace.jsonl pre append."""

    def setUp(self) -> None:
        super().setUp()
        self._old_env = {}
        for k in ("DCNESS_INFRA", "CLAUDE_PLUGIN_ROOT"):
            self._old_env[k] = os.environ.get(k)
            os.environ.pop(k, None)
        self._old_cwd = os.getcwd()
        os.chdir(str(self.base))

    def tearDown(self) -> None:
        os.chdir(self._old_cwd)
        for k, v in self._old_env.items():
            if v is not None:
                os.environ[k] = v
        super().tearDown()

    def _payload_file(self, tool_name: str, **tool_input) -> dict:
        return {
            "sessionId": self.sid,
            "tool_name": tool_name,
            "tool_input": tool_input,
        }

    def test_pre_trace_appended_on_pass(self) -> None:
        update_live(self.sid, base_dir=self.base, active_agent="engineer")
        rc = handle_pretooluse_file_op(
            stdin_data=self._payload_file("Edit", file_path="src/foo.py"),
            cc_pid=self.cc_pid,
            base_dir=self.base,
        )
        self.assertEqual(rc, 0)
        entries = read_trace(self.sid, self.rid, base_dir=self.base)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["phase"], "pre")
        self.assertEqual(entries[0]["agent"], "engineer")
        self.assertEqual(entries[0]["tool"], "Edit")
        self.assertEqual(entries[0]["input"], "src/foo.py")

    def test_no_trace_on_block(self) -> None:
        update_live(self.sid, base_dir=self.base, active_agent="engineer")
        rc = handle_pretooluse_file_op(
            stdin_data=self._payload_file("Edit", file_path="hooks/foo.sh"),
            cc_pid=self.cc_pid,
            base_dir=self.base,
        )
        self.assertEqual(rc, 1)
        entries = read_trace(self.sid, self.rid, base_dir=self.base)
        self.assertEqual(entries, [])

    def test_no_trace_when_main_claude(self) -> None:
        # active_agent 미설정 → trace 미기록.
        rc = handle_pretooluse_file_op(
            stdin_data=self._payload_file("Edit", file_path="src/foo.py"),
            cc_pid=self.cc_pid,
            base_dir=self.base,
        )
        self.assertEqual(rc, 0)
        entries = read_trace(self.sid, self.rid, base_dir=self.base)
        self.assertEqual(entries, [])

    def test_bash_input_in_trace(self) -> None:
        update_live(self.sid, base_dir=self.base, active_agent="engineer")
        rc = handle_pretooluse_file_op(
            stdin_data=self._payload_file("Bash", command="ls -la docs/"),
            cc_pid=self.cc_pid,
            base_dir=self.base,
        )
        self.assertEqual(rc, 0)
        entries = read_trace(self.sid, self.rid, base_dir=self.base)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["input"], "ls -la docs/")

    def test_long_input_truncated(self) -> None:
        update_live(self.sid, base_dir=self.base, active_agent="engineer")
        long_cmd = "echo " + "x" * 500
        rc = handle_pretooluse_file_op(
            stdin_data=self._payload_file("Bash", command=long_cmd),
            cc_pid=self.cc_pid,
            base_dir=self.base,
        )
        self.assertEqual(rc, 0)
        entries = read_trace(self.sid, self.rid, base_dir=self.base)
        # 200 cap + "..." suffix
        self.assertTrue(entries[0]["input"].endswith("..."))
        self.assertLessEqual(len(entries[0]["input"]), 210)


class PostToolUseFileOpTests(_PreToolBase):
    """handle_posttooluse_file_op — sub 행동 post trace append."""

    def _post_payload(
        self, tool_name: str, tool_response: dict, **tool_input
    ) -> dict:
        return {
            "sessionId": self.sid,
            "tool_name": tool_name,
            "tool_input": tool_input,
            "tool_response": tool_response,
        }

    def test_post_trace_appended(self) -> None:
        update_live(self.sid, base_dir=self.base, active_agent="engineer")
        rc = handle_posttooluse_file_op(
            stdin_data=self._post_payload(
                "Bash",
                {"exit_code": 0, "stdout": "hello"},
                command="echo hello",
            ),
            cc_pid=self.cc_pid,
            base_dir=self.base,
        )
        self.assertEqual(rc, 0)
        entries = read_trace(self.sid, self.rid, base_dir=self.base)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["phase"], "post")
        self.assertEqual(entries[0]["tool"], "Bash")
        self.assertEqual(entries[0]["exit"], 0)
        self.assertEqual(entries[0]["stdout_size"], 5)

    def test_post_noop_when_main(self) -> None:
        # active_agent 미설정 → noop.
        rc = handle_posttooluse_file_op(
            stdin_data=self._post_payload("Edit", {}, file_path="src/x.py"),
            cc_pid=self.cc_pid,
            base_dir=self.base,
        )
        self.assertEqual(rc, 0)
        entries = read_trace(self.sid, self.rid, base_dir=self.base)
        self.assertEqual(entries, [])

    def test_post_records_is_error(self) -> None:
        update_live(self.sid, base_dir=self.base, active_agent="engineer")
        rc = handle_posttooluse_file_op(
            stdin_data=self._post_payload(
                "Bash",
                {"exit_code": 1, "is_error": True},
                command="false",
            ),
            cc_pid=self.cc_pid,
            base_dir=self.base,
        )
        self.assertEqual(rc, 0)
        entries = read_trace(self.sid, self.rid, base_dir=self.base)
        self.assertEqual(entries[0]["exit"], 1)
        self.assertTrue(entries[0]["is_error"])

    def test_post_invalid_sid_silent(self) -> None:
        rc = handle_posttooluse_file_op(
            stdin_data={"sessionId": "!"},
            cc_pid=self.cc_pid,
            base_dir=self.base,
        )
        self.assertEqual(rc, 0)


# ---------------------------------------------------------------------------
# DCN-CHG-20260501-13 — PostToolUse Agent histogram inject + auto redo_log
# ---------------------------------------------------------------------------


class PostToolUseAgentHistogramTests(_PreToolBase):
    """sub 종료 후 trace 집계 → redo_log 자동 append + stdout 메시지."""

    def _seed_trace(self, agent_id: str, tools: list) -> None:
        for tool in tools:
            trace_append(self.sid, self.rid, {
                "phase": "pre", "agent_id": agent_id, "tool": tool,
            }, base_dir=self.base)
            trace_append(self.sid, self.rid, {
                "phase": "post", "agent_id": agent_id, "tool": tool,
            }, base_dir=self.base)

    def _post_payload(self, sub_type: str, agent_id: str, prompt: str = "") -> dict:
        return {
            "sessionId": self.sid,
            "agent_id": agent_id,
            "tool_name": "Agent",
            "tool_input": {
                "subagent_type": sub_type,
                "prompt": prompt,
            },
        }

    def test_pass_auto_redo_log(self):
        self._seed_trace("aid-engineer", ["Read", "Read", "Write", "Bash"])
        rc = handle_posttooluse_agent(
            stdin_data=self._post_payload("engineer", "aid-engineer"),
            cc_pid=self.cc_pid,
            base_dir=self.base,
        )
        self.assertEqual(rc, 0)
        redos = read_redos(self.sid, self.rid, base_dir=self.base)
        self.assertEqual(len(redos), 1)
        self.assertEqual(redos[0]["decision"], "PASS")
        self.assertTrue(redos[0]["auto"])
        self.assertEqual(redos[0]["sub"], "engineer")
        self.assertEqual(redos[0]["tool_uses"], 4)

    def test_redo_suspect_on_low_calls(self):
        self._seed_trace("aid-x", ["Read"])
        rc = handle_posttooluse_agent(
            stdin_data=self._post_payload("architect", "aid-x"),
            cc_pid=self.cc_pid,
            base_dir=self.base,
        )
        self.assertEqual(rc, 0)
        redos = read_redos(self.sid, self.rid, base_dir=self.base)
        self.assertEqual(redos[0]["decision"], "REDO_SUSPECT")
        self.assertTrue(redos[0]["anomalies"])

    def test_redo_suspect_on_prose_only(self):
        # Read 만 4번 + Write 0건. prompt 에 "create file" 약속.
        self._seed_trace("aid-arch", ["Read", "Read", "Read", "Read"])
        rc = handle_posttooluse_agent(
            stdin_data=self._post_payload(
                "architect", "aid-arch",
                prompt="create the impl plan file at docs/foo.md"
            ),
            cc_pid=self.cc_pid,
            base_dir=self.base,
        )
        self.assertEqual(rc, 0)
        redos = read_redos(self.sid, self.rid, base_dir=self.base)
        self.assertEqual(redos[0]["decision"], "REDO_SUSPECT")
        self.assertTrue(any("prose-only" in a for a in redos[0]["anomalies"]))

    def test_clears_active_agent_still_works(self):
        update_live(
            self.sid, base_dir=self.base,
            active_agent="engineer", active_mode="IMPL",
        )
        self._seed_trace("aid-engineer", ["Read", "Bash"])
        rc = handle_posttooluse_agent(
            stdin_data=self._post_payload("engineer", "aid-engineer"),
            cc_pid=self.cc_pid,
            base_dir=self.base,
        )
        self.assertEqual(rc, 0)
        live = read_live(self.sid, base_dir=self.base)
        self.assertNotIn("active_agent", live)
        self.assertNotIn("active_mode", live)

    def test_no_trace_no_redo_log(self):
        # trace 비어있으면 자동 redo_log 미추가, hook 본 흐름만.
        rc = handle_posttooluse_agent(
            stdin_data=self._post_payload("engineer", "aid-empty"),
            cc_pid=self.cc_pid,
            base_dir=self.base,
        )
        self.assertEqual(rc, 0)
        self.assertEqual(read_redos(self.sid, self.rid, base_dir=self.base), [])

    def test_agent_id_fallback_only_on_subtype_match(self):
        """#272 W3 — payload agent_id 비어있고 trace 의 마지막 entry 가 *다른* sub
        의 것이면 폴백 사용 X. redo_log 의 agent_id 가 직전 step 으로 오기록되는
        문제 회귀."""
        # trace 에 engineer 의 흔적만 있음 (직전 step). 이제 pr-reviewer Agent 가
        # 호출됐고 (prose-only 라 자기 file-op trace 없음), payload agent_id 비어있음.
        for tool in ["Read", "Edit", "Bash"]:
            trace_append(self.sid, self.rid, {
                "phase": "pre", "agent_id": "aid-engineer",
                "agent": "engineer", "tool": tool,
            }, base_dir=self.base)
        rc = handle_posttooluse_agent(
            stdin_data={
                "sessionId": self.sid,
                "tool_name": "Agent",
                "tool_input": {"subagent_type": "pr-reviewer"},
                # agent_id 비어있음
            },
            cc_pid=self.cc_pid,
            base_dir=self.base,
        )
        self.assertEqual(rc, 0)
        redos = read_redos(self.sid, self.rid, base_dir=self.base)
        if redos:
            # trace 마지막 agent="engineer" ≠ sub_type="pr-reviewer"
            # → target_aid 폴백 안 됨 → ""
            self.assertNotEqual(
                redos[0].get("agent_id"), "aid-engineer",
                msg="직전 sub 의 agent_id 가 폴백으로 박혔음 (#272 W3 회귀)",
            )

    def test_agent_id_fallback_uses_matching_subtype(self):
        """#272 W3 회귀 — trace 의 마지막 entry agent 가 sub_type 과 *일치* 하면 폴백 사용."""
        # 직전 다른 sub 의 trace + 같은 sub_type (pr-reviewer) 의 trace 둘 다.
        for aid, agent, tool in [
            ("aid-engineer", "engineer", "Edit"),
            ("aid-engineer", "engineer", "Bash"),
            ("aid-pr1", "pr-reviewer", "Read"),
            ("aid-pr1", "pr-reviewer", "Read"),
        ]:
            trace_append(self.sid, self.rid, {
                "phase": "pre", "agent_id": aid, "agent": agent, "tool": tool,
            }, base_dir=self.base)
        rc = handle_posttooluse_agent(
            stdin_data={
                "sessionId": self.sid,
                "tool_name": "Agent",
                "tool_input": {"subagent_type": "pr-reviewer"},
            },
            cc_pid=self.cc_pid,
            base_dir=self.base,
        )
        self.assertEqual(rc, 0)
        redos = read_redos(self.sid, self.rid, base_dir=self.base)
        # 폴백 → aid-pr1 (sub_type 일치하는 마지막)
        self.assertEqual(redos[0]["agent_id"], "aid-pr1")
        self.assertEqual(redos[0]["sub"], "pr-reviewer")

    def test_prose_only_subtype_not_promised_write(self):
        """#272 W1 — prose-only sub (qa) 는 promised_write anomaly 발화 X."""
        for tool in ["Read", "Read", "Read"]:
            trace_append(self.sid, self.rid, {
                "phase": "pre", "agent_id": "aid-qa",
                "agent": "qa", "tool": tool,
            }, base_dir=self.base)
        rc = handle_posttooluse_agent(
            stdin_data={
                "sessionId": self.sid,
                "agent_id": "aid-qa",
                "tool_name": "Agent",
                "tool_input": {
                    "subagent_type": "qa",
                    "prompt": "분석 작성해줘",
                },
            },
            cc_pid=self.cc_pid,
            base_dir=self.base,
        )
        self.assertEqual(rc, 0)
        redos = read_redos(self.sid, self.rid, base_dir=self.base)
        self.assertEqual(redos[0]["decision"], "PASS")
        # prose-only anomaly 발화 X
        self.assertFalse(
            any("prose-only" in a for a in redos[0]["anomalies"]),
            msg="prose-only 화이트리스트 미적용 (#272 W1 회귀)",
        )


# ---------------------------------------------------------------------------
# DCN-CHG-20260501-15 — PostToolUse Agent prose auto-staging
# ---------------------------------------------------------------------------


class PostToolUseAgentProseAutoStageTests(_PreToolBase):
    """handle_posttooluse_agent — tool_response.text → run_dir prose 자동 저장."""

    def _payload_with_prose(
        self, sub_type: str, agent: str, mode: Optional[str], prose: str
    ) -> dict:
        return {
            "sessionId": self.sid,
            "tool_name": "Agent",
            "tool_input": {
                "subagent_type": sub_type,
            },
            "tool_response": [{"type": "text", "text": prose}],
        }

    def _set_current_step(self, agent: str, mode: Optional[str]) -> None:
        from harness.session_state import update_current_step
        update_current_step(self.sid, self.rid, agent, mode, base_dir=self.base)

    def test_prose_staged_to_run_dir(self) -> None:
        self._set_current_step("qa", None)
        prose = "## 결과\nFUNCTIONAL_BUG\n"
        rc = handle_posttooluse_agent(
            stdin_data=self._payload_with_prose("qa", "qa", None, prose),
            cc_pid=self.cc_pid,
            base_dir=self.base,
        )
        self.assertEqual(rc, 0)
        expected = session_dir(self.sid, base_dir=self.base) / "runs" / self.rid / "qa.md"
        self.assertTrue(expected.exists())
        self.assertEqual(expected.read_text(encoding="utf-8"), prose)

    def test_prose_staged_with_mode(self) -> None:
        self._set_current_step("validator", "PLAN_VALIDATION")
        prose = "## 결론\nPASS\n"
        rc = handle_posttooluse_agent(
            stdin_data=self._payload_with_prose("validator", "validator", "PLAN_VALIDATION", prose),
            cc_pid=self.cc_pid,
            base_dir=self.base,
        )
        self.assertEqual(rc, 0)
        expected = (
            session_dir(self.sid, base_dir=self.base) / "runs" / self.rid
            / "validator-PLAN_VALIDATION.md"
        )
        self.assertTrue(expected.exists())

    def test_prose_file_stored_in_current_step(self) -> None:
        self._set_current_step("architect", "MODULE_PLAN")
        prose = "## 결론\nREADY_FOR_IMPL\n"
        handle_posttooluse_agent(
            stdin_data=self._payload_with_prose("architect", "architect", "MODULE_PLAN", prose),
            cc_pid=self.cc_pid,
            base_dir=self.base,
        )
        live = read_live(self.sid, base_dir=self.base) or {}
        slot = live.get("active_runs", {}).get(self.rid, {})
        cur_step = slot.get("current_step") or {}
        self.assertIn("prose_file", cur_step)
        self.assertTrue(cur_step["prose_file"].endswith("architect-MODULE_PLAN.md"))

    def test_empty_prose_no_staging(self) -> None:
        self._set_current_step("qa", None)
        rc = handle_posttooluse_agent(
            stdin_data=self._payload_with_prose("qa", "qa", None, "   "),
            cc_pid=self.cc_pid,
            base_dir=self.base,
        )
        self.assertEqual(rc, 0)
        expected = session_dir(self.sid, base_dir=self.base) / "runs" / self.rid / "qa.md"
        self.assertFalse(expected.exists())

    def test_tool_response_dict_format_fallback(self) -> None:
        """dict 포맷 ({\"text\": ...}) 하위호환 — CC 포맷 변경 전 방어."""
        self._set_current_step("qa", None)
        prose = "## 결론\nPASS\n"
        rc = handle_posttooluse_agent(
            stdin_data={
                "sessionId": self.sid,
                "tool_name": "Agent",
                "tool_input": {"subagent_type": "qa"},
                "tool_response": {"type": "text", "text": prose},
            },
            cc_pid=self.cc_pid,
            base_dir=self.base,
        )
        self.assertEqual(rc, 0)
        expected = session_dir(self.sid, base_dir=self.base) / "runs" / self.rid / "qa.md"
        self.assertTrue(expected.exists())
        self.assertEqual(expected.read_text(encoding="utf-8"), prose)

    def test_tool_response_string_format_fallback(self) -> None:
        """string 포맷 하위호환."""
        self._set_current_step("qa", None)
        prose = "## 결론\nPASS\n"
        rc = handle_posttooluse_agent(
            stdin_data={
                "sessionId": self.sid,
                "tool_name": "Agent",
                "tool_input": {"subagent_type": "qa"},
                "tool_response": prose,
            },
            cc_pid=self.cc_pid,
            base_dir=self.base,
        )
        self.assertEqual(rc, 0)
        expected = session_dir(self.sid, base_dir=self.base) / "runs" / self.rid / "qa.md"
        self.assertTrue(expected.exists())

    def test_tool_response_empty_list_no_staging(self) -> None:
        """빈 list → prose 없음."""
        self._set_current_step("qa", None)
        rc = handle_posttooluse_agent(
            stdin_data={
                "sessionId": self.sid,
                "tool_name": "Agent",
                "tool_input": {"subagent_type": "qa"},
                "tool_response": [],
            },
            cc_pid=self.cc_pid,
            base_dir=self.base,
        )
        self.assertEqual(rc, 0)
        expected = session_dir(self.sid, base_dir=self.base) / "runs" / self.rid / "qa.md"
        self.assertFalse(expected.exists())

    def test_no_tool_response_no_staging(self) -> None:
        self._set_current_step("qa", None)
        rc = handle_posttooluse_agent(
            stdin_data={"sessionId": self.sid, "tool_name": "Agent"},
            cc_pid=self.cc_pid,
            base_dir=self.base,
        )
        self.assertEqual(rc, 0)
        expected = session_dir(self.sid, base_dir=self.base) / "runs" / self.rid / "qa.md"
        self.assertFalse(expected.exists())

    def test_no_current_step_no_staging(self) -> None:
        prose = "## 결론\nPASS\n"
        rc = handle_posttooluse_agent(
            stdin_data=self._payload_with_prose("qa", "qa", None, prose),
            cc_pid=self.cc_pid,
            base_dir=self.base,
        )
        self.assertEqual(rc, 0)
        expected = session_dir(self.sid, base_dir=self.base) / "runs" / self.rid / "qa.md"
        self.assertFalse(expected.exists())

    def test_no_current_step_emits_diagnostic_stderr(self) -> None:
        """#272 W2 / #273 W1 — silent fail 제거. current_step 부재 시 stderr 진단 로그.

        post-agent-clear.sh 가 stderr → /tmp/dcness-hook-stderr.log 보존이라
        다음 run 에서 외부 환경 (jajang) staging 미동작 원인 진단 가능.
        """
        import io
        import contextlib

        prose = "## 결론\nPASS\n"
        buf = io.StringIO()
        with contextlib.redirect_stderr(buf):
            rc = handle_posttooluse_agent(
                stdin_data=self._payload_with_prose("qa", "qa", None, prose),
                cc_pid=self.cc_pid,
                base_dir=self.base,
            )
        self.assertEqual(rc, 0)
        stderr = buf.getvalue()
        self.assertIn("[hook prose stage]", stderr)
        self.assertIn("current_step 부재", stderr)

    def test_unrecognized_tool_response_emits_shape_diagnostic(self) -> None:
        """#272 W2 — tool_response 형식 미스매치 시 stderr 에 형식 정보 출력."""
        import io
        import contextlib

        self._set_current_step("qa", None)
        # CC 가 다른 형식 보낼 가능성 — list of dict 인데 "type" 이 "text" 아닌 경우
        buf = io.StringIO()
        with contextlib.redirect_stderr(buf):
            rc = handle_posttooluse_agent(
                stdin_data={
                    "sessionId": self.sid,
                    "tool_name": "Agent",
                    "tool_input": {"subagent_type": "qa"},
                    "tool_response": [{"type": "tool_result", "content": "x"}],
                },
                cc_pid=self.cc_pid,
                base_dir=self.base,
            )
        self.assertEqual(rc, 0)
        stderr = buf.getvalue()
        self.assertIn("[hook prose stage]", stderr)
        self.assertIn("prose 추출 실패", stderr)
        # 형식 정보 포함 — 외부 환경 디버그용
        self.assertIn("item0_type=tool_result", stderr)

    def test_occurrence_increments_on_repeat(self) -> None:
        import json

        self._set_current_step("engineer", None)
        # 첫 번째 end-step 기록을 .steps.jsonl 에 직접 박기 (base_dir 정합)
        steps_path = run_dir(self.sid, self.rid, base_dir=self.base) / ".steps.jsonl"
        steps_path.parent.mkdir(parents=True, exist_ok=True)
        steps_path.write_text(
            json.dumps({"agent": "engineer", "mode": None, "enum": "PASS"}) + "\n",
            encoding="utf-8",
        )
        # 두 번째 sub 호출 → occurrence=1 → engineer-1.md
        prose = "## 결론\nPASS\n"
        handle_posttooluse_agent(
            stdin_data=self._payload_with_prose("engineer", "engineer", None, prose),
            cc_pid=self.cc_pid,
            base_dir=self.base,
        )
        expected = (
            session_dir(self.sid, base_dir=self.base) / "runs" / self.rid / "engineer-1.md"
        )
        self.assertTrue(expected.exists())


if __name__ == "__main__":
    unittest.main()
