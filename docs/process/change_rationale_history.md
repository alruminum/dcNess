# Change Rationale History (WHY log)

> 본 파일은 dcNess 프로젝트 모든 변경 작업의 **WHY** (왜 바꿨나) 로그.
> 규칙 정의: [`governance.md`](governance.md) §2.3 / §2.6 (재기술 금지).

## 형식

```
### {Task-ID}
- **Date**: YYYY-MM-DD
- **Rationale**: 변경 동기 / 해결할 문제
- **Alternatives**: 검토한 대안과 기각 이유 (최소 1개 이상)
- **Decision**: 채택안 + 채택 이유
- **Follow-Up**: 후속 작업 / 측정 항목 / 회귀 위험
```

---

## Records

### DCN-CHG-20260429-01
- **Date**: 2026-04-29
- **Rationale**: 신규 프로젝트 dcNess 는 RWHarness fork-and-refactor 의 메인 Claude 직접 작업 모드(`status-json-mutate-pattern.md` §10/§11). 코드/정책/빌드 변경이 관련 문서를 동반하지 않아 발생하는 drift 를 commit 단위에서 차단할 거버넌스가 부재.
- **Alternatives**:
  1. *PR 리뷰어 수동 검사* — 인적 오류, 일관성 없음. 기각.
  2. *GitHub Action 만 (push 후 fail)* — 피드백 지연, `status-json-mutate-pattern.md` R9 trade-off 와 동일. local 차단 부재. 기각.
  3. *(채택)* **3중 pre-commit + SSOT** — git hook + Claude Code hook + 에이전트 지침 + diff 기반 게이트. local 차단 + 기계 강제 + 에이전트 강제 동시.
- **Decision**: 옵션 3. `governance.md` SSOT + `scripts/check_document_sync.mjs` diff 게이트 + 3중 pre-commit. `status-json-mutate-pattern.md` §2.5 원칙 1(룰 순감소) 정합 — *기존 룰 중복 회피* 위해 SSOT 단일화, 다른 파일은 참조만.
- **Follow-Up**:
  - bootstrap PR 머지 후 1주 사용 데이터 수집 (Document-Exception 빈도, false positive 횟수)
  - GitHub Actions workflow (`.github/workflows/document-sync.yml`) 추가는 별도 Task-ID
  - 30일 후 carry-over: 게이트가 차단한 위반 카탈로그 → `governance.md` §2.6 룰 정정 input
  - git 저장소 초기화 + 첫 commit (별도 작업)

### DCN-CHG-20260429-02
- **Date**: 2026-04-29
- **Rationale**:
  - dcNess 는 글로벌 `~/.claude/CLAUDE.md` 의 RWHarness 위임 룰(에이전트 분기 / 인프라 분기)이 미적용되는 신규 프로젝트(`status-json-mutate-pattern.md` §10/§11.4). 메인 Claude 가 본 저장소 작업 시 *어떤 절차·문서·금지사항*을 따라야 하는지 단일 진입점이 부재.
  - 부수 문제: `CLAUDE.md` / `AGENTS.md` 같은 루트 정책 파일이 게이트의 Change-Type 분류에서 어떤 패턴에도 매칭되지 않아 *분류 비대상* → 정책 변경이 record/rationale 동반 없이 통과되는 구멍.
- **Alternatives**:
  1. *글로벌 `~/.claude/CLAUDE.md` 만 의존* — RWHarness 위임 룰이 dcNess 모드와 충돌 (architect/engineer 강제 vs §11.4 메인 직접 작업). 기각.
  2. *루트 정책 파일을 `docs-only` 로 분류* — 정책 변경에 WHY 로그 동반 강제가 안 됨. 기각.
  3. *(채택)* **루트 CLAUDE.md 신규 + 게이트 `agent` 카테고리에 `^CLAUDE\.md$` / `^AGENTS\.md$` 추가** — 프로젝트 모드 명시 + 정책 변경에 record + rationale 동반 강제.
- **Decision**: 옵션 3. CLAUDE.md 는 SSOT 재기술 금지 — 절차·링크·문서지도만 박는다. 게이트 룰은 governance.md §2.2 와 `check_document_sync.mjs` 양쪽 동시 갱신 (코드 = 명세 구현).
- **Follow-Up**:
  - 후속 정책 파일(예: `SECURITY.md`, `CONTRIBUTING.md`) 도입 시 동일 카테고리 검토.
  - 빌드/테스트 도입 시 CLAUDE.md §4 개발 명령어 / §6 환경변수 갱신 (별도 Task-ID).
  - `.github/workflows/document-sync.yml` 추가 (CI 게이트, 별도 Task-ID).
