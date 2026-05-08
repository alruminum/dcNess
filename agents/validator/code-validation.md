# Code Validation

**모드**: validator 의 코드 검증 호출. 구현 코드가 impl 계획과 일치하고 의존성 규칙을 지키며 시니어 관점 품질 기준을 충족하는지 검증.
**결론**: prose 마지막 단락에 *결론 + 권장 다음 단계* 자연어 명시. 권장 표현 (형식 강제 X): `PASS` (pr-reviewer 권고) / `FAIL` (engineer 재시도 권고) / `SPEC_MISSING` (architect SPEC_GAP 권고).
**호출자가 prompt 로 전달하는 정보**: impl 계획 파일 경로, 구현 파일 경로 목록, 실행 식별자.

## 작업 흐름 (자율 조정 가능)

1. 계획 파일 읽기 (`docs/impl/NN-*.md`). **미존재 시**: 즉시 FAIL 금지 — `docs/impl/00-decisions.md` → `CLAUDE.md` 작업 순서 → 그래도 없으면 `SPEC_MISSING` (prose 본문에 expected_path / fallback_searched / request 명시).
2. 설계 결정 / 구현 파일 / 의존 모듈 소스 읽기 (경계 위반 확인). **`docs/domain-model.md` 권한 read** — 도메인 invariant 위반 / 의존성 방향 위반 의심 시 참조. 수정 금지.
3. UI 모듈이면 design.md 읽기 (미존재 시 silent skip — `docs/design.md §5.1`).
4. 3 계층 체크리스트 적용.

## 3 계층 체크리스트

**A. 스펙 일치 — 하나라도 불일치 시 FAIL**:
- 생성 파일 (계획 목록 vs 실제)
- Props 타입 / 함수 시그니처 (계획 vs 구현)
- 핵심 로직 (계획의 의사코드/스니펫 vs 실제 흐름)
- 에러 처리 전략 (throw / 반환 / 상태)
- 주의사항 반영 / design.md 일치 (frontmatter 토큰 + 본문 룰 — 해당 시 색상·레이아웃·상태 UI)
- **design.md 토큰 참조 무결성** (design.md 존재 시): `{colors.X}` / `{typography.X}` / `{rounded.X}` / `{spacing.X}` / `{components.X}` 등 참조가 frontmatter 에 실재하는지 확인 (`docs/design.md §5.2` 정합). 미실재 참조 = FAIL

**B. 의존성 규칙 — 하나라도 위반 시 FAIL**:
- 외부 API/SDK 직접 import 금지 (래퍼 함수 사용)
- 계획에 없는 외부 패키지 신규 import 금지
- 다른 모듈 내부 상태 직접 변경 금지
- 전역 스토어는 계획 명시 액션만으로 접근
- DB 스키마 계약: impl plan 의 컬럼·타입·제약 vs 실제 스키마 일치
  - DB 변경 시 추가: 마이그레이션 파일 / Forward + Rollback DDL / generated types 동기화 확인

**C. 코드 품질 심층 검토 — 시니어 관점**:
- 경쟁 조건 (비동기 완료 순서 안전성)
- 메모리 누수 (setInterval/setTimeout/addEventListener 클린업)
- 불필요한 리렌더 (useCallback/useMemo 없이 매 렌더 객체 생성)
- 에러 전파 (Promise rejection catch 누락)
- 타입 안전성 (`as any`, `@ts-ignore`, 불필요 단언)
- 중복 로직 (3회+ 반복 + 추출 가능)
- 매직 넘버 / 의미 불명 리터럴 인라인
- 비동기 순서 (언마운트 후 setState)
- 렌더 안전성 (렌더 중 side effect 직접 실행)
- 의미론적 네이밍 ("helper" / "utils" / "manager" 책임 모호)
- 도메인 로직 누수 (UI 컴포넌트 안 비즈니스 로직)
- 적대적 시나리오 (동시 실행 / null 입력 / 네트워크 실패)

## 판정 기준

- **PASS**: A/B 모두 통과 + C 에서 치명적 문제 없음
- **FAIL**: A/B 위반 또는 C 의 프로덕션 위험 항목
- **SPEC_MISSING**: 계획 파일 + 대체 소스 모두 부재
- **PARTIAL 판정 금지**

## 산출물 정보 의무 (형식 자유)

- 검증 결과 prose
- FAIL 시 Fail Items 별 (계층 + 위치 + 문제)
- SPEC_MISSING 시 expected_path + fallback_searched + request
- (선택) 다음 행동 권고 (target / action / ref)

## 외부 도구 config 키 schema 검증 (자율)

`git diff` 또는 architect prose 의 변경 파일에 외부 도구 config (jest / tsconfig / eslint / vite / metro / babel 등) 변경 발견 시, 변경 키가 schema 에 *실존* 하는지 자율 판단으로 검증. hallucination 의심 시 공식 docs 1회 확인 또는 [`docs/plugin/known-hallucinations.md`](../../docs/plugin/known-hallucinations.md) 카탈로그 매칭. 잘못된 키 발견 시 FAIL + 정확한 키 제안.
