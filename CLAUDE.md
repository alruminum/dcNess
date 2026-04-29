# CLAUDE.md — dcNess 프로젝트 작업 지침

> 본 파일은 메인 Claude (Claude Code) 가 dcNess 저장소에서 작업할 때의 지침이다.
> 거버넌스 규칙은 [`docs/process/governance.md`](docs/process/governance.md) (SSOT) 에 있다 — 본 파일은 *재기술하지 않고 절차·링크만 박는다*.

## 0. 프로젝트 정체성

- **목적**: RWHarness fork-and-refactor — status-JSON-mutate 결정론 + 4 기둥 정합 + 함정 회피 5원칙 (`docs/status-json-mutate-pattern.md` §1~§2.5).
- **모드**: **메인 Claude 직접 작업** (`status-json-mutate-pattern.md` §10 / §11.4 정합).
  - architect / validator / engineer 위임 강제 **없음**.
  - RWHarness 가드 미적용 환경. **단** Document Sync 거버넌스만 강제.
  - 글로벌 `~/.claude/CLAUDE.md` 의 RWHarness 위임 룰(에이전트 분기 / 인프라 프로젝트 분기)은 본 프로젝트에 **미적용**. 본 파일이 우선한다.

## 1. 작업 절차 (모든 변경 공통)

> SSOT: [`docs/process/governance.md`](docs/process/governance.md) §2.3.

1. **Task-ID 발급**: `DCN-CHG-YYYYMMDD-NN` (governance §2.1).
2. **변경 분류**: governance §2.2 표에서 Change-Type 토큰 결정.
3. **수정 작업**.
4. **완료 직전 동반 갱신**:
   - `docs/process/document_update_record.md` (모든 변경)
   - `docs/process/change_rationale_history.md` (spec / agent / harness / hooks / ci 변경 시)
   - `PROGRESS.md` (harness / hooks / ci 변경 시)
   - 카테고리별 deliverable (governance §2.6)
5. **commit 직전**: `node scripts/check_document_sync.mjs` 통과 확인.
   - 자동: Claude Code PreToolUse hook (`scripts/hooks/cc-pre-commit.sh`) + git pre-commit hook 이 동시 차단.
6. **branch → PR → squash merge** (직접 `main` push 금지).

## 2. 거버넌스 핵심 (전체 룰은 SSOT 참조)

- **Task-ID 형식**: `DCN-CHG-YYYYMMDD-NN` (governance §2.1)
- **Change-Type 7종**: `spec` / `agent` / `harness` / `hooks` / `ci` / `test` / `docs-only` (governance §2.2)
- **예외**: `Document-Exception:` 토큰 (governance §2.4 — *현재 diff 추가 라인만 유효*, 과거 누적 무효)
- **3중 강제**: git pre-commit hook + Claude Code PreToolUse hook + AGENTS.md (governance §2.7)

> ⚠️ **금지**: `--no-verify` 등 hook 우회. 룰 재기술. Task-ID 없는 commit. 과거 머지된 Exception 으로 현재 위반 회피.

## 3. 문서 지도

| 파일 | 역할 |
|---|---|
| [`docs/process/governance.md`](docs/process/governance.md) | **SSOT** — 모든 거버넌스 룰의 단일 출처 |
| [`docs/process/document_update_record.md`](docs/process/document_update_record.md) | WHAT 로그 (Task-ID 별 변경 파일) |
| [`docs/process/change_rationale_history.md`](docs/process/change_rationale_history.md) | WHY 로그 (Task-ID 별 동기·대안·결정·후속) |
| [`docs/process/document_impact_matrix.md`](docs/process/document_impact_matrix.md) | 변경 → 검토 문서 빠른 참조 |
| [`docs/status-json-mutate-pattern.md`](docs/status-json-mutate-pattern.md) | RWHarness fork-and-refactor proposal (정체성·Phase·원칙) |
| [`PROGRESS.md`](PROGRESS.md) | 현재 상태 / TODO / Blockers |
| [`AGENTS.md`](AGENTS.md) | 외부 에이전트(Codex 등) 지침 |
| [`.github/PULL_REQUEST_TEMPLATE.md`](.github/PULL_REQUEST_TEMPLATE.md) | PR 체크리스트 |
| [`scripts/check_document_sync.mjs`](scripts/check_document_sync.mjs) | Document Sync 게이트 구현 |
| [`scripts/check_task_id.mjs`](scripts/check_task_id.mjs) | Task-ID 형식 검증 게이트 (governance §2.1) |
| [`scripts/setup_branch_protection.mjs`](scripts/setup_branch_protection.mjs) | main 브랜치 보호 적용 스크립트 (governance §2.8) |
| [`docs/process/branch-protection-setup.md`](docs/process/branch-protection-setup.md) | branch protection 적용/검증 가이드 |
| [`docs/process/plugin-dryrun-guide.md`](docs/process/plugin-dryrun-guide.md) | RWHarness 와 공존 plugin 배포 dry-run 절차 (proposal §12 풀어쓴 운영 가이드) |
| [`scripts/hooks/pre-commit`](scripts/hooks/pre-commit) | git pre-commit hook |
| [`scripts/hooks/cc-pre-commit.sh`](scripts/hooks/cc-pre-commit.sh) | Claude Code PreToolUse hook |

## 4. 개발 명령어

```sh
# Document Sync 게이트 수동 실행 (commit 전 자동 호출됨)
node scripts/check_document_sync.mjs

# git hook 설치 (clone 후 1회)
cp scripts/hooks/pre-commit .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit

# 하네스 단위 테스트 실행
python3 -m unittest discover -s tests -v
python3 -m unittest tests.test_signal_io -v   # 단일 모듈
```

> 빌드 / 런타임 명령어는 코드 도입 시 본 섹션에 추가 (별도 Task-ID).

## 5. 커밋 / PR 절차

> 상세: 글로벌 `~/.claude/CLAUDE.md` "커밋 절차" 섹션 + 본 프로젝트 거버넌스 추가 강제.

```
1. git checkout -b {type}/{설명} main      # type: chore | feat | fix | docs
2. (변경 + 거버넌스 동반 파일 갱신)
3. git add {파일}
4. node scripts/check_document_sync.mjs    # 게이트 수동 확인 (선택)
5. git commit -m "..."                      # hook 자동 게이트
6. git push -u origin {branch}
7. gh pr create --title "..." --body "..."  # PULL_REQUEST_TEMPLATE 채움
8. gh pr merge --squash
9. git checkout main && git pull
```

- **main 직접 commit/push 금지**. 항상 branch → PR → squash merge.
- **branch 는 merge 후에도 삭제하지 않는다** (글로벌 룰 정합).
- PR title = commit message subject. PR body = 거버넌스 체크리스트 + 변경 요약.

## 6. 환경변수

현재 없음. 도입 시 본 섹션에 (이름·용도·기본값·필수 여부) 추가.
