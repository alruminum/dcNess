#!/usr/bin/env bash
# dcNess catastrophic-gate 훅 — PreToolUse Agent 직전 §2.3 4룰 검사
#
# 트리거: Claude Code PreToolUse event, tool=Agent
# stdin: CC payload (sessionId + tool_input.{subagent_type, mode})
# 동작: harness/hooks.py 의 handle_pretooluse_agent 호출
#
# 반환:
#   exit 0: allow (CC 가 Agent 호출 진행)
#   exit 1: block (stderr 메시지 + CC 가 호출 거부)
#
# 강제 룰:
#   - §2.3.1 — pr-reviewer 직전 code-validator PASS 확인
#   - §2.3.3 — engineer 직전 module-architect READY 확인
#   - §2.3.6~§2.3.8 — impl-task-loop 3-commit 단계 (docs / tests / src) 확인

set -uo pipefail

# plugin root 를 PYTHONPATH 에 prepend — cross-project 시나리오 대응.
export PYTHONPATH="${CLAUDE_PLUGIN_ROOT:-.}:${PYTHONPATH:-}"

# 활성화 게이트 — 미활성 프로젝트는 즉시 통과 (Agent 호출 차단 0).
python3 -m harness.session_state is-active >/dev/null 2>&1 || exit 0

# bash 의 PPID = CC main process
CC_PID=$PPID

python3 -m harness.hooks pretooluse-agent --cc-pid "$CC_PID"
exit $?
