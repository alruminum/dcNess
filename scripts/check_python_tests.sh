#!/bin/sh
# dcNess pytest pre-commit gate (paths 분기)
# 규칙 정의: docs/process/governance.md §2.7
#
# 동작:
#   1. staged 파일 목록 추출 (git diff --cached --name-only)
#   2. harness/ | tests/ | agents/ | .github/workflows/python-tests.yml 매칭 시만 실행
#   3. python3 -m unittest discover -s tests
#
# 종료 코드:
#   0 — 통과 (or 매칭 0)
#   1 — 테스트 실패
#
# 우회: git commit --no-verify (룰 위반).

set -u

# CI 환경 (GITHUB_ACTIONS) 에선 skip — workflow 가 별도 실행
if [ -n "${GITHUB_ACTIONS:-}" ]; then
  exit 0
fi

# staged 파일 매칭 검사
CHANGED=$(git diff --cached --name-only 2>/dev/null)
if [ -z "$CHANGED" ]; then
  exit 0
fi

if ! printf '%s\n' "$CHANGED" | grep -qE '^(harness/|tests/|agents/|\.github/workflows/python-tests\.yml$)'; then
  # 미매칭 — skip
  exit 0
fi

echo "[pytest-gate] harness/tests/agents 변경 감지 — 단위 테스트 실행"
if ! python3 -m unittest discover -s tests >&2; then
  echo "[pytest-gate] FAIL — 단위 테스트 회귀. fix 후 재커밋. (우회: --no-verify, 룰 위반)" >&2
  exit 1
fi
echo "[pytest-gate] PASS"
exit 0
