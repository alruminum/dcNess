# Document Impact Matrix

> 변경 유형 → 검토 / 갱신 필수 문서 매핑.
> 규칙 정의: [`governance.md`](governance.md) §2.6 (재기술 금지). 본 파일은 빠른 참조용.

## 매트릭스

| Change-Type | 항상 필수 | 추가 필수 | 카테고리별 deliverable (Document-Exception 가능) |
|---|---|---|---|
| `spec` | `document_update_record.md` | `change_rationale_history.md` | `docs/spec/**` 또는 `docs/proposals/**` |
| `agent` | `document_update_record.md` | `change_rationale_history.md` | `agents/*.md` (해당 agent docs) |
| `harness` | `document_update_record.md` | `change_rationale_history.md`, `PROGRESS.md` | `tests/**` 또는 `docs/impl/**` |
| `hooks` | `document_update_record.md` | `change_rationale_history.md`, `PROGRESS.md` | `tests/hooks/**` (있을 시) |
| `ci` | `document_update_record.md` | `change_rationale_history.md`, `PROGRESS.md` | — |
| `test` | `document_update_record.md` | — | — |
| `docs-only` | `document_update_record.md` | — | — |

## 사용 흐름

1. `git status` / `git diff --name-only` 로 변경 파일 확인
2. [`governance.md`](governance.md) §2.2 표로 Change-Type 결정
3. 위 표의 *항상 필수* + *추가 필수* 모두 같은 commit 에 동반
4. *카테고리별 deliverable* 미충족 시 `Document-Exception:` 기재 ([`governance.md`](governance.md) §2.4)
5. `node scripts/check_document_sync.mjs` 통과 확인 후 commit
