#!/usr/bin/env bash
# setup_labels.sh — dcNess 정적 GitHub 레이블 생성 (BugFix / UI / Docs)
# 동적 레이블 (V0N / EPIC0N / Story0N) 은 agent 가 이슈 생성 시 자동 생성.
#
# 사용:
#   bash scripts/setup_labels.sh [<owner/repo>]
#   (인자 없으면 gh repo view 로 자동 감지)
set -euo pipefail

REPO="${1:-}"
if [ -z "$REPO" ]; then
  REPO="$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null || echo '')"
fi
if [ -z "$REPO" ]; then
  echo "[setup_labels] REPO 미지정 — 인자로 전달 또는 gh 로그인 후 재실행" >&2
  exit 1
fi

echo "[setup_labels] target: $REPO"

_upsert_label() {
  local name="$1" color="$2" description="$3"
  if gh label create "$name" --color "$color" --description "$description" --repo "$REPO" 2>/dev/null; then
    echo "  created: $name"
  else
    gh label edit "$name" --color "$color" --description "$description" --repo "$REPO" 2>/dev/null && \
      echo "  updated: $name" || echo "  skip: $name (no change or error)"
  fi
}

_upsert_label "BugFix" "d73a4a" "버그 수정 — qa 분류 FUNCTIONAL_BUG"
_upsert_label "UI"     "0075ca" "UI/Design 이슈 — designer 생성"
_upsert_label "Docs"   "cfd3d7" "문서 변경"

echo "[setup_labels] 완료 — BugFix / UI / Docs"
