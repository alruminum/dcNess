#!/bin/bash
# dcness pr-finalize — PR 머지 + CI 대기 + main sync 자동
#
# 한 명령으로 머지 절차 끝:
#   1. gh pr merge --auto --merge (auto-merge 토글 ON)
#   2. gh pr checks --watch (CI 결과 대기)
#   3. auto-merge 완료 대기 (GitHub 백그라운드 lag)
#   4. git checkout main + git pull
#
# 사용:
#   pr-finalize.sh                # current branch 의 open PR 자동 검출
#   pr-finalize.sh <PR_NUMBER>    # 명시 PR 번호
#
# 안전:
#   - 현재 working tree dirty 면 abort (git pull 충돌 회피)
#   - CI FAIL 시 main sync skip + 에러 코드
#   - 머지 안 됐으면 main sync skip + 사용자 안내

set -e

PR="$1"

# PR 번호 자동 검출 — current branch
if [ -z "$PR" ]; then
  BRANCH=$(git rev-parse --abbrev-ref HEAD)
  if [ "$BRANCH" = "main" ]; then
    echo "[pr-finalize] ERROR: current branch = main. PR 번호 인자 박거나 feature branch 에서 호출" >&2
    exit 1
  fi
  PR=$(gh pr list --head "$BRANCH" --json number -q '.[0].number' 2>/dev/null)
  if [ -z "$PR" ] || [ "$PR" = "null" ]; then
    echo "[pr-finalize] ERROR: '$BRANCH' branch 의 open PR 없음. PR 먼저 생성 (gh pr create)" >&2
    exit 1
  fi
  echo "[pr-finalize] current branch '$BRANCH' → PR #$PR 자동 검출"
fi

# working tree dirty check
if [ -n "$(git status --porcelain)" ]; then
  echo "[pr-finalize] WARN: working tree dirty — main sync 시 충돌 위험" >&2
  git status --short >&2
  echo "[pr-finalize] 계속 진행 (auto-merge 만, main sync skip) Y/n? "
  read -r reply
  if [ "$reply" != "Y" ] && [ "$reply" != "y" ]; then
    exit 1
  fi
  SKIP_SYNC=true
fi

# Step 1: auto-merge 토글
echo "[pr-finalize] PR #$PR — auto-merge 토글 ON"
gh pr merge "$PR" --auto --merge

# Step 2: CI 결과 대기
echo "[pr-finalize] CI 결과 대기 (gh pr checks --watch)"
if ! gh pr checks "$PR" --watch; then
  echo "[pr-finalize] ERROR: CI FAIL — 머지 안 됨. main sync skip" >&2
  exit 1
fi

# Step 3: auto-merge 완료 대기 (GitHub 백그라운드)
echo "[pr-finalize] auto-merge 완료 대기"
STATE=""
for i in 1 2 3 4 5 6 7 8; do
  STATE=$(gh pr view "$PR" --json state -q .state 2>/dev/null)
  if [ "$STATE" = "MERGED" ]; then
    break
  fi
  sleep 3
done

if [ "$STATE" != "MERGED" ]; then
  echo "[pr-finalize] WARN: PR #$PR 머지 안 됐음 (state=$STATE). branch protection 미충족 또는 review 필요 가능. 수동 확인:" >&2
  echo "  gh pr view $PR" >&2
  exit 1
fi

# Step 4: main sync
if [ "${SKIP_SYNC:-}" = "true" ]; then
  echo "[pr-finalize] main sync skip (working tree dirty)"
  exit 0
fi

echo "[pr-finalize] main sync"
git checkout main
git pull --quiet

echo "[pr-finalize] 완료 — PR #$PR 머지 + main 동기화"
