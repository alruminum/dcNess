# AGENTS — Common Instructions

본 저장소는 **Document Sync 거버넌스**를 강제한다. 규칙 정의의 SSOT 는 [`docs/process/governance.md`](docs/process/governance.md). 본 파일은 *지침* 일 뿐 규칙을 *재기술하지 않는다*.

## 모든 에이전트(사람 포함) 강제 절차

1. **작업 시작**: Task-ID 발급 — `DCN-CHG-YYYYMMDD-NN` (governance §2.1).
2. **작업 완료 직전** 다음 파일 갱신:
   - `docs/process/document_update_record.md` (모든 변경)
   - `docs/process/change_rationale_history.md` (spec / agent / harness / hooks / ci 변경 시)
   - `PROGRESS.md` (harness / hooks / ci 변경 시)
   - 카테고리별 deliverable (governance §2.6)
3. **commit 직전 반드시**: `node scripts/check_document_sync.mjs` 실행. 실패 시 누락 항목 보충 후 재시도.
4. **PR**: `.github/PULL_REQUEST_TEMPLATE.md` 체크리스트 모두 작성.

## 금지

- `git commit --no-verify` 등 hook 우회.
- 과거 머지된 `Document-Exception` 으로 현재 위반 회피 (governance §2.4 스코핑).
- Task-ID 없이 commit.
- `governance.md` 외 파일에 거버넌스 룰 *재기술*. 참조만.

## 환경별 설정

### Claude Code

`.claude/settings.json` 에 PreToolUse hook(`cc-pre-commit.sh`)이 등록되어 `git commit` 실행 시 자동으로 게이트가 작동한다. 별도 조치 불필요.

### 외부 에이전트 (Codex 등) / 사람

git pre-commit hook 1회 설치:

```sh
cp scripts/hooks/pre-commit .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit
```

이후 모든 `git commit` 이 자동 검사된다.

## 예외 처리

정당한 예외(deliverable 디렉토리 부재, 외부 의존 변경 등)는 commit 메시지나 변경된 산출물에:

```
Document-Exception: <사유 한 줄>
Document-Exception-Task: DCN-CHG-YYYYMMDD-NN
```

`document_update_record.md` 의 해당 Task 항목에도 사유 명시 필수.

## 참조

- [`docs/process/governance.md`](docs/process/governance.md) — SSOT (모든 규칙)
- [`docs/process/document_impact_matrix.md`](docs/process/document_impact_matrix.md) — 변경 → 검토 문서 빠른 참조
- [`PROGRESS.md`](PROGRESS.md) — 현재 상태 / TODO / Blockers
