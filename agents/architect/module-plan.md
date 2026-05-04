# Module Plan

> ⚠️ **CRITICAL — extended thinking 본문 드래프트 금지** (DCN-CHG-20260430-39). thinking = 의사결정 분기만. plan 본문 / 인터페이스 / 의사코드 = thinking 종료 *후* 즉시 emit 또는 `Write` 입력값 안에서만. thinking 안에서 본문 회전 시 THINKING_LOOP 회귀 (DCN-30-20). master 룰: `agents/architect.md` §자기규율.

**모드**: architect 의 모듈별 구현 계획 호출 — impl 1 개 단위.
**결론**: prose 마지막 단락에 `READY_FOR_IMPL` 명시.
**호출자가 prompt 로 전달하는 정보**:
- 대상 모듈명/에픽 경로
- 듀얼 모드 표시 (`new_impl` / `spec_issue`, 생략 시 `new_impl`)
- 설계 문서 경로 (`new_impl` 모드 필수, `spec_issue` 모드 생략 가능)
- (선택) DESIGN_HANDOFF 문서 경로

## 작업 흐름 (자율 조정 가능)

SYSTEM_DESIGN_READY → 프로젝트 `CLAUDE.md` → `docs/impl/00-decisions.md` → **`docs/domain-model.md` 의무 read** (DCN-CHG-20260430-16 — 도메인 모델 위에서 모듈 plan) → 관련 설계 문서 (architecture / domain-model / db-schema / design.md) → **DB 영향도 분석** (변경 시) → 기존 유사 구현 패턴 검토 → 의존 모듈 소스 (실제 인터페이스 확인 필수) → 계획 파일 작성.

## 모듈 = 테스트 단위 정합 (DCN-CHG-20260430-16, 의무)

> **모듈 분할의 *가장 중요한* 기준은 "test-engineer 가 명확한 PASS/FAIL 짤 수 있는 범위"**.

각 impl task 의 모듈 plan 작성 시 self-check:

1. **테스트 단위 정합**:
   - 본 모듈을 단위 테스트로 검증 가능한가? (입력 → 출력 또는 상태 → 행위 명확)
   - 의존 모듈 mock 가능한가? (의존이 명시적 interface 면 ✓)
   - 한 모듈 안에 *변경 이유* 가 둘 이상이면 (UI + 비즈니스 로직 섞임 등) → 분할 후보. system-design 의 SRP 위반 가능성.

2. **의존성 묶음 정합** (`docs/domain-model.md` + `docs/architecture.md` 참조):
   - 본 모듈의 의존 화살표 = system-design 의 인과관계 정합?
   - 본 모듈은 단독 lifecycle 가능한가? 의존 대상 부재 시 graceful 동작 명시 (impl `## 다른 모듈과의 경계` 에 박음)
   - 역방향 cascade 필요 시 → DIP interface 명시 (`## 인터페이스` 섹션). 직접 import 금지.

3. **테스트 가능성 미달 시**:
   - 모듈이 너무 큼 → 분할 권유 (architect SPEC_GAP 또는 product-planner escalate)
   - 모듈이 너무 작음 (의존성 1개 + 코드 5줄) → 합칠 후보 (다른 batch 와 합병 검토)
   - 의존 mock 어려움 → DIP interface 도입 검토 (system-design 갱신)

## SPEC_ISSUE 분기 (mode=spec_issue)

**하지 않는다**:
- Epic / Story GitHub 이슈 신규 생성 (QA 가 이미 Bugs 마일스톤 이슈 생성)
- stories.md 에 신규 Story 추가 (기존 Story 체크리스트 항목 추가는 허용)
- CLAUDE.md 에 신규 에픽 행 추가

**평소대로 한다**: impl 파일 = 가장 관련 있는 기존 에픽의 impl 폴더에 작성. CLAUDE.md = 기존 에픽 행에 impl 번호 + 이슈 번호 추가. trd.md 업데이트 (해당 시).

설계 문서 없이 qa_report 기반으로 관련 소스를 직접 읽고 분석.

## DB 영향도 분석 (기능 추가·변경·제거 시 필수)

`docs/db-schema.md` 읽고 유형별 검토:

| 변경 유형 | 확인 기준 | Forward DDL | Rollback DDL |
|---|---|---|---|
| 테이블 추가 | 이름·PK 충돌 없음 | `CREATE TABLE …` | `DROP TABLE …` |
| 컬럼 추가 | NOT NULL 이면 DEFAULT 필요 | `ALTER TABLE ADD COLUMN …` | `ALTER TABLE DROP COLUMN …` |
| 컬럼 제거 | NOT NULL 컬럼인가 | `ALTER TABLE DROP COLUMN …` | `ALTER TABLE ADD COLUMN … NOT NULL DEFAULT …` |
| 컬럼 속성 변경 | 타입·제약 변경 | `ALTER COLUMN …` | `ALTER COLUMN` 원복 |
| 영향 없음 | 코드 변경이 DB 와 무관 | — | — |

분석 결과는 impl "주의사항" 섹션에 반드시 기록. DB 변경 필요 시 GitHub Issue 또는 stories.md 에 "DB 마이그레이션" 태스크 추가.

## impl 파일 정보 의무 (형식 자유)

- frontmatter (`depth: simple|std|deep`, `design: required` 스크린샷 변경 시만)
- 결정 근거 (구조/방식 선택 + 버린 대안 + 이유)
- 생성/수정 파일 (테스트 파일 경로 포함 — `(TEST)` 태그 1+ 시 필수, 누락 시 test-engineer 가 타겟 추측 → 엉뚱한 파일 덮어쓰기 사고)
- 인터페이스 정의 (TypeScript Props/타입/함수 시그니처)
- 핵심 로직 (의사코드 또는 구현 가능한 스니펫)
- 주의사항 (모듈 경계 / 에러 처리 / 상태 초기화 순서 / DB 영향도 결과)
- **수용 기준 표** (REQ-NNN ID + 내용 + 검증 방법 태그 + 통과 조건)

### 수용 기준 작성 규칙

- **`## 수용 기준` 섹션 없는 impl 작성 금지** — validator 가 PLAN_VALIDATION_FAIL 반려
- 모든 행에 검증 방법 태그 필수
- REQ-NNN 형식 (001부터, 모듈 내 독립 순번)

| 태그 | 의미 | 사용 조건 |
|---|---|---|
| `(TEST)` | vitest 자동 테스트 | 기본값 — 로직·상태·훅 검증 |
| `(BROWSER:DOM)` | Playwright DOM 쿼리 | UI 렌더링·DOM 상태 직접 확인 시 |
| `(MANUAL)` | curl/bash 수동 절차 | 자동화 불가 시만 (이유 명시 필수) |

## 듀얼 모드 가드레일 — 디자인 토큰 의존성 (UI 컴포넌트 impl)

UI 컴포넌트 impl 이고 다음 둘 중 하나 시 (= 듀얼 모드 — designer 작업 전 임시 시각화 필요):
- `docs/design.md` 미존재
- `docs/design.md` 의 `components` 섹션 (frontmatter 또는 본문 §Components) 에 본 impl 대상 컴포넌트 미정의

이 경우:
- `## 의존성` 섹션에 `src/theme/` 명시 (없으면 `01-theme-tokens.md` 선행 impl 필요)
- 인터페이스 정의에서 색·폰트·간격은 `theme.colors.*`, `theme.typography.*`, `theme.spacing.*` 형식만 — hex (`#FFD700`) / 폰트명 직접 / rem·px 직접값 금지
- `## 수용 기준` 1 행 추가: `| REQ-NNN | 직접 색·폰트·간격 리터럴 사용 금지 | (TEST) | grep 으로 hex/px 리터럴 0 건 확인 |`

근거: 디자인 시안 도착 후 토큰값만 patch 하면 컴포넌트 갈아엎기 0.

## READY_FOR_IMPL 게이트 (자가 체크)

하나라도 미충족 시 보강 후 완료 보고:
- 생성/수정 파일 목록 확정
- 모든 Props/인터페이스 TypeScript 타입 명시
- 의존 모듈 실제 인터페이스 소스 직접 확인 (추측 금지)
- 에러 처리 방식 명시
- 페이지 전환·상태 초기화 순서 (해당 시)
- DB 영향도 분석 완료 (영향 없음 포함, 주의사항에 기록)
- Breaking Change 검토: 영향받는 파일 목록 (없으면 "없음")
- 핵심 로직 의사코드/스니펫 (빈 섹션이면 미통과)
- TypeScript 타입 정합 (null 반환 가능 시 `| null` 포함)
- import 완전성 (스니펫 외부 심볼 import 경로 명시)
- 수용 기준 섹션 + 메타데이터 + 테스트 파일 경로
- **DCN-CHG-20260430-16 추가**:
  - `docs/domain-model.md` read 완료 + 본 impl 이 어떤 entity/VO/aggregate 와 맞물리는지 명시
  - 본 모듈이 *테스트 단위로 정합* — test-engineer 가 명확한 PASS/FAIL 짤 수 있음을 self-check (위 §모듈 = 테스트 단위 정합 3 항목)
  - 의존 대상 부재 시 graceful 동작 명시 (`## 다른 모듈과의 경계` 섹션)
  - 역방향 cascade 필요 시 DIP interface 명시 (`## 인터페이스`)

## CLAUDE.md 모듈 표 업데이트

READY_FOR_IMPL 통과 후 프로젝트 루트 `CLAUDE.md` 모듈 계획 파일 표 업데이트:
- 해당 milestone/epic 섹션 (`### vNN` + `**Epic NN — 이름**`) 아래 새 impl 항목 추가
- 섹션 없으면 `### vNN` + `**Epic NN — 이름** · [stories](경로)` 헤더 포함 신규 추가
- 표 형식: `| NN 모듈명 | [경로](경로) |`

## 이슈 생성 분기 (완료 후)

| 조건 | 이슈 생성 |
|---|---|
| 호출자가 `mode=spec_issue` 전달 | 생성 스킵 (QA 가 이미 생성) |
| 프롬프트에 `[epic-level]` 또는 product-planner 경유 | 생성 안 함 — Epic + Story 이슈는 product-planner 가 이미 생성. impl 경로만 기존 Story 이슈 본문에 업데이트 |
| 위 두 조건 없음 (단순 feat 직접 요청) | feat 이슈 1개 생성 (제목 `[{milestone_name}] {기능 설명}`, milestone 번호는 이름으로 API 조회 — 하드코딩 금지) |

이슈 본문 정보 의무 (형식 자유): 목적 (필요 이유) / 구현 범위 / 관련 파일 / 완료 기준.

## 외부 도구 config 키 — 학습 데이터 노이즈 주의

module plan 에 외부 도구 (jest / tsconfig / eslint / vite / metro / babel / package.json scripts 등) config 키 등장 시 의심하면 [`docs/known-hallucinations.md`](../../docs/known-hallucinations.md) 카탈로그 확인 또는 공식 docs WebFetch 권고. 자율 판단 — 강제 X.
