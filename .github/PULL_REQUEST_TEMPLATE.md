## Summary
<!-- 변경 요약 1~3줄 -->

## Task-ID
`DCN-CHG-YYYYMMDD-NN`

## Change-Type
<!-- governance §2.2 — 해당 토큰 모두 체크 -->
- [ ] `spec`
- [ ] `agent`
- [ ] `harness`
- [ ] `hooks`
- [ ] `ci`
- [ ] `test`
- [ ] `docs-only`

## Document Sync Checklist
- [ ] `docs/process/document_update_record.md` 갱신 (WHAT 로그)
- [ ] `docs/process/change_rationale_history.md` 갱신 — *spec/agent/harness/hooks/ci 변경 시*
- [ ] `PROGRESS.md` 갱신 — *harness/hooks/ci 변경 시*
- [ ] 카테고리별 deliverable 동반 (impact matrix)
- [ ] `node scripts/check_document_sync.mjs` 로컬 실행 통과
- [ ] *(예외 시)* `Document-Exception:` 사유 기재

## Test Plan
- [ ] 관련 테스트 추가/갱신
- [ ] 회귀 검증

---
규칙 정의: [`docs/process/governance.md`](../docs/process/governance.md) (SSOT)
