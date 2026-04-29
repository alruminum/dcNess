#!/bin/sh
# dcNess Claude Code PreToolUse hook (Bash matcher)
# 규칙 정의: docs/process/governance.md §2.7
#
# 입력: stdin JSON ({"tool_name":"Bash","tool_input":{"command":"..."}})
# 동작: command 에 `git commit` 포함 시 doc-sync 게이트 실행
# 종료 코드:
#   0 — 통과 (또는 git commit 미포함)
#   2 — 게이트 실패 (Claude Code PreToolUse 차단)

set -u

INPUT=$(cat)

# command 추출 (python3 가 없으면 grep fallback)
if command -v python3 >/dev/null 2>&1; then
  COMMAND=$(printf '%s' "$INPUT" | python3 -c 'import sys,json
try:
  d=json.load(sys.stdin); print(d.get("tool_input",{}).get("command",""))
except Exception:
  pass' 2>/dev/null || echo "")
else
  COMMAND=$(printf '%s' "$INPUT" | grep -o '"command"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"command"[[:space:]]*:[[:space:]]*"//; s/"$//')
fi

case "$COMMAND" in
  *"git commit"*)
    # 프로젝트 루트로 이동
    cd "${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null)}" 2>/dev/null || exit 0
    if [ -f scripts/check_document_sync.mjs ]; then
      if ! node scripts/check_document_sync.mjs >&2; then
        # PreToolUse block: exit 2
        exit 2
      fi
    fi
    ;;
esac
exit 0
