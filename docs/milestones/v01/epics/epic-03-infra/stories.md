# Epic 03 — 인프라

> **GitHub Epic Issue:** [#110](https://github.com/alruminum/dcNess/issues/110)
> **Origin**: `DCN-CHG-20260504-02`
> **Scope**: 거버넌스 / git 규칙 / 프로세스 문서 / dcness plugin agent 룰 정합 작업.

## Story 5 — spec 현실 갭 8건 stories 일괄 등록 (메타)

**GitHub Issue:** [#115](https://github.com/alruminum/dcNess/issues/115)

### 배경 / 문제

dcness plugin (0.1.0-alpha) 의 agent / 글로벌 CLAUDE.md / 본 프로젝트 CLAUDE.md 사이 spec 현실 불일치 8건 발견 (실증 검증 — `~/.claude/plugins/cache/dcness/dcness/0.1.0-alpha/agents/**` 전수 grep 기준):

1. `ui-spec.md` 유령 owner / `design-handoff.md` 1회성 패키지 정리 필요 → Story 6
2. `stories.md` Write owner 3중 (product-planner / tech-epic / task-decompose) 충돌 → Story 7
3. `docs/impl/00-decisions.md` owner spec 부재 → Story 8
4. `domain-logic` vs `domain-model` 명칭 잔존 충돌 → Story 9
5. `epic-index.md` vs `backlog.md` 역할 중복 → Story 10
6. `db-schema.md` 부트스트랩 (최초 생성) owner 누락 → Story 11
7. `bugfix/` 글로벌 매트릭스 보강 + `issue-lifecycle.md` plugin 반영 → Story 12

각 갭을 **forward-only 등록** 한다. 본 메타 스토리는 후속 7개 스토리의 진입점.

### 수용 기준 (Given/When/Then)

- **Given** EPIC03 (인프라, #110) 가 open 상태이고 Story 6~12 가 미등록일 때
  **When** stories.md (본 파일) write + Story 6~12 GitHub 이슈 8개 (Story 5 포함) 생성
  **Then** 각 Story 헤더 직하 `**GitHub Issue:** [#NNN](url)` 매치 + EPIC03 sub-issue 연결

- **Given** stories.md 에 8개 Story 모두 등록된 상태에서
  **When** `node scripts/check_document_sync.mjs` 실행
  **Then** `[doc-sync] PASS`

### 작업 범위

- `docs/milestones/v01/epics/epic-03-infra/stories.md` (신규)
- GitHub 이슈 8개 (Story 5~12) — 라벨 `V01` + `EPIC03` + `story`, milestone `v0.1.0`
- `docs/process/document_update_record.md`

---

## Story 6 — design.md SSOT 도입 (ui-spec / design-handoff 폐기)

**GitHub Issue:** [#116](https://github.com/alruminum/dcNess/issues/116)

### 배경 / 문제

plugin agent grep 결과:
- `docs/ui-spec.md` = read 4건 (designer / engineer / code-validation L11+L21) / **Write 0건** — 유령 spec
- `pr-reviewer.md` L98 / `docs-sync.md` L36: "owner = designer" 표기되어 있으나 designer.md Write 책임 섹션엔 ui-spec 없음
- `designer.md` L31 실제 산출 = `docs/design-handoff.md` (1회성 인계 패키지: Issue ID / Variant / Pencil Frame ID / Tokens / Component Structure / Animation Spec / Notes for Engineer)
- design-handoff 의 8개 항목은 Pencil 캔버스 + GitHub 이슈 + ux-flow §0 디자인 가이드 로 분산 흡수 가능

→ Google design.md 공식 spec (https://github.com/google-labs-code/design.md `docs/spec.md`) 을 채택해 의미적 디자인 시스템 SSOT 로 일원화. ui-spec.md / design-handoff.md 둘 다 폐기.

### 수용 기준 (Given/When/Then)

- **Given** dcness plugin agent 들이 `ui-spec.md` / `design-handoff.md` 를 read/write 하는 spec 을 가진 상태에서
  **When** plugin agents (`designer.md` / `engineer.md` / `ux-architect.md` / `architect/docs-sync.md` / `validator/code-validation.md` / `pr-reviewer.md`) + 글로벌 `~/.claude/CLAUDE.md` + `docs/design.md` spec docs 신설 작업 commit
  **Then** `ui-spec` / `design-handoff` 토큰 0건 (글로벌 CLAUDE.md + plugin agents 전체 grep) — 단 본 stories.md / change log 의 역사 기록 라인 제외

- **Given** Google design.md 공식 spec (Frontmatter `version`/`name`/`description`/`colors`/`typography`/`rounded`/`spacing`/`components` + 8섹션 본문) 를 채택한 상태에서
  **When** `docs/design.md` spec docs 작성
  **Then** Frontmatter schema + 토큰 참조 syntax `{path.to.token}` + 8섹션 헤딩 + Unknown 처리 룰 + dcness 적용 룰 (조건부 read / 토큰 무결성 검증) 5개 항목 모두 명시

- **Given** UI 없는 프로젝트 (dcness 자체 등) 에서
  **When** plugin agent (designer / engineer / code-validation / ux-architect) 가 design.md read 시도
  **Then** silent skip (FAIL X)

### 작업 범위

- `docs/design.md` (신규 — dcness 자체 spec 문서, Google spec 인용 + dcness 적용 룰)
- plugin agents (cache + 원본 동시):
  - `agents/ux-architect.md` — UX_FLOW / UX_SYNC / UX_REFINE 모드에 design.md 산출 추가, Write 권한 확장
  - `agents/designer.md` — ui-spec read → design.md read, Phase 4 DESIGN_HANDOFF 슬림화 (또는 폐지), components 부분 갱신 권한 명시
  - `agents/engineer.md` — UI 모듈 시 ui-spec → design.md
  - `agents/architect/docs-sync.md` — owner 표기 ui-spec → design.md
  - `agents/validator/code-validation.md` — ui-spec → design.md, 토큰 참조 무결성 검증
  - `agents/pr-reviewer.md` — 스코프 매트릭스 ui-spec → design.md
  - `agents/design-critic.md` — REVIEW 입력 ui-spec → design.md
- 글로벌 `~/.claude/CLAUDE.md` — `docs/ui-spec.md` 행 → `docs/design.md`
- `docs/process/document_update_record.md` + `docs/process/change_rationale_history.md`

---

## Story 7 — stories.md 다중 Write owner 충돌 해소

**GitHub Issue:** [#117](https://github.com/alruminum/dcNess/issues/117)

### 배경 / 문제

plugin agent 3개가 같은 `stories.md` 를 Write 함, 충돌 룰 부재:
- `agents/product-planner.md` L33: `Write 허용: prd.md, stories.md` (초기 생성)
- `agents/architect/tech-epic.md` L15: 폴백 시 `docs/milestones/vNN/epics/epic-NN-*/stories.md` 작성
- `agents/architect/task-decompose.md` L47: `stories.md 의 해당 Story 라인에 관련 이슈: #N 추가`

→ 책임 분리 명문화 필요.

### 수용 기준 (Given/When/Then)

- **Given** product-planner / tech-epic / task-decompose 3 agent 가 stories.md 를 Write 하는 상태에서
  **When** 각 agent.md 에 stories.md 책임 분리 룰 명시
  **Then** product-planner = 초기 생성 (PRODUCT_PLAN_READY 시 1회) / tech-epic = epic 추가 시 신규 Story 행 추가만 / task-decompose = 기존 Story 행에 `관련 이슈: #N` 만 추가 — 3 역할 disjoint

- **Given** 분리 룰 명시된 상태에서
  **When** `stories.md` 가 이미 존재하는데 product-planner 가 다시 Write 시도
  **Then** product-planner 가 PRODUCT_PLAN_CHANGE 모드로 분기 (overwrite 금지) — 명문화

### 작업 범위

- `agents/product-planner.md` — Write 책임 명시 (초기 생성 only)
- `agents/architect/tech-epic.md` — Write 범위 (신규 Story 행 추가만)
- `agents/architect/task-decompose.md` — Write 범위 (`관련 이슈` 라인 추가만)
- (선택) `docs/issue-lifecycle.md` — stories.md ownership 섹션 추가
- `docs/process/document_update_record.md` + `docs/process/change_rationale_history.md`

---

## Story 8 — `docs/impl/00-decisions.md` owner 명문화

**GitHub Issue:** [#118](https://github.com/alruminum/dcNess/issues/118)

### 배경 / 문제

plugin agent grep:
- `module-plan.md` L15 / `task-decompose.md` L11 / `code-validation.md` L9 — 모두 read 강제
- 어떤 agent 도 Write 책임 없음 → greenfield 부트스트랩 시 막힘

→ architect:system-design Phase B 산출 목록에 추가하거나 별도 부트스트랩 시점 명시.

### 수용 기준 (Given/When/Then)

- **Given** `agents/architect/system-design.md` 산출 목록 (L163~L173) 에 `00-decisions.md` 가 없는 상태에서
  **When** system-design.md Phase B 산출 또는 별도 부트스트랩 단계로 명문화
  **Then** greenfield 프로젝트가 PRODUCT_PLAN 직후 `docs/impl/00-decisions.md` 자동 생성 — 다른 agent 가 read 시 silent skip 없이 정상 read

- **Given** `00-decisions.md` 가 비어있는 brownfield 프로젝트에서
  **When** 새 architect 호출
  **Then** read 전 빈 파일 fallback 룰 적용 (없으면 skip, 있으면 read) — code-validation.md L9 의 SPEC_MISSING 분기와 정합

### 작업 범위

- `agents/architect/system-design.md` — 산출 목록에 `docs/impl/00-decisions.md` 추가 + 작성 시점 명시
- (필요 시) `agents/architect/module-plan.md` — read fallback 룰 명시
- `docs/process/document_update_record.md` + `docs/process/change_rationale_history.md`

---

## Story 9 — `domain-logic` / `domain-model` 명칭 통일

**GitHub Issue:** [#119](https://github.com/alruminum/dcNess/issues/119)

### 배경 / 문제

- 글로벌 `~/.claude/CLAUDE.md` = `docs/domain-logic.md` 명시
- plugin 실제 산출 = `docs/domain-model.md` (system-design.md L17 / module-plan.md L15 / spec-gap.md L19 — architect 단독 권한)
- `module-plan.md` L15 의 read 목록 안에 `domain-logic` 토큰 잔존
- → plugin 5+ agent 영향, read 시 path 혼동

### 수용 기준 (Given/When/Then)

- **Given** plugin agent 들 (system-design / module-plan / spec-gap / engineer / code-validation / plan-validation 등) 에 `domain-logic` 과 `domain-model` 토큰이 혼재한 상태에서
  **When** 모든 토큰을 `domain-model` 로 통일
  **Then** plugin agents 전체 grep `domain-logic` 결과 0건 (역사 기록 / 본 stories.md / change log 제외)

- **Given** 글로벌 `~/.claude/CLAUDE.md` 의 직접 수정 금지 매트릭스에 `docs/domain-logic.md` 가 명시된 상태에서
  **When** `docs/domain-model.md` 로 교체
  **Then** plugin spec 과 글로벌 룰 정합

### 작업 범위

- plugin agents 전수 grep → `domain-logic` 모두 `domain-model` 로 교체
  - 확인된 위치: `module-plan.md` L15, `plan-validation.md` L9 / L22 (등)
- 글로벌 `~/.claude/CLAUDE.md` 의 `docs/domain-logic.md` → `docs/domain-model.md`
- `docs/process/document_update_record.md` + `docs/process/change_rationale_history.md`

---

## Story 10 — `epic-index.md` vs `backlog.md` 역할 분리

**GitHub Issue:** [#120](https://github.com/alruminum/dcNess/issues/120)

### 배경 / 문제

- `agents/product-planner.md` L100~L104: `docs/epic-index.md` (epic ↔ GitHub 이슈 매핑) 생성
- `agents/architect/tech-epic.md` L15: 루트 `backlog.md` (epic 목록 + 완료 체크) 생성
- 둘 다 epic 인덱스 역할, 동기화 룰 부재 → drift 위험

### 수용 기준 (Given/When/Then)

- **Given** 두 파일 모두 epic 인덱스를 표기하지만 정의가 모호한 상태에서
  **When** 역할 분리 명문화 또는 한쪽 폐기
  **Then** 다음 중 1택 명시:
  - (a) `epic-index.md` = 이슈 매핑 SSOT / `backlog.md` = 진행률 체크 SSOT (역할 분리)
  - (b) `epic-index.md` 단일화 (backlog.md 폐기)
  - (c) `backlog.md` 단일화 (epic-index.md 폐기)

- **Given** 분리 / 단일화 결정 후
  **When** plugin agents (product-planner / tech-epic) 의 산출 책임 정합
  **Then** 두 파일 사이 drift 발생 시점 차단 (cross-reference 또는 1개 파일로 collapse)

### 작업 범위

- 결정 문서 작성 (1회 분석 + 옵션 채택)
- 채택안 따라 plugin agents 수정
- 글로벌 `~/.claude/CLAUDE.md` 의 backlog.md / epic-index.md 표기 정합
- `docs/process/document_update_record.md` + `docs/process/change_rationale_history.md`

---

## Story 11 — `db-schema.md` 부트스트랩 owner 명시

**GitHub Issue:** [#121](https://github.com/alruminum/dcNess/issues/121)

### 배경 / 문제

- `agents/architect/spec-gap.md` L23: "DB 스키마 변경 → `docs/db-schema.md` + `trd.md §4`" — **갱신 책임** 명시
- 그러나 신규 프로젝트 최초 생성 시점 spec 부재 (`agents/architect/system-design.md` 산출 목록 L163~L173 에 db-schema 없음)
- → DB 있는 greenfield 프로젝트에서 db-schema.md 가 누가 만드는지 모호

### 수용 기준 (Given/When/Then)

- **Given** `system-design.md` 산출 목록에 `db-schema.md` 가 없고 spec-gap.md 만 갱신 책임을 가진 상태에서
  **When** system-design.md Phase B 산출 목록에 `db-schema.md` 조건부 추가 (DB 있는 프로젝트만)
  **Then** greenfield + DB 프로젝트가 PRODUCT_PLAN 직후 `docs/db-schema.md` 자동 생성

- **Given** DB 없는 프로젝트 (dcness 자체 등) 에서
  **When** system-design 호출
  **Then** db-schema.md 미생성 (조건부 — `agents/architect/system-design.md` 에 명시)

### 작업 범위

- `agents/architect/system-design.md` — 산출 목록에 `docs/db-schema.md` 조건부 추가
- (필요 시) `agents/architect/spec-gap.md` — 부트스트랩 시점과 갱신 시점 분리 명시
- `docs/process/document_update_record.md` + `docs/process/change_rationale_history.md`

---

## Story 12 — `bugfix/` 글로벌 매트릭스 보강 + `issue-lifecycle.md` plugin 반영

**GitHub Issue:** [#122](https://github.com/alruminum/dcNess/issues/122)

### 배경 / 문제

**(a) bugfix/ 글로벌 매트릭스 보강**:
- plugin 은 `agents/architect/light-plan.md` L54 에 `docs/bugfix/#{이슈번호}-{슬러그}.md` 명문화 (architect 산출)
- 글로벌 `~/.claude/CLAUDE.md` 의 직접 수정 금지 매트릭스에는 bugfix/ 행 없음
- → 글로벌 룰 보강만 필요

**(b) issue-lifecycle.md plugin 반영**:
- 본 dcNess 프로젝트엔 `docs/issue-lifecycle.md` 신설됨 (DCN-CHG-20260504-01)
- plugin agents (qa / product-planner / tech-epic / engineer / impl 커맨드) 일부에 참조 추가됐으나, **본 SSOT 를 plugin docs 로 승격할지** 결정 필요
- → dcness plugin 의 docs 디렉토리에 issue-lifecycle 표준 추가 또는 본 프로젝트 단독 SSOT 유지 결정

### 수용 기준 (Given/When/Then)

- **Given** 글로벌 `~/.claude/CLAUDE.md` 직접 수정 금지 매트릭스에 bugfix 행이 없는 상태에서
  **When** `docs/bugfix/**` 행 추가 (owner = `architect:light-plan`)
  **Then** 메인 Claude 가 bugfix 파일을 직접 수정하지 않고 light-plan 위임 강제 — plugin spec 정합

- **Given** `docs/issue-lifecycle.md` 가 본 dcNess 프로젝트 단독 SSOT 인 상태에서
  **When** plugin docs 로 승격 여부 결정 + (승격 시) plugin docs 디렉토리에 복사 / (미승격 시) 본 프로젝트 단독 표기 명시
  **Then** plugin agents 가 issue-lifecycle.md 참조 시 경로가 명확 (현재는 `../docs/issue-lifecycle.md` 또는 본 프로젝트 root 가정 — 분리 필요)

### 작업 범위

- 글로벌 `~/.claude/CLAUDE.md` — 직접 수정 금지 매트릭스에 `docs/bugfix/**` 행 추가
- (결정 후) plugin docs 디렉토리에 issue-lifecycle.md 복사 또는 본 프로젝트 단독 유지 표기
- (필요 시) plugin agents 의 issue-lifecycle.md 경로 정합
- `docs/process/document_update_record.md` + `docs/process/change_rationale_history.md`

---

## 관련 이슈

| 스토리 | GitHub Issue |
|---|---|
| Epic | [#110](https://github.com/alruminum/dcNess/issues/110) |
| Story 5 | [#115](https://github.com/alruminum/dcNess/issues/115) |
| Story 6 | [#116](https://github.com/alruminum/dcNess/issues/116) |
| Story 7 | [#117](https://github.com/alruminum/dcNess/issues/117) |
| Story 8 | [#118](https://github.com/alruminum/dcNess/issues/118) |
| Story 9 | [#119](https://github.com/alruminum/dcNess/issues/119) |
| Story 10 | [#120](https://github.com/alruminum/dcNess/issues/120) |
| Story 11 | [#121](https://github.com/alruminum/dcNess/issues/121) |
| Story 12 | [#122](https://github.com/alruminum/dcNess/issues/122) |
