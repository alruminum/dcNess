#!/usr/bin/env bash
# dcNess subagent-stop-clear 훅 — SubagentStop (issue #598)
#
# 트리거: Claude Code SubagentStop event (sub-agent 종료 직발)
# stdin: CC payload (sessionId, agent_id, agent_type 동반)
# 동작: harness/hooks.py 의 handle_subagent_stop 호출
#   - live.json.active_agent / active_mode 신뢰 clear (PostToolUse Agent 매칭보다
#     신뢰도 높은 시점). match-guard 로 동시 sub 슬롯 오클리어 방지.
#
# 반환:
#   exit 0: 항상 (SubagentStop 을 차단하지 않음 — clear 만 수행).
#   stderr: /tmp/dcness-hook-stderr.log 보존 (디버그용).

set -uo pipefail

export PYTHONPATH="${CLAUDE_PLUGIN_ROOT:-.}:${PYTHONPATH:-}"

# 활성화 게이트 — 현재 프로젝트가 dcness whitelist 에 없으면 pass-through.
python3 -m harness.session_state is-active >/dev/null 2>&1 || exit 0

CC_PID=$PPID

python3 -m harness.hooks subagent-stop --cc-pid "$CC_PID" 2>>/tmp/dcness-hook-stderr.log || true
exit 0
