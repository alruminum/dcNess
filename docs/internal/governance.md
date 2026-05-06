# dcNess Governance

> **Scope**: 본 저장소(dcNess)의 모든 commit / PR / 작업자(사람·Claude Code·Codex·기타 에이전트)

## 0. 목적

본 문서는 dcNess 저장소의 작업 규칙 SSOT. 다른 파일은 본 문서를 *참조* 만 한다(재기술 금지).

**WHAT/WHY 추적**: GitHub이 자동으로 대체 — `git log` / PR description / issue thread / commit body.

## 1. 작업 규칙

### 1.1 Branch → PR → Merge (main 직접 commit 금지)

- 항상 branch 만들고 PR 통해 merge
- squash merge 금지 — 커밋별 히스토리 보존
- branch는 merge 후에도 삭제하지 않는다

### 1.2 main 직접 commit 차단

`scripts/hooks/pre-commit` 이 main 위 직접 commit 을 자동 차단한다.

```sh
cp scripts/hooks/pre-commit .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit
```

회귀 사례: Story 1.3 (#155) commit `2df1113` — 메인이 main 위에서 직접 commit. 차단 이후 재발 0.

### 1.3 git-naming 규칙

브랜치명·커밋 제목·PR 제목 형식: [`docs/plugin/git-naming-spec.md`](../plugin/git-naming-spec.md) (SSOT).

`scripts/hooks/commit-msg` + `.github/workflows/git-naming-validation.yml` 이 로컬/CI 양쪽 자동 검사.

### 1.4 Python Tests

`harness/` / `tests/` / `agents/` / `python-tests.yml` staged 시 pytest 자동 실행:

```sh
python3 -m unittest discover -s tests -v
```

pre-commit hook 이 자동 호출. 수동: `sh scripts/check_python_tests.sh`.

## 2. 강제 메커니즘

| 게이트 | 스크립트 | 적용 범위 |
|---|---|---|
| main-block | `scripts/hooks/pre-commit` 안 inline 검사 | 모든 commit |
| git-naming (로컬) | `scripts/hooks/commit-msg` | 모든 commit |
| git-naming (CI) | `.github/workflows/git-naming-validation.yml` | 모든 PR |
| pytest | `scripts/check_python_tests.sh` | harness/tests/agents/yml staged 시만 |

## 3. 참조

| 파일 | 역할 |
|---|---|
| [`docs/plugin/git-naming-spec.md`](../plugin/git-naming-spec.md) | 브랜치·커밋·PR 네이밍 규칙 SSOT |
| [`scripts/hooks/pre-commit`](../../scripts/hooks/pre-commit) | main-block + pytest 게이트 |
| [`scripts/hooks/commit-msg`](../../scripts/hooks/commit-msg) | git-naming 로컬 게이트 |
| [`scripts/check_python_tests.sh`](../../scripts/check_python_tests.sh) | pytest pre-commit 게이트 |
| [`PROGRESS.md`](../../PROGRESS.md) | 현재 상태·TODO·Blockers |
| [`docs/archive/`](../archive/) | 폐기된 거버넌스 문서 보존 (read-only) |

## 4. 역사 자료

Task-ID 시스템 / WHAT-WHY 로그 / Document Sync 게이트는 2026-05-06 폐기 (이슈 #182).
관련 문서: `docs/archive/document_update_record.md` / `docs/archive/change_rationale_history.md`.
