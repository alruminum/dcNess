# Module Plan

**모드**: architect 의 모듈별 구현 계획 호출 — impl 1개 단위.
**결론**: prose 마지막 단락에 `READY_FOR_IMPL` 명시.
**호출자가 prompt 로 전달하는 정보**:
- 대상 모듈명/에픽 경로
- 듀얼 모드 표시 (`new_impl` / `spec_issue`, 생략 시 `new_impl`)
- 설계 문서 경로 (`new_impl` 모드 필수, `spec_issue` 모드 생략 가능)
- (선택) DESIGN_HANDOFF 문서 경로

**목표**: 특정 모듈의 구현 계획 파일을 작성한다.

## SPEC_ISSUE 분기 (mode=spec_issue)

**하지 않는다**:
- Epic / Story GitHub 이슈 신규 생성 (QA 가 이미 Bugs 마일스톤 이슈 생성)
- stories.md 에 신규 Story 추가 (기존 Story 체크리스트 항목 추가는 허용)
- CLAUDE.md 에 신규 에픽 행 추가

**평소대로 한다**:
- impl 파일: 가장 관련 있는 기존 에픽의 impl 폴더에 작성
- CLAUDE.md: 기존 에픽 행에 impl 번호 + 이슈 번호 추가
- trd.md 업데이트 (해당 시)

설계 문서 없이 qa_report 기반으로 관련 소스를 직접 읽고 분석.

## 작업 순서

1. `SYSTEM_DESIGN_READY` 문서 읽기 (전체 구조 파악)
2. 프로젝트 루트 `CLAUDE.md` 읽기
3. `docs/impl/00-decisions.md` 또는 유사 파일 읽기
4. 관련 설계 문서 읽기 (architecture, domain-logic, db-schema, ui-spec 등)
4-a. **DB 영향도 분석** (기능 추가·변경·제거 포함 시 필수) — `docs/db-schema.md` 를 읽고 유형별 검토:

  | 변경 유형 | 확인 기준 | Forward DDL | Rollback DDL |
  |---|---|---|---|
  | 테이블 추가 | 기존 테이블과 이름·PK 충돌 없는가 | `CREATE TABLE ...` | `DROP TABLE ...` |
  | 컬럼 추가 | NOT NULL 이면 DEFAULT 필요 | `ALTER TABLE ADD COLUMN ...` | `ALTER TABLE DROP COLUMN ...` |
  | 컬럼 제거 | NOT NULL 컬럼인가 | `ALTER TABLE DROP COLUMN ...` | `ALTER TABLE ADD COLUMN ... NOT NULL DEFAULT ...` |
  | 컬럼 속성 변경 | 타입·제약 변경 | `ALTER COLUMN ...` | `ALTER COLUMN` 원복 |
  | 영향 없음 | 코드 변경이 DB 와 무관 | — | — |

  분석 결과는 impl "주의사항" 섹션에 반드시 기록. DB 변경 필요 시 GitHub Issue 또는 stories.md 에 "DB 마이그레이션" 태스크 추가.

5. 기존 유사 구현 파일 검토 (패턴 일관성)
6. 의존 모듈 소스 파일 읽기 (실제 인터페이스 확인 필수)
7. 계획 파일 작성

## 계획 파일 템플릿

```markdown
---
depth: std
design: required  # 스크린샷 변경 시만
---
# [모듈명]

## 결정 근거
- [구조/방식 선택 이유]
- [버린 대안 + 이유]

## 생성/수정 파일
- `src/path/to/file.tsx` — [역할]
- `src/__tests__/[모듈명].test.tsx` — [검증 대상] (테스트 파일도 명시 필수)

> **테스트 파일 경로 필수**: `## 수용 기준` 표에 `(TEST)` 태그 1개 이상이면 대응 테스트 파일 경로를 본 목록에 반드시 포함. 누락 시 test-engineer 가 타겟 추측 → 엉뚱한 파일 덮어쓰기 사고.

## 인터페이스 정의
[TypeScript Props/타입/함수 시그니처]

## 핵심 로직
[의사코드 또는 구현 가능한 스니펫]

## 주의사항
- [모듈 경계]
- [에러 처리 방식]
- [상태 초기화 순서]
- [DB 영향도 결과]

## 수용 기준

| 요구사항 ID | 내용 | 검증 방법 | 통과 조건 |
|---|---|---|---|
| REQ-001 | ... | (TEST) | vitest TC 이름 |
| REQ-002 | ... | (BROWSER:DOM) | DOM 쿼리/상태 |
| REQ-003 | ... | (MANUAL) | 자동화 불가 이유 + 검증 절차 |
```

## 수용 기준 작성 규칙

- **`## 수용 기준` 섹션 없는 impl 작성 금지** — validator 가 PLAN_VALIDATION_FAIL 반려
- **모든 행에 검증 방법 태그 필수**
- **REQ-NNN** 형식 (001부터, 모듈 내 독립 순번)

| 태그 | 의미 | 사용 조건 |
|---|---|---|
| `(TEST)` | vitest 자동 테스트 | 기본값 — 로직·상태·훅 검증 |
| `(BROWSER:DOM)` | Playwright DOM 쿼리 | UI 렌더링·DOM 상태 직접 확인 시 |
| `(MANUAL)` | curl/bash 수동 절차 | 자동화 불가 시만 (이유 명시 필수) |

## 듀얼 모드 가드레일 — 디자인 토큰 의존성 (UI 컴포넌트 impl 만)

UI 컴포넌트(*.tsx 화면·뷰) impl 이고 **`docs/ux-flow.md` §0 디자인 가이드 존재 + `docs/design-handoff.md` 미존재**(=듀얼 모드) 인 경우:

- `## 의존성` 섹션에 `src/theme/` 명시 (없으면 `01-theme-tokens.md` 선행 impl 필요)
- `## 인터페이스 정의` 에서 색·폰트·간격은 `theme.colors.*`, `theme.typography.*`, `theme.spacing.*` 형식만 — hex 리터럴(`#FFD700`)·폰트명 직접·rem/px 직접값 금지
- `## 수용 기준` 1행 추가: `| REQ-NNN | 직접 색·폰트·간격 리터럴 사용 금지 | (TEST) | grep 으로 hex/px 리터럴 0건 확인 |`

근거: 디자인 시안 도착 후 토큰값만 patch 하면 컴포넌트 갈아엎기 0. 자세한 정책은 task-decompose.md §듀얼 모드 가드레일 참조.

## READY_FOR_IMPL 게이트

자가 체크. 하나라도 미충족 시 보강 후 완료 보고:

- [ ] 생성/수정 파일 목록 확정
- [ ] 모든 Props/인터페이스 TypeScript 타입 명시
- [ ] 의존 모듈 실제 인터페이스 소스에서 직접 확인 (추측 금지)
- [ ] 에러 처리 방식 명시 (throw / 반환 / 상태 업데이트)
- [ ] 페이지 전환·상태 초기화 순서 명시 (해당 시)
- [ ] DB 영향도 분석 완료 (영향 없음 포함, 주의사항에 기록)
- [ ] Breaking Change 검토: 영향받는 파일 목록 명시 (없으면 "없음")
- [ ] 핵심 로직: 의사코드/스니펫 포함 (빈 섹션이면 미통과)
- [ ] TypeScript 타입 정합: null 반환 가능 시 `| null` 포함
- [ ] import 완전성: 스니펫 외부 심볼 import 경로 명시
- [ ] **수용 기준 섹션 존재**
- [ ] **수용 기준 메타데이터**: 모든 행에 (TEST)/(BROWSER:DOM)/(MANUAL) 태그
- [ ] **테스트 파일 경로 명시**: (TEST) 태그 1+ 시 대응 테스트 경로가 ## 생성/수정 파일에 포함

## prose 결론 예시

```markdown
## 작업 결과

impl 파일 작성 완료: docs/milestones/v1/epics/epic-03-auth/impl/02-login-form.md

최종 체크:
- [✓] 생성 파일 목록
- [✓] 타입 명시
- [✓] 의존 모듈 실제 확인
- [✓] 에러 처리
- [✓] 핵심 로직
- [✓] 수용 기준 + 메타데이터 + 테스트 파일 경로

## 산출물
- impl_path: docs/milestones/v1/epics/epic-03-auth/impl/02-login-form.md
- depth: std

## 결론

READY_FOR_IMPL
```

## CLAUDE.md 모듈 표 업데이트

READY_FOR_IMPL 통과 후, 프로젝트 루트 `CLAUDE.md` 의 모듈 계획 파일 표 업데이트:

- 해당 milestone/epic 섹션(`### vNN` + `**Epic NN — 이름**`) 아래 새 impl 항목 추가
- 섹션 없으면 `### vNN` + `**Epic NN — 이름** · [stories](경로)` 헤더 포함 신규 추가
- 표 형식: `| NN 모듈명 | [경로](경로) |`

## 이슈 생성 분기 (완료 후)

| 조건 | 이슈 생성 |
|---|---|
| 호출자가 `mode=spec_issue` 전달 | 생성 스킵 (QA 가 이미 생성) |
| 프롬프트에 `[epic-level]` 또는 product-planner 경유 | 이슈 생성 안 함 — Epic + Story 이슈는 product-planner 가 이미 생성. impl 경로만 기존 Story 이슈 본문에 업데이트 |
| 위 두 조건 없음 (단순 feat 직접 요청) | feat 이슈 1개 생성 |

### Feature 이슈 제목 / 본문

```
제목: [{milestone_name}] {기능 설명}
```

```markdown
## 목적
[필요 이유]

## 구현 범위
- [ ] 항목1

## 관련 파일
- `파일경로`

## 완료 기준
- [ ] 기준1
```

milestone 반드시 포함. milestone 번호는 이름으로 API 조회 후 사용 (하드코딩 금지).
