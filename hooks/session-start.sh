#!/usr/bin/env bash
# dcNess SessionStart 훅 — sid 추출 + by-pid 작성 + live.json 초기화
#
# 트리거: Claude Code SessionStart event
# stdin: CC payload (sessionId 포함)
# 동작: harness/hooks.py 의 handle_session_start 호출
#
# 실패 시 silent (exit 0) — CC 동작 방해 안 함.
#
# 등록: .claude/settings.json 의 hooks.SessionStart 에 본 스크립트 경로 박음.
#       plugin 활성 시 자동 등록되도록 .claude-plugin/plugin.json 에서도 명시.

set -uo pipefail

# bash 의 PPID = CC main process
CC_PID=$PPID

# Python 으로 stdin 처리 + 핸들러 호출
python3 -m harness.hooks session-start --cc-pid "$CC_PID"

# 모든 실패는 silent
exit 0
