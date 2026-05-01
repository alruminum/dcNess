"""hooks.py — Claude Code 훅 핸들러 (`docs/conveyor-design.md` §7).

bash 훅 (`hooks/*.sh`) 이 stdin payload + cc_pid 를 본 모듈의 핸들러로 전달.
순수 Python 으로 catastrophic 검사 + by-pid 레지스트리 갱신을 처리.

핸들러:
    handle_session_start(stdin_data, cc_pid) -> exit_code
        SessionStart event. sid 추출 + by-pid 작성 + live.json 초기화.

    handle_pretooluse_agent(stdin_data, cc_pid) -> exit_code
        PreToolUse, tool=Agent. HARNESS_ONLY_AGENTS + §2.3 4 룰 검사.
        exit 0 = allow, exit 1 = block (stderr 메시지 + CC 가 호출 거부).

규약:
    - 모든 실패 케이스 silent (exit 0) — CC 동작 방해 최소화
    - 단, catastrophic 위반은 exit 1 + stderr 메시지 (CC 사용자에게 가시)
    - stdin payload 파싱 실패 / sid 없음 / 잘못된 sid 등은 exit 0 (skip)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from harness.session_state import (
    read_live,
    read_pid_current_run,
    run_dir,
    update_live,
    valid_cc_pid,
    valid_session_id,
    write_pid_session,
)


__all__ = [
    "HARNESS_ONLY_AGENTS",
    "handle_session_start",
    "handle_pretooluse_agent",
    "handle_pretooluse_file_op",
    "handle_posttooluse_agent",
    "handle_posttooluse_file_op",
]


# ── DCN-CHG-20260501-11 — agent-trace.jsonl 헬퍼 ──────────────────────


_TRACE_INPUT_MAX = 200  # entry size cap (POSIX append atomic = 4096 bytes 이내)


def _summarize_input(tool_name: str, tool_input: Dict[str, Any]) -> str:
    """tool_input 핵심을 _TRACE_INPUT_MAX bytes 이하로 요약."""
    if not isinstance(tool_input, dict):
        return ""
    if tool_name == "Bash":
        s = str(tool_input.get("command", ""))
    elif tool_name in ("Edit", "Write", "NotebookEdit", "Read"):
        s = str(tool_input.get("file_path", "") or tool_input.get("path", ""))
    elif tool_name in ("Glob", "Grep"):
        s = str(tool_input.get("pattern", ""))
    else:
        s = ""
    if len(s) > _TRACE_INPUT_MAX:
        s = s[:_TRACE_INPUT_MAX] + "..."
    return s


def _append_trace_safe(
    sid: str,
    rid: str,
    entry: Dict[str, Any],
    *,
    base_dir: Optional[Path] = None,
) -> None:
    """trace append — 어떤 실패도 hook 본 흐름 방해 X."""
    try:
        from harness.agent_trace import append as _trace_append
        _trace_append(sid, rid, entry, base_dir=base_dir)
    except Exception:  # noqa: BLE001 — silent
        pass


# orchestration.md §7.1 — 컨베이어 경유 필수 agent
# (agent_name, mode_or_None) — None = 모든 mode 적용
HARNESS_ONLY_AGENTS: tuple = (
    ("engineer", None),
    ("validator", "PLAN_VALIDATION"),
    ("validator", "CODE_VALIDATION"),
    ("validator", "BUGFIX_VALIDATION"),
)


def _extract_sid(payload: Dict[str, Any]) -> str:
    """OMC 3 변형 fallback."""
    return (
        payload.get("session_id")
        or payload.get("sessionId")
        or payload.get("sessionid")
        or ""
    )


def _is_harness_only(subagent: str, mode: str) -> bool:
    for agent, m in HARNESS_ONLY_AGENTS:
        if subagent == agent and (m is None or mode == m):
            return True
    return False


def _resolve_rid(
    sid: str,
    cc_pid: Optional[int],
    *,
    base_dir: Optional[Path] = None,
) -> str:
    """rid 결정 — by-pid-current-run 우선, live.json 의 가장 최근 미완료 슬롯 폴백."""
    if cc_pid is not None and valid_cc_pid(cc_pid):
        rid = read_pid_current_run(cc_pid, base_dir=base_dir)
        if rid:
            return rid

    live = read_live(sid, base_dir=base_dir) or {}
    active = live.get("active_runs", {})
    if not isinstance(active, dict):
        return ""
    candidates = [
        (rid_, slot) for rid_, slot in active.items()
        if isinstance(slot, dict) and slot.get("completed_at") is None
    ]
    if not candidates:
        return ""
    candidates.sort(key=lambda x: x[1].get("started_at", ""), reverse=True)
    return candidates[0][0]


def handle_session_start(
    stdin_data: Optional[Dict[str, Any]] = None,
    cc_pid: Optional[int] = None,
    *,
    base_dir: Optional[Path] = None,
) -> int:
    """SessionStart 훅 처리.

    1. stdin 의 sessionId 추출
    2. regex 검증
    3. `.by-pid/{cc_pid}` ← sid 작성
    4. `.sessions/{sid}/live.json` 초기화 (없으면)

    실패 시 silent (exit 0).
    """
    if stdin_data is None:
        try:
            raw = sys.stdin.read()
            stdin_data = json.loads(raw) if raw.strip() else {}
        except (json.JSONDecodeError, OSError):
            return 0

    if not isinstance(stdin_data, dict):
        return 0

    sid = _extract_sid(stdin_data)
    if not valid_session_id(sid):
        return 0

    if cc_pid is None or not valid_cc_pid(cc_pid):
        return 0

    try:
        write_pid_session(cc_pid, sid, base_dir=base_dir)
        if not read_live(sid, base_dir=base_dir):
            update_live(sid, base_dir=base_dir)
    except (OSError, ValueError):
        return 0
    return 0


def handle_pretooluse_agent(
    stdin_data: Optional[Dict[str, Any]] = None,
    cc_pid: Optional[int] = None,
    *,
    base_dir: Optional[Path] = None,
) -> int:
    """PreToolUse Agent 훅 처리 — HARNESS_ONLY_AGENTS + orchestration.md §2.3 4룰.

    Returns:
        0: allow
        1: block (stderr 메시지 동반 — CC 가 호출 거부)
    """
    if stdin_data is None:
        try:
            raw = sys.stdin.read()
            stdin_data = json.loads(raw) if raw.strip() else {}
        except (json.JSONDecodeError, OSError):
            return 0  # parse 실패 → silent allow

    if not isinstance(stdin_data, dict):
        return 0

    sid = _extract_sid(stdin_data)
    if not valid_session_id(sid):
        return 0  # sid 없음 → 검사 불가, allow

    tool_input = stdin_data.get("tool_input")
    if not isinstance(tool_input, dict):
        return 0
    subagent = tool_input.get("subagent_type", "") or ""
    mode = tool_input.get("mode", "") or ""

    rid = _resolve_rid(sid, cc_pid, base_dir=base_dir)

    # 1. HARNESS_ONLY_AGENTS — run 컨텍스트 없으면 차단
    if _is_harness_only(subagent, mode):
        if not rid:
            label = subagent + (f":{mode}" if mode else "")
            print(
                f"[catastrophic] {label} 는 컨베이어 경유 필수 (run 미시작)",
                file=sys.stderr,
            )
            return 1

    if not rid:
        return 0  # 컨베이어 외부 — 그 외 agent 는 통과

    rd = run_dir(sid, rid, base_dir=base_dir)

    # 2. §2.3.3 — engineer 직전 architect plan READY 필수 (mode != POLISH)
    if subagent == "engineer" and mode != "POLISH":
        if not _has_plan_ready(rd):
            print(
                "[catastrophic §2.3.3] engineer 호출은 architect plan READY 후만 "
                "(MODULE_PLAN.md 안 READY_FOR_IMPL 또는 LIGHT_PLAN.md 안 LIGHT_PLAN_READY)",
                file=sys.stderr,
            )
            return 1

    # 3. §2.3.1 — pr-reviewer 직전 validator (CODE/BUGFIX) PASS 필수
    if subagent == "pr-reviewer":
        if _has_engineer_write(rd) and not _has_validator_pass(rd):
            print(
                "[catastrophic §2.3.1] pr-reviewer 호출은 validator "
                "CODE_VALIDATION 또는 BUGFIX_VALIDATION PASS 후만",
                file=sys.stderr,
            )
            return 1

    # 4. §2.3.4 — architect SD/TD 직전 plan-reviewer + ux-architect 검토 필수
    if subagent == "architect" and mode in ("SYSTEM_DESIGN", "TASK_DECOMPOSE"):
        if (rd / "product-planner.md").exists():
            if not _has_plan_review_pass(rd):
                print(
                    "[catastrophic §2.3.4] PRD 변경 후 plan-reviewer "
                    "PLAN_REVIEW_PASS 필수",
                    file=sys.stderr,
                )
                return 1
            if not _has_ux_flow_ready(rd):
                print(
                    "[catastrophic §2.3.4] PRD 변경 후 ux-architect "
                    "UX_FLOW_READY/PATCHED 필수",
                    file=sys.stderr,
                )
                return 1

    # 5. §2.3.5 (DCN-CHG-20260430-05) — architect TASK_DECOMPOSE 직전 validator
    #    DESIGN_VALIDATION (DESIGN_REVIEW_PASS) 필수. 시스템 설계 검증 안 한 채
    #    impl batch 분해 = 무의미.
    if subagent == "architect" and mode == "TASK_DECOMPOSE":
        # SYSTEM_DESIGN 단계가 있었다는 사실 확인 — design-validation 검사 발동 조건
        if (rd / "architect-SYSTEM_DESIGN.md").exists():
            if not _has_design_review_pass(rd):
                print(
                    "[catastrophic §2.3.5] architect TASK_DECOMPOSE 직전 "
                    "validator DESIGN_VALIDATION DESIGN_REVIEW_PASS 필수",
                    file=sys.stderr,
                )
                return 1

    # DCN-CHG-20260501-01: 통과 시 live.json.active_agent 기록 — sub-agent 내부
    # PreToolUse(Edit/Write/Read/Bash) 훅이 활성 agent 판정에 사용 (agent_boundary).
    if subagent:
        try:
            update_live(sid, base_dir=base_dir, active_agent=subagent, active_mode=(mode or None))
        except (OSError, ValueError):
            pass  # 실패해도 Agent 호출은 통과 — 식별만 누락.

    return 0


# ── DCN-CHG-20260501-01 — sub-agent path 강제 (handoff-matrix.md §4) ─


def handle_pretooluse_file_op(
    stdin_data: Optional[Dict[str, Any]] = None,
    cc_pid: Optional[int] = None,
    *,
    base_dir: Optional[Path] = None,
) -> int:
    """PreToolUse Edit/Write/Read/Bash — agent_boundary 강제.

    활성 sub-agent (live.json.active_agent) 가 있을 때만 검사. 메인 Claude 는
    governance Document Sync 게이트가 별도 보호하므로 본 훅 통과.
    """
    from harness.agent_boundary import (
        check_read_allowed,
        check_write_allowed,
        extract_bash_paths,
    )

    if stdin_data is None:
        try:
            raw = sys.stdin.read()
            stdin_data = json.loads(raw) if raw.strip() else {}
        except (json.JSONDecodeError, OSError):
            return 0

    if not isinstance(stdin_data, dict):
        return 0

    sid = _extract_sid(stdin_data)
    if not valid_session_id(sid):
        return 0

    live = read_live(sid, base_dir=base_dir) or {}
    active_agent = live.get("active_agent") or ""
    if not active_agent:
        return 0  # 메인 Claude — governance 가 보호.

    tool_name = stdin_data.get("tool_name", "") or ""
    tool_input = stdin_data.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        return 0

    cwd = Path.cwd()

    # boundary 검사 — 차단 시 즉시 return (trace 미기록 — 차단된 행동은 file-guard 가 stderr 에 별도 기록)
    if tool_name == "Read":
        fp = tool_input.get("file_path", "") or ""
        if fp:
            reason = check_read_allowed(active_agent, fp, cwd=cwd)
            if reason:
                print(f"[agent-boundary] {reason}", file=sys.stderr)
                return 1
    elif tool_name in ("Edit", "Write", "NotebookEdit"):
        fp = tool_input.get("file_path", "") or ""
        if fp:
            reason = check_write_allowed(active_agent, fp, cwd=cwd)
            if reason:
                print(f"[agent-boundary] {reason}", file=sys.stderr)
                return 1
    elif tool_name == "Bash":
        cmd = tool_input.get("command", "") or ""
        for fp in extract_bash_paths(cmd):
            reason = check_write_allowed(active_agent, fp, cwd=cwd)
            if reason:
                print(f"[agent-boundary][Bash] {reason}", file=sys.stderr)
                return 1

    # DCN-CHG-20260501-11 — sub 행동 trace append (rid 활성 시만)
    rid = _resolve_rid(sid, cc_pid, base_dir=base_dir)
    if rid:
        _append_trace_safe(
            sid,
            rid,
            {
                "phase": "pre",
                "agent": active_agent,
                "agent_id": stdin_data.get("agent_id", "") or "",
                "tool": tool_name,
                "input": _summarize_input(tool_name, tool_input),
            },
            base_dir=base_dir,
        )
    return 0


def handle_posttooluse_file_op(
    stdin_data: Optional[Dict[str, Any]] = None,
    cc_pid: Optional[int] = None,
    *,
    base_dir: Optional[Path] = None,
) -> int:
    """PostToolUse Edit/Write/Read/Bash — sub 행동 trace post append (DCN-CHG-20260501-11).

    활성 sub-agent 가 있을 때만 기록. 메인 Claude turn 은 noop.
    PostToolUse 는 차단 권한 X — 항상 exit 0.
    """
    if stdin_data is None:
        try:
            raw = sys.stdin.read()
            stdin_data = json.loads(raw) if raw.strip() else {}
        except (json.JSONDecodeError, OSError):
            return 0

    if not isinstance(stdin_data, dict):
        return 0

    sid = _extract_sid(stdin_data)
    if not valid_session_id(sid):
        return 0

    live = read_live(sid, base_dir=base_dir) or {}
    active_agent = live.get("active_agent") or ""
    if not active_agent:
        return 0

    rid = _resolve_rid(sid, cc_pid, base_dir=base_dir)
    if not rid:
        return 0

    tool_name = stdin_data.get("tool_name", "") or ""
    tool_response = stdin_data.get("tool_response") or {}
    if not isinstance(tool_response, dict):
        tool_response = {}

    entry: Dict[str, Any] = {
        "phase": "post",
        "agent": active_agent,
        "agent_id": stdin_data.get("agent_id", "") or "",
        "tool": tool_name,
    }

    # Bash — exit code + stdout size
    exit_code = tool_response.get("exit_code")
    if isinstance(exit_code, int):
        entry["exit"] = exit_code
    stdout = tool_response.get("stdout")
    if isinstance(stdout, str):
        entry["stdout_size"] = len(stdout)

    # 모든 도구 — error flag
    is_error = tool_response.get("is_error") or stdin_data.get("is_error")
    if is_error is True:
        entry["is_error"] = True

    _append_trace_safe(sid, rid, entry, base_dir=base_dir)
    return 0


def handle_posttooluse_agent(
    stdin_data: Optional[Dict[str, Any]] = None,
    cc_pid: Optional[int] = None,
    *,
    base_dir: Optional[Path] = None,
) -> int:
    """PostToolUse Agent — live.json.active_agent / active_mode 해제."""
    if stdin_data is None:
        try:
            raw = sys.stdin.read()
            stdin_data = json.loads(raw) if raw.strip() else {}
        except (json.JSONDecodeError, OSError):
            return 0

    if not isinstance(stdin_data, dict):
        return 0

    sid = _extract_sid(stdin_data)
    if not valid_session_id(sid):
        return 0

    try:
        update_live(sid, base_dir=base_dir, active_agent=None, active_mode=None)
    except (OSError, ValueError):
        return 0
    return 0


def _read_or_empty(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8") if path.exists() else ""
    except OSError:
        return ""


def _has_plan_ready(rd: Path) -> bool:
    mp = _read_or_empty(rd / "architect-MODULE_PLAN.md")
    if "READY_FOR_IMPL" in mp:
        return True
    lp = _read_or_empty(rd / "architect-LIGHT_PLAN.md")
    return "LIGHT_PLAN_READY" in lp


def _has_engineer_write(rd: Path) -> bool:
    return (rd / "engineer-IMPL.md").exists() or (rd / "engineer-POLISH.md").exists()


def _has_validator_pass(rd: Path) -> bool:
    cv = _read_or_empty(rd / "validator-CODE_VALIDATION.md")
    if "PASS" in cv:
        return True
    bv = _read_or_empty(rd / "validator-BUGFIX_VALIDATION.md")
    return "PASS" in bv


def _has_plan_review_pass(rd: Path) -> bool:
    return "PLAN_REVIEW_PASS" in _read_or_empty(rd / "plan-reviewer.md")


def _has_ux_flow_ready(rd: Path) -> bool:
    text = _read_or_empty(rd / "ux-architect.md")
    return "UX_FLOW_READY" in text or "UX_FLOW_PATCHED" in text


def _has_design_review_pass(rd: Path) -> bool:
    """validator-DESIGN_VALIDATION.md 안 DESIGN_REVIEW_PASS 확인 (DCN-CHG-20260430-05)."""
    return "DESIGN_REVIEW_PASS" in _read_or_empty(rd / "validator-DESIGN_VALIDATION.md")


# ── CLI 진입점 (bash 훅 → python -m harness.hooks <subcommand>) ─────


def _main(argv: Optional[list] = None) -> int:
    import argparse
    import os

    parser = argparse.ArgumentParser(
        prog="python3 -m harness.hooks",
        description="dcNess Claude Code 훅 진입점",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_ss = sub.add_parser("session-start", help="SessionStart 훅 처리")
    p_ss.add_argument("--cc-pid", type=int, default=None)

    p_ag = sub.add_parser("pretooluse-agent", help="PreToolUse Agent 훅 처리")
    p_ag.add_argument("--cc-pid", type=int, default=None)

    p_fo = sub.add_parser("pretooluse-file-op",
                          help="PreToolUse Edit/Write/Read/Bash agent_boundary 강제")
    p_fo.add_argument("--cc-pid", type=int, default=None)

    p_pa = sub.add_parser("posttooluse-agent",
                          help="PostToolUse Agent — live.json.active_agent 해제")
    p_pa.add_argument("--cc-pid", type=int, default=None)

    p_pf = sub.add_parser("posttooluse-file-op",
                          help="PostToolUse Edit/Write/Read/Bash — agent-trace post append")
    p_pf.add_argument("--cc-pid", type=int, default=None)

    args = parser.parse_args(argv)

    # cc_pid 미명시 시 PPID 사용 (bash 훅 의 PPID = CC main)
    cc_pid = args.cc_pid if args.cc_pid is not None else os.getppid()

    if args.cmd == "session-start":
        return handle_session_start(cc_pid=cc_pid)
    elif args.cmd == "pretooluse-agent":
        return handle_pretooluse_agent(cc_pid=cc_pid)
    elif args.cmd == "pretooluse-file-op":
        return handle_pretooluse_file_op(cc_pid=cc_pid)
    elif args.cmd == "posttooluse-agent":
        return handle_posttooluse_agent(cc_pid=cc_pid)
    elif args.cmd == "posttooluse-file-op":
        return handle_posttooluse_file_op(cc_pid=cc_pid)
    return 0


if __name__ == "__main__":
    sys.exit(_main())
