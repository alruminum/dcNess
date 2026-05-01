#!/usr/bin/env bash
# dcNess post-file-op-trace 훅 — PostToolUse Edit/Write/Read/Bash sub 행동 trace
# (DCN-CHG-20260501-11)
#
# 트리거: Claude Code PostToolUse event, tool=Edit|Write|NotebookEdit|Read|Bash
# stdin: CC payload (sessionId + tool_name + tool_input + tool_response)
# 동작: harness/hooks.py 의 handle_posttooluse_file_op 호출 — 활성 sub-agent 가
#       있을 때만 agent-trace.jsonl 에 post phase 1줄 append.
#
# 반환:
#   exit 0: 항상 (PostToolUse 는 차단 권한 X)
#
# 메인 Claude turn (active_agent 미설정) 은 noop. 비활성 프로젝트도 noop.

set -uo pipefail

export PYTHONPATH="${CLAUDE_PLUGIN_ROOT:-.}:${PYTHONPATH:-}"

# 활성화 게이트.
python3 -m harness.session_state is-active >/dev/null 2>&1 || exit 0

CC_PID=$PPID

python3 -m harness.hooks posttooluse-file-op --cc-pid "$CC_PID" 2>/dev/null || true
exit 0
