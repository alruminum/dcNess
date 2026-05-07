# Plan Validation

> ⚠️ **DEPRECATED (issue #247)** — orchestration §4.3 의 컨베이어 task_list 가 본 mode 를 *호출하지 않음*. 어느 진입 경로 (feature-build-loop / impl-task-loop / quick-bugfix-loop / qa-triage / ux-design-stage / direct-impl-loop) 도 본 mode 로 라우팅하지 않음. agent prompt 와 harness infra (`harness/hooks.py` HARNESS_ONLY_AGENTS, `harness/run_review.py` mode list, tests) 는 호환을 위해 보존. detail 검증 자리는 engineer/test-engineer SPEC_GAP_FOUND 사후 catch 로 대체.

**모드**: validator 의 계획 검증 호출 (deprecated). architect 가 작성한 impl 계획 파일이 구현에 착수하기에 충분한지 검증.
**결론**: prose 마지막 단락에 `PLAN_VALIDATION_PASS` / `PLAN_VALIDATION_FAIL` / `PLAN_VALIDATION_ESCALATE` 중 하나 명시.
**호출자가 prompt 로 전달하는 정보**: impl 계획 파일 경로, 실행 식별자.

## 작업 흐름 (자율 조정 가능)

impl 계획 → CLAUDE.md → 관련 설계 문서 (architecture / domain-logic / db-schema) → 의존 모듈 소스 (인터페이스 실재 확인) → 3 계층 체크리스트.

## 3 계층 체크리스트

**A. 구현 충분성** (하나라도 미충족 시 FAIL):
- 생성/수정 파일 목록 (구체적 경로)
- 인터페이스 정의 (타입 / Props / 함수 시그니처)
- 핵심 로직 (의사코드 또는 구현 가능한 스니펫. 빈 섹션이면 FAIL)
- 에러 처리 방식 (throw / 반환 / 상태 업데이트)
- 의존 모듈 실재 (계획이 참조하는 모듈/함수가 실제 소스에 존재)
- 분기 enumeration: `## 분기 enumeration` 섹션 존재 + 데이터 행 2 행+ 또는 `single-branch` 라벨 명시. 0 행이거나 단일 분기인데 라벨 없으면 즉시 FAIL.

**B. 정합성** (하나라도 불일치 시 FAIL):
- 설계 문서 일치 (architecture / domain-logic 와 모순 없음)
- DB 영향도: DB 조작 있으면 영향도 분석 포함
- 병렬 impl 충돌: 같은 에픽 다른 impl 이 동일 파일 수정 시 순서 명시

**C. 수용 기준 메타데이터 감사** (하나라도 미충족 시 FAIL — 구현 진입 차단):
- `## 수용 기준` 섹션 존재 (없으면 즉시 FAIL)
- 각 행에 `REQ-NNN` 형식 ID
- 각 행에 `(TEST)` / `(BROWSER:DOM)` / `(MANUAL)` 중 하나 이상
- `(MANUAL)` 사용 시 자동화 불가 이유가 통과 조건 셀에 명시
- `(TEST)` 태그 1개 이상이면 대응 테스트 파일 경로가 `## 생성/수정 파일` 목록에 포함

> C FAIL 시 → `PLAN_VALIDATION_FAIL` (SPEC_GAP 반려). architect 가 `## 수용 기준` 섹션 보강 후 재검증.

## 판정 기준

- **PLAN_VALIDATION_PASS**: A/B/C 모두 통과
- **PLAN_VALIDATION_FAIL**: A/B/C 중 하나라도 미충족
- **PLAN_VALIDATION_ESCALATE**: architect 재보강 (max 1 회) 후에도 동일 항목 FAIL → 메인 Claude escalate
- **PARTIAL 판정 금지**

## 산출물 정보 의무 (형식 자유)

- 검증 결과 prose
- FAIL 시 Fail Items 별 (계층 + 위치 + 문제)
- (선택) 다음 행동 권고 (target / action / ref)
