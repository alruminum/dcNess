#!/usr/bin/env bash
# dcNess catastrophic-gate 훅 — PreToolUse Agent 직전 §2.1 catastrophic 룰 검사
#
# 트리거: Claude Code PreToolUse event, tool=Agent
# stdin: CC payload (sessionId + tool_input.{subagent_type, mode})
# 동작: harness/hooks.py 의 handle_pretooluse_agent 호출
#
# 반환:
#   exit 0: allow (CC 가 Agent 호출 진행)
#   exit 2: block (stderr 메시지 + CC 가 호출 거부)
#          — CC docs: PreToolUse 는 exit 2 라야 차단 + stderr 가 Claude 에 피드백.
#            exit 1 = non-blocking error → 도구 그대로 진행 (차단 안 됨).
#
# 강제 룰:
#   - §2.1.1 — pr-reviewer 직전 code-validator PASS 확인
#   - §2.1.3 — engineer 직전 module-architect PASS 확인
#   - §2.1.5 — architect-loop 안 module-architect × K 첫 호출 직전 architecture-validator PASS

set -uo pipefail

# plugin root 를 PYTHONPATH 에 prepend — cross-project 시나리오 대응.
export PYTHONPATH="${CLAUDE_PLUGIN_ROOT:-.}:${PYTHONPATH:-}"

# 활성화 게이트 — 미활성 프로젝트는 즉시 통과 + suppressOutput.
if ! python3 -m harness.session_state is-active >/dev/null 2>&1; then
  echo '{"suppressOutput": true, "hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "allow"}}'
  exit 0
fi

# bash 의 PPID = CC main process
CC_PID=$PPID

python3 -m harness.hooks pretooluse-agent --cc-pid "$CC_PID"
RC=$?

# #404 — 정상 통과 시 suppressOutput: true 써서 transcript attachment 숨김 시도.
if [ "$RC" = "0" ]; then
  echo '{"suppressOutput": true, "hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "allow"}}'
  exit 0
fi
# 정책 위반 (handler 가 정확히 1 반환) → exit 2 라야 CC 가 차단 + stderr 를 Claude 에 피드백.
# (exit 1 = non-blocking error → 도구 그대로 진행하므로 차단 효과 없음 — 본 hook 의 핵심 fix.)
# 그 외 nonzero (인터프리터 오류 등) → fail-open (exit 0) 으로 hook 버그발 과차단 회피.
[ "$RC" = "1" ] && exit 2
exit 0
