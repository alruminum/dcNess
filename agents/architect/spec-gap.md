# SPEC_GAP

`@MODE:ARCHITECT:SPEC_GAP` → prose emit (마지막 단락에 결론 enum)

```
@PARAMS: { "gap_list": "SPEC_GAP_FOUND 갭 목록", "impl_path": "...", "current_depth": "simple|std|deep" }
@CONCLUSION_ENUM: SPEC_GAP_RESOLVED | PRODUCT_PLANNER_ESCALATION_NEEDED | TECH_CONSTRAINT_CONFLICT
```

engineer 로부터 SPEC_GAP_FOUND 피드백 받은 경우.

## 작업 순서

1. 갭 목록 분석
2. 해당 소스 파일 직접 확인
3. 계획 파일 보강 (갭 발생 섹션 수정)
4. READY_FOR_IMPL 게이트 재체크
5. **설계 문서 동기화** (아래 규칙)
6. prose 작성 → stdout

## 완료 후 설계 문서 동기화 (필수)

SPEC_GAP 처리로 로직·스키마·인터페이스 변경 시 아래 문서를 반드시 확인 + 불일치 시 즉시 수정.

| 변경 유형 | 동기화 대상 |
|---|---|
| 게임 로직·알고리즘·수치 변경 | `docs/game-logic.md` (또는 프로젝트 해당 문서) |
| 핵심 로직·상태머신·알고리즘 변경 | `trd.md` §3 |
| DB 스키마 변경 | `docs/db-schema.md` + `trd.md` §4 |
| SDK 연동 방식 변경 | `docs/sdk.md` + `trd.md` §5 |
| store 인터페이스 변경 | `trd.md` §6 |
| 화면·컴포넌트 스펙 변경 | `trd.md` §7 |

## prd.md 불일치 발견 시

architect 는 직접 수정하지 않는다. prose 마지막 단락에 `PRODUCT_PLANNER_ESCALATION_NEEDED` enum 출력 + 본문에 다음 정보 명시:

```markdown
## prd.md 불일치
- 현재 prd.md 내용: [해당 부분]
- 실제 구현/스펙: [무엇이 다른지]
- 권고: product-planner 에게 prd.md 수정 요청

## 결론

PRODUCT_PLANNER_ESCALATION_NEEDED
```

## 기술 제약 vs 비즈니스 요구 충돌 시

SPEC_GAP 분석 결과 "현재 기술 스택/제약으로 PRD 요구사항 구현 불가" 인 경우:

1. 즉시 구현 중단
2. prose 본문에 충돌 명시 + 마지막 단락에 `TECH_CONSTRAINT_CONFLICT`:

```markdown
## 충돌 내용
- PRD 요구사항: [구체]
- 기술 제약: [왜 불가능한지]
- 영향 범위: [어떤 기능 영향]

## 옵션
A. PRD 요구사항 축소 → product-planner 에게 스펙 변경 요청
B. 기술 스택 변경 → architect System Design 재설계 필요
C. 임시 우회 구현 → 기술 부채 명시 후 진행

## 권고: [A/B/C 중 하나 + 이유]

## 결론

TECH_CONSTRAINT_CONFLICT
```

3. 메인 Claude 가 product-planner 에스컬레이션 여부 결정
4. architect 가 직접 PRD 수정·"일단 하겠다" 진행 금지

## 정상 해결 시 prose 결론 예시

```markdown
## 작업 결과

3 건의 갭 분석 완료. impl §3 핵심 로직 + §5 의존성 보강. trd.md §3 동기화.

## 산출물
- impl_path: docs/impl/14-feature.md (보강)
- depth: std (변경 없음)

## 결론

SPEC_GAP_RESOLVED
```

## depth 재판정 (상향만 허용)

SPEC_GAP 처리 중 작업 범위가 커지면 depth 상향 가능 (simple → std → deep). 하향 금지.
prose 산출물 섹션에 `depth:` 변경 사실 명시.
