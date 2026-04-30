#!/usr/bin/env bash
# dcNess post-agent-clear 훅 — PostToolUse Agent: live.json.active_agent 해제
#
# 트리거: Claude Code PostToolUse event, tool=Agent
# stdin: CC payload (sessionId)
# 동작: harness/hooks.py 의 handle_posttooluse_agent 호출 — live.json 의
#       active_agent / active_mode 필드 clear (sub-agent 종료 후 메인 복귀).
#
# 반환:
#   exit 0: 항상 (PostToolUse 는 차단 권한 X)

set -uo pipefail

export PYTHONPATH="${CLAUDE_PLUGIN_ROOT:-.}:${PYTHONPATH:-}"

# 활성화 게이트.
python3 -m harness.session_state is-active >/dev/null 2>&1 || exit 0

CC_PID=$PPID

python3 -m harness.hooks posttooluse-agent --cc-pid "$CC_PID" 2>/dev/null || true
exit 0
