#!/bin/bash
set -euo pipefail

# sync_local_plugin.sh — dcNess repo → 로컬 plugin 경로 동기화 (테스트용)
# sync_release.sh 와 동일한 EXCLUDE_PATHS 사용.

REPO_ROOT=$(git rev-parse --show-toplevel)
DEST="$HOME/.claude/plugins/marketplaces/dcness"

rsync -a --delete \
    --exclude=docs/internal \
    --exclude=docs/archive \
    --exclude=tests \
    --exclude=PROGRESS.md \
    --exclude=CLAUDE.md \
    --exclude=scripts/sync_release.sh \
    --exclude=scripts/sync_local_plugin.sh \
    --exclude=.github/workflows/python-tests.yml \
    --exclude=.github/workflows/release-sync.yml \
    --exclude=.claude \
    "$REPO_ROOT/" "$DEST/"

echo "✔ synced to $DEST"
