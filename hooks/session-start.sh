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

# DCN-CHG-20260430-26 (신설), DCN-CHG-20260430-40 (schema fix + 압축),
# DCN-CHG-20260501-17 (lazy-load 최적화), DCN-CHG-20260502-01 (blocking gate 강화):
# dcness 활성 프로젝트 매 세션 SessionStart 시 SSOT read 의무 directive 를
# system-reminder 로 inject.
#
# DCN-CHG-20260502-01 변경: 단순 "지금 읽어라" 지시 → BLOCKING 게이트 3원칙 적용.
#   1. "텍스트 출력 금지" 조건 — 읽기 전 출력 자체를 막는 언어
#   2. 검증 토큰 — 첫 응답 첫 줄에 토큰 의무 출력 (유저 즉시 확인 가능)
#   3. 예외 없음 명시 — "인사도 예외 없음" 패턴 매칭 차단
#
# JSON schema:
#   {"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": "..."}}
# Read 도구는 절대 경로만 허용 — CLAUDE_PROJECT_DIR 로 절대 경로 구성.
PROJ="${CLAUDE_PROJECT_DIR:-$(pwd)}"
GUIDELINES_PATH="${PROJ}/docs/plugin/skill-guidelines.md"

python3 -c "
import json, sys
guidelines_path = sys.argv[1]
msg = '''## [BLOCKING GATE] dcness 세션 시작 강제

**유저의 첫 메시지 종류에 관계없이 — 인사·잡담·질문·작업 요청 전부 포함 —**
**첫 텍스트를 출력하기 전에 아래 두 단계를 반드시 완료한다.**

---

### STEP 1: 파일 읽기 [스킵 불가 / 예외 없음]

Read 도구로 다음 파일을 *지금 바로* 호출한다 (절대 경로):
  Read(\"''' + guidelines_path + '''\")

- 이 도구 호출 완료 전까지 텍스트 출력 금지.
- \"이미 알고 있다\" → 예외 아님. 항상 다시 읽는다.
- 유저가 \"안녕\" / \"hi\" / \"hello\" / 짧은 질문 → 예외 아님. 읽고 나서 응답.

### STEP 2: 확인 토큰 출력 [스킵 불가]

읽은 후 첫 응답의 **첫 줄**에 반드시 다음 토큰을 출력한다:
  [skill-guidelines 로드 완료 — §11 감시자 Hat 장착]

이 토큰 없이 응답 = 즉시 룰 위반 (유저가 즉시 확인 가능).

---

**나머지 loop 실행 docs (loop-procedure / orchestration / handoff-matrix) 는 지금 읽지 말 것.**
각 skill 의 ## 사전 read 섹션이 진입 시 직접 경로를 안내한다.
'''
print(json.dumps({
    'hookSpecificOutput': {
        'hookEventName': 'SessionStart',
        'additionalContext': msg,
    }
}))
" "$GUIDELINES_PATH" 2>/dev/null

# 모든 실패는 silent
exit 0
