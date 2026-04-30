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

# DCN-CHG-20260430-26 (신설), DCN-CHG-20260430-40 (schema fix + 압축):
# dcness 활성 프로젝트 매 세션 SessionStart 시 SSOT read 의무 directive 를
# system-reminder 로 inject.
#
# 본문 inject 가 아닌 *지시* 만 (~1K) — CC additionalContext 10K cap 회피 +
# CLAUDE.md 와 동일 강제력 ("지금 즉시 read 의무"). 메인 Claude 가 read 후
# 컨텍스트 안에 SSOT 본문 자체 적재.
#
# JSON schema (정확한 CC 형식):
#   {"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": "..."}}
# top-level 의 {continue, additionalContext} 는 CC 가 honor X (DCN-30-26 bug,
# DCN-30-40 fix). 자장 jajang 세션에서 inject 0회 검증 후 발견.
python3 -c "
import json
msg = '''## dcness Guidelines (DCN-30-40 자동 로드)

**[필수 — 지금 즉시 read 의무]**

본 프로젝트는 dcness plugin 활성. 글로벌 \`~/.claude/CLAUDE.md\` 와 *동일 레벨 강제*. 다음 SSOT 본 메시지 수신 *직후* read:

1. **\`docs/process/dcness-guidelines.md\`** — 가시성 / Step 기록 / yolo / AMBIGUOUS / worktree / 결과 출력 / 권한 요청 / Karpathy / **§12 self-verify 원칙** / 행동지침 md 300줄 cap
2. **\`docs/loop-procedure.md\`** — Step 0~8 mechanics (worktree → begin-run → TaskCreate → begin-step → Agent → end-step → finalize-run --auto-review)
3. **\`docs/loop-catalog.md\`** — 8 loop × 풀스펙 (entry / task_list / advance / clean_enum / branch_prefix / Step 별 allowed_enums / 분기 / sub_cycles)
4. **\`docs/orchestration.md\`** §2~§3 — 시퀀스 + 진입 경로 mini-graph
5. **\`docs/handoff-matrix.md\`** — agent 결정표 / Retry / Escalate / 접근 권한

**룰 의무 적용 범위**: 모든 dcness skill 진행 (\`/qa\`, \`/quick\`, \`/product-plan\`, \`/impl\`, \`/impl-loop\`, \`/run-review\`) + skill 외 직접 발화 (orchestration §3 보고 동적 구성).

**핵심 강제 룰 — read 전이라도 즉시 적용**:
- 매 Agent 호출 후 prose 5~12줄 의무 echo (가시성 §1)
- begin-step / end-step 1:1 의무 (§2 Step 기록)
- 추측 금지 + 실측 후 단언 (§12 self-verify, 글로벌 제1룰 정합)
- finalize-run 시 \`--auto-review\` flag 의무 (loop-procedure §5.1)

**미인지 진행 = 룰 위반**. read 없이 작업 금지.
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
