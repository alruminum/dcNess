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

# #404 — 정상 통과 시 suppressOutput: true 박아 transcript attachment 숨김 시도.
allow() {
  echo '{"suppressOutput": true, "hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "allow"}}'
  exit 0
}

INPUT=$(cat)
[ -z "$INPUT" ] && allow

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

[ -z "$FILE_PATH" ] && allow

# 자동 skip — test 파일 자체
case "$FILE_PATH" in
  *test*|*spec*|*.test.*|*.spec.*|*__tests__*) allow ;;
esac

# 자동 skip — 설정 / 비-코드 / 타입 / Next.js 특수
case "$FILE_PATH" in
  *.json|*.css|*.scss|*.md|*.yml|*.yaml|*.env*|*.config.*|*tailwind*|*postcss*|*next.config*|*tsconfig*) allow ;;
  */types/*|*/types.ts|*/types.d.ts|*.d.ts) allow ;;
  */layout.tsx|*/layout.ts|*/page.tsx|*/page.ts|*/loading.tsx|*/error.tsx|*/not-found.tsx|*/globals.css) allow ;;
esac

# 자동 skip — plug-in 시드 boilerplate / 디자인 시안 폴더
# templates/ = dcness self repo 의 사용자 프로젝트 배포용 시드 (cp 후 활성화)
# design-variants/ = 활성화 프로젝트의 디자인 시안 폴더 (UI prototype, production 테스트 의무 X)
case "$FILE_PATH" in
  */templates/*|*/design-variants/*) allow ;;
esac

# 자동 skip — entry-file path heuristic (#423)
# registerRootComponent / AppRegistry.registerComponent 같은 entry 정의 파일은
# 비즈니스 로직 없는 boilerplate. test 의무 X. 컨벤션 path 만 좁게 매치.
# - */App.{ts,tsx,js,jsx}      = RN / Expo entry shell
# - */_layout.{ts,tsx,js,jsx}  = expo-router layout (Next.js layout.tsx 는 라인 67에서 별도 cover)
# - */apps/*/index.{ts,tsx,js,jsx} = monorepo apps/<name>/ entry (일반 index.* 는 너무 광범위라 제외)
# - */src/main.{ts,tsx,js,jsx}     = Vue/Vite main entry
case "$FILE_PATH" in
  */App.ts|*/App.tsx|*/App.js|*/App.jsx) allow ;;
  */_layout.ts|*/_layout.tsx|*/_layout.js|*/_layout.jsx) allow ;;
  */apps/*/index.ts|*/apps/*/index.tsx|*/apps/*/index.js|*/apps/*/index.jsx) allow ;;
  */src/main.ts|*/src/main.tsx|*/src/main.js|*/src/main.jsx) allow ;;
esac

# TS/JS 한정 — 그 외 silent skip
case "$FILE_PATH" in
  *.ts|*.tsx|*.js|*.jsx) ;;
  *) allow ;;
esac

# 자동 skip — 파일 내용 시그니처 매치 (#423)
# entry-file 가 path heuristic 못 잡은 위치에 있어도 내용으로 detection.
# 단 Edit 케이스만 cover (파일 이미 존재). 최초 Write 시는 path heuristic 의존.
if [ -f "$FILE_PATH" ]; then
  if grep -qE 'registerRootComponent\(|AppRegistry\.registerComponent\(' "$FILE_PATH" 2>/dev/null; then
    allow
  fi
fi

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

allow
