#!/usr/bin/env bash
# dcness TDD Guard Hook — PreToolUse[Edit|Write|NotebookEdit]
# agent 가 src 파일 작성/편집 시도 시 매칭 test 파일 존재 검사.
# 없으면 deny + 한국어 안내. 진짜 TDD 강제 (코드 작성 *전* 테스트 먼저).
#
# 영감: jha0313/codex-live-demo/.codex/hooks/tdd-guard.sh
# 차이: dcness 환경 (Claude Code plug-in hook) 매처 정합 + 한국어 메시지 보강
#
# 시점: agent Edit/Write tool_use 직전. tool_input.file_path 추출 + 검증.
# 차단 시 plug-in 표준 hookSpecificOutput JSON 으로 deny.

set -u

INPUT=$(cat)
[ -z "$INPUT" ] && exit 0

PROJECT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)

deny() {
  local reason="$1"
  python3 - "$reason" <<'PY'
import json
import sys
print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": sys.argv[1],
    }
}, ensure_ascii=False))
PY
}

# tool_input.file_path 추출
FILE_PATH=$(python3 - "$INPUT" <<'PY'
import json, sys
try:
    payload = json.loads(sys.argv[1])
except Exception:
    sys.exit(0)
ti = payload.get("tool_input") or {}
for key in ("file_path", "path", "filename"):
    v = ti.get(key)
    if isinstance(v, str) and v:
        print(v)
        sys.exit(0)
PY
)

[ -z "$FILE_PATH" ] && exit 0

# 자동 skip — test 파일 자체
case "$FILE_PATH" in
  *test*|*spec*|*.test.*|*.spec.*|*__tests__*) exit 0 ;;
esac

# 자동 skip — 설정 / 비-코드 / 타입 / Next.js 특수
case "$FILE_PATH" in
  *.json|*.css|*.scss|*.md|*.yml|*.yaml|*.env*|*.config.*|*tailwind*|*postcss*|*next.config*|*tsconfig*) exit 0 ;;
  */types/*|*/types.ts|*/types.d.ts|*.d.ts) exit 0 ;;
  */layout.tsx|*/layout.ts|*/page.tsx|*/page.ts|*/loading.tsx|*/error.tsx|*/not-found.tsx|*/globals.css) exit 0 ;;
esac

# TS/JS 한정 — 그 외 silent skip
case "$FILE_PATH" in
  *.ts|*.tsx|*.js|*.jsx) ;;
  *) exit 0 ;;
esac

# 매칭 test 파일 존재 검사
has_test_for() {
  local fp="$1"
  local dir base parent ext
  dir=$(dirname "$fp")
  base=$(basename "$fp" | sed -E 's/\.(ts|tsx|js|jsx)$//')
  parent=$(dirname "$dir")
  for ext in ts tsx js jsx; do
    [ -f "${dir}/${base}.test.${ext}" ] && return 0
    [ -f "${dir}/${base}.spec.${ext}" ] && return 0
    [ -f "${dir}/__tests__/${base}.test.${ext}" ] && return 0
    [ -f "${dir}/__tests__/${base}.spec.${ext}" ] && return 0
    [ -f "${parent}/__tests__/${base}.test.${ext}" ] && return 0
    [ -f "${parent}/__tests__/${base}.spec.${ext}" ] && return 0
    [ -f "${PROJECT_ROOT}/src/__tests__/${base}.test.${ext}" ] && return 0
    [ -f "${PROJECT_ROOT}/src/__tests__/${base}.spec.${ext}" ] && return 0
  done
  return 1
}

if ! has_test_for "$FILE_PATH"; then
  BASE=$(basename "$FILE_PATH" | sed -E 's/\.(ts|tsx|js|jsx)$//')
  deny "TDD GUARD: '${BASE}' 에 대한 테스트 파일이 존재하지 않습니다. 구현 코드를 작성하기 *전*에 테스트를 먼저 작성하세요.

예: ${BASE}.test.ts 또는 __tests__/${BASE}.test.ts

이미 테스트 있는데 인식 안 됨 — dcness 가 검사하는 8 location:
  <dir>/<name>.{test,spec}.{ts,tsx,js,jsx}
  <dir>/__tests__/<name>.{test,spec}.{ts,tsx,js,jsx}
  <parent>/__tests__/<name>.{test,spec}.{ts,tsx,js,jsx}
  <root>/src/__tests__/<name>.{test,spec}.{ts,tsx,js,jsx}"
  exit 0
fi

exit 0
