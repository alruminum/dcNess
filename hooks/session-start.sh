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

# plugin root 를 PYTHONPATH 에 prepend — cwd 에 harness/ 없는 cross-project 시나리오 대응.
# CLAUDE_PLUGIN_ROOT 는 CC 가 plugin hook 실행 시 자동 설정.
export PYTHONPATH="${CLAUDE_PLUGIN_ROOT:-.}:${PYTHONPATH:-}"

# 활성화 게이트 — 현재 프로젝트가 dcness whitelist 에 없으면 즉시 pass-through.
# /init-dcness 로 활성화. 미활성 프로젝트에선 hook 자체가 no-op.
python3 -m harness.session_state is-active >/dev/null 2>&1 || exit 0

# bash 의 PPID = CC main process
CC_PID=$PPID

# Python 으로 stdin 처리 + 핸들러 호출 (silent — stdout 안 씀)
python3 -m harness.hooks session-start --cc-pid "$CC_PID"

# DCN-CHG-20260430-26: dcness guidelines 를 system-reminder 로 inject.
# 활성 프로젝트 한정 (위 is-active 게이트 통과 후만 실행). plugin 비활성 X.
# CC SessionStart 훅 출력 = JSON {continue, additionalContext} → 매 세션 자동 인지.
GUIDELINES="${CLAUDE_PLUGIN_ROOT:-.}/docs/process/dcness-guidelines.md"
if [ -f "$GUIDELINES" ]; then
    python3 -c "
import json
try:
    with open('$GUIDELINES', encoding='utf-8') as f:
        content = f.read()
    msg = (
        '## dcness Guidelines (자동 로드 — DCN-30-26)\n\n'
        '**[필수 인지]** 본 프로젝트는 dcness plugin 활성. 아래 룰 모든 dcness skill 진행 시 의무 적용.\n\n'
        '---\n\n' + content
    )
    print(json.dumps({'continue': True, 'additionalContext': msg}))
except Exception:
    pass
" 2>/dev/null
fi

# 모든 실패는 silent
exit 0
