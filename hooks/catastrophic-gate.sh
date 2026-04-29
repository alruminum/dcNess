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
#   - HARNESS_ONLY_AGENTS (engineer, validator-PLAN/CODE/BUGFIX_VALIDATION) — run 미시작 시 차단
#   - §2.3.1 — pr-reviewer 직전 validator (CODE/BUGFIX) PASS 확인
#   - §2.3.3 — engineer 직전 architect plan READY 확인
#   - §2.3.4 — architect SD/TD 직전 plan-reviewer + ux-architect 검토 확인

set -uo pipefail

# bash 의 PPID = CC main process
CC_PID=$PPID

python3 -m harness.hooks pretooluse-agent --cc-pid "$CC_PID"
exit $?
