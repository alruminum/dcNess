#!/usr/bin/env bash
# dcNess SessionStart 훅 — sid 추출 + by-pid 작성 + live.json 초기화 + 슬림 inject
#
# 트리거: Claude Code SessionStart event
# stdin: CC payload (sessionId 포함)
# 동작: harness/hooks.py 의 handle_session_start 호출 + 슬림 본문 inject
#
# 실패 시 silent (exit 0) — CC 동작 방해 안 함.

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

# 슬림 inject — dcness-rules.md 폐기 (PR-3). 매 세션 system-reminder 로 본문 자동 노출.
# 외부 plug-in 사용자가 매 세션 강제 영역 + 메인 Claude 필수 + 진입 매트릭스 인지.
python3 -c "
import json
msg = '''## [dcness 활성 환경]

첫 응답 첫 줄에 토큰 \`[dcness 활성 확인]\` 출력 의무 (사용자 즉시 룰 위반 확인 가능).

### 강제 영역 (코드 hook 차단)
- **작업 순서**: agent 시퀀스 + retry 정책 — catastrophic 3 룰 = \`docs/plugin/orchestration.md\` §2.1
- **접근 영역**: file 경계 (ALLOW/READ_DENY) + 인프라 차단 (DCNESS_INFRA_PATTERNS) = \`docs/plugin/handoff-matrix.md\` §4
- 그 외 = agent 자율 (출력 형식 / handoff / preamble / marker 강제 X)

### 메인 Claude 필수 (dcness 특화)
- **채널별 형식 분기**: 사용자 chat = 평문 백틱 \`경로\` / 본문(docs / agents / commands / 이슈) = 마크다운 링크. 혼용 시 cmd-click 깨짐
- **행동지침 md 300줄 cap** (orchestration.md 만 500줄 예외) — 대상: \`agents/**\` / \`commands/*.md\` / \`docs/plugin/*.md\`
- **Step 7 회고 → 메모리 candidate emit 의무**: caveat 또는 review report 의 waste finding 발견 시 *메모리 candidate* 양식 emit (없으면 \"없음\" 1줄). prose 본문만 적고 끝내면 다음 세션 회귀.

### 안티패턴 (피하기)
- 룰이 룰을 부르는 reactive cycle — 신규 룰 추가 전 기존 룰 제거 가능성 먼저 검토
- 강제 vs 권고 혼동 — catastrophic 만 block, 그 외 = 측정 + 경고 + 사용자 개입
- 에이전트 자율성 침해 — agent prompt 안 강제 형식 박기 금지

### 작업 진입 매트릭스 (lazy read)
| 상황 | 읽어야 할 문서 |
|---|---|
| 루프 진입 / 시퀀스 / catastrophic 룰 | \`docs/plugin/orchestration.md\` §2 + §4 |
| Step 0~8 mechanics / echo 5~12줄 / REDO 분류 | \`docs/plugin/loop-procedure.md\` |
| agent 결론 → 다음 agent / retry / 권한 | \`docs/plugin/handoff-matrix.md\` |
| hook 시점 / 차단 동작 | \`docs/plugin/hooks.md\` |
| 이슈 lifecycle / PR 트레일러 | \`docs/plugin/issue-lifecycle.md\` |
| 브랜치/커밋/PR 네이밍 | \`docs/plugin/git-naming-spec.md\` |

skill 트리거 시 해당 skill 파일의 ## 사전 read 섹션이 정확한 경로 안내.
'''
print(json.dumps({
    'hookSpecificOutput': {
        'hookEventName': 'SessionStart',
        'additionalContext': msg,
    }
}))
" 2>/dev/null

# 모든 실패는 silent
exit 0
