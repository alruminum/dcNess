# UX Validation

**모드**: validator 의 UX Flow 검증 호출. ux-architect 가 생성한 UX Flow Doc 이 PRD 요구사항을 충족하는지 검증.
**결론**: prose 마지막 단락에 `UX_REVIEW_PASS` / `UX_REVIEW_FAIL` / `UX_REVIEW_ESCALATE` 중 하나 명시.
**호출자가 prompt 로 전달하는 정보**: UX Flow Doc 경로 (`docs/ux-flow.md`), PRD 경로 (`prd.md`), 실행 식별자.

## 작업 순서

1. PRD (`prd.md`) 읽기
2. UX Flow Doc (`docs/ux-flow.md`) 읽기
3. 아래 체크리스트 수행
4. prose 작성 → stdout

## 검증 체크리스트

### 1. 화면 커버리지

- [ ] PRD 의 모든 기능이 하나 이상의 화면에 매핑되어 있는가?
- [ ] 화면 인벤토리에 PRD 범위 밖 화면이 포함되어 있지 않은가?

### 2. 플로우 완전성

- [ ] 모든 화면 간 이동 경로가 정의되어 있는가?
- [ ] 데드엔드(이동 불가 상태)가 없는가?
- [ ] 진입점(첫 화면)이 명확한가?

### 3. 상태 커버리지

- [ ] 각 화면의 필수 상태(로딩·빈 값·에러·정상)가 모두 정의되어 있는가?
- [ ] 에러 상태에서의 복구 경로가 있는가?

### 4. 인터랙션 정합성

- [ ] PRD 의 유저 시나리오(Happy path + Edge case)가 플로우에 반영되어 있는가?
- [ ] 수용 기준(Given/When/Then)과 인터랙션 정의가 일치하는가?

### 5. 디자인 테이블 완전성

- [ ] 화면 인벤토리의 모든 화면이 디자인 테이블에 포함되어 있는가?
- [ ] 우선순위(P0/P1/P2)가 할당되어 있는가?

## 판정 기준

- **UX_REVIEW_PASS**: 5 카테고리 모두 통과
- **UX_REVIEW_FAIL**: 하나라도 미충족
- **UX_REVIEW_ESCALATE**: ux-architect 재설계(max 1회) 후에도 FAIL

## prose 예시

### PASS

```markdown
## 검증 결과

5 카테고리 통과. 화면 12, 플로우 28, PRD 100% 매핑.

### Metrics
- screen_count: 12
- flow_path_count: 28
- prd_coverage_pct: 100

## 결론

UX_REVIEW_PASS
```

### FAIL

```markdown
## 검증 결과

3건의 위반 발견.

### Fail Items
- 1.화면 커버리지: PRD §3.4 'export 기능' 매핑 화면 부재
- 3.상태 커버리지: ScreenA 의 에러 상태 미정의
- 4.인터랙션 정합성: PRD §5 Edge case '네트워크 실패' 가 ScreenB 인터랙션에 미반영

### 다음 행동
- target: ux-architect / action: rework_flow / ref: docs/ux-flow.md — export 화면 추가
- target: ux-architect / action: rework_flow / ref: docs/ux-flow.md§ScreenA 에러 상태

### Metrics
- screen_count: 11
- flow_path_count: 24
- prd_coverage_pct: 87

## 결론

UX_REVIEW_FAIL
```

### ESCALATE

```markdown
## 검증 결과

재검에도 1.화면 커버리지 / 3.상태 커버리지 미해결. rework limit 1회 초과.

### 다음 행동
- target: main_claude / action: user_decision / ref: rework limit 1회 초과

## 결론

UX_REVIEW_ESCALATE
```
