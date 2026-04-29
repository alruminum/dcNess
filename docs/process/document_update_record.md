# Document Update Record (WHAT log)

> 본 파일은 dcNess 프로젝트 모든 변경 작업의 **WHAT** (무엇을 바꿨나) 로그.
> 규칙 정의: [`governance.md`](governance.md) §2.3 / §2.6 (재기술 금지).

## 형식

```
### {Task-ID}
- **Date**: YYYY-MM-DD
- **Change-Type**: spec | agent | harness | hooks | ci | test | docs-only (복수 가능)
- **Files Changed**:
  - path/to/file.md
  - path/to/code.ts
- **Summary**: 한 줄 요약
- **Document-Exception** (있을 때만): 예외 사유
```

---

## Records

### DCN-CHG-20260429-01
- **Date**: 2026-04-29
- **Change-Type**: ci, docs-only
- **Files Changed**:
  - `docs/process/governance.md` (신규)
  - `docs/process/document_update_record.md` (신규)
  - `docs/process/change_rationale_history.md` (신규)
  - `docs/process/document_impact_matrix.md` (신규)
  - `scripts/check_document_sync.mjs` (신규)
  - `scripts/hooks/pre-commit` (신규)
  - `scripts/hooks/cc-pre-commit.sh` (신규)
  - `.claude/settings.json` (신규)
  - `.github/PULL_REQUEST_TEMPLATE.md` (신규)
  - `AGENTS.md` (신규)
  - `PROGRESS.md` (신규)
- **Summary**: 거버넌스 시스템 초기 구축 — Document Sync 게이트(`check_document_sync.mjs`) + 3중 pre-commit 강제(git hook + Claude Code hook + AGENTS 지침) + SSOT(`governance.md`).
- **Document-Exception**: bootstrap commit — 거버넌스 자체 도입이라 이전 산출물 없음. 본 항목 자체가 self-record.

### DCN-CHG-20260429-02
- **Date**: 2026-04-29
- **Change-Type**: agent, ci, docs-only
- **Files Changed**:
  - `CLAUDE.md` (신규 — 메인 Claude 작업 지침)
  - `docs/process/governance.md` (§2.2 agent 패턴에 `^CLAUDE\.md$`, `^AGENTS\.md$` 추가)
  - `scripts/check_document_sync.mjs` (CATEGORY_RULES agent 토큰에 동일 패턴 추가)
  - `docs/process/document_update_record.md` (본 항목)
  - `docs/process/change_rationale_history.md`
  - `PROGRESS.md`
- **Summary**: 프로젝트 루트 CLAUDE.md 신규 + 게이트 룰에 루트 정책 파일(`CLAUDE.md` / `AGENTS.md`) `agent` 카테고리 분류 추가.

### DCN-CHG-20260429-03
- **Date**: 2026-04-29
- **Change-Type**: harness, test, agent, docs-only
- **Files Changed**:
  - `harness/state_io.py` (신규 — Phase 1 핵심 모듈)
  - `tests/test_state_io.py` (신규 — 32 케이스, 5 failure modes 검증)
  - `CLAUDE.md` (§4 개발 명령어에 테스트 실행 명령 추가)
  - `docs/process/document_update_record.md` (본 항목)
  - `docs/process/change_rationale_history.md`
  - `PROGRESS.md`
- **Summary**: Phase 1 foundation — `harness/state_io.py` 신규(write/read/clear + R8 5 failure modes 단일 normalize) + 테스트 32 케이스 전부 PASS. `parse_marker` 사다리 폐기를 위한 첫 모듈.
