# Epic Index

> EPIC 번호 ↔ GitHub 이슈 번호 매핑 SSOT.
> **product-planner** 가 PRODUCT_PLAN_READY 산출물 write 후 epic 이슈 생성 + 본 파일에 추가.
> **task-decompose** 가 story 이슈 생성 시 부모 epic 번호/이슈 번호 조회.

## 관리 규칙

- **epic 이슈 생성 주체**: `product-planner` (PRODUCT_PLAN_READY 시 — `agents/product-planner.md` §PRODUCT_PLAN_READY 참조)
- **epic 번호 형식**: `EPIC01`, `EPIC02` (2자리 zero-pad, 에픽 내 독립 순번)
- **버전 레이블**: `V01`, `V02` (PRD 마일스톤 버전)
- **독립 스토리용 잡탕 에픽**: `EPIC00` (버전 무관, epic 이슈 없음 — stories.md 에만 존재)
- **레이블 조합**: epic 이슈 = `V0N` + `EPIC0N`. story 이슈 = `V0N` + `EPIC0N` + `Story0N`.

## 매핑 테이블

| EPIC 번호 | 버전 | GitHub 이슈 # | 제목 | 상태 |
|---|---|---|---|---|
| EPIC00 | — | — | 잡탕 에픽 (독립 스토리) | reserved |
