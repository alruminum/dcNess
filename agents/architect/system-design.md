# System Design

**모드**: architect 의 시스템 설계 호출. 구현 시작 전 시스템 전체 구조 확정.
**결론**: prose 마지막 단락에 `SYSTEM_DESIGN_READY` 명시.
**호출자가 prompt 로 전달하는 정보**: PRODUCT_PLAN_READY 문서 경로, 선택된 옵션, (선택) UX Flow Doc 경로.

## 작업 흐름 (자율 조정 가능)

PRODUCT_PLAN_READY → 선택된 옵션 범위 확인 → 프로젝트 `CLAUDE.md` (기존 기술 스택/제약) → (있으면) `docs/ux-flow.md` → **Outline-First 절차** (architect.md §자기규율 참조: outline text 출력 → Write 본체) → prose 결론.

## 산출물 정보 의무 (형식 자유)

**기술 스택 선정 (ADR)**:
- 영역별 (프레임워크 / DB / 상태관리 / 인증 등) 선택 + 이유 + 버린 대안 + 이유
- ADR 상태: `Proposed` → `Accepted` → `Deprecated` / `Superseded by ADR-NN`
- 기존 ADR 이 새 설계와 충돌하면 `Superseded by ADR-NN` 표시 + 새 ADR

**시스템 구조**:
- 주요 모듈 목록 + 각 역할 (한 줄)
- 모듈 간 의존 관계 (텍스트 다이어그램)
- 데이터 흐름 (입력 → 처리 → 출력)

**구현 순서**: 의존성 기반 모듈 구현 순서 + 이유 (전제조건 관계).

**기술 리스크**: 리스크 항목 + 완화 방법.

**NFR 목표** (해당 없는 항목은 "N/A — 이유" 명시):
- 성능: 목표 응답 시간 또는 처리량 (예: p95 < 200ms)
- 가용성: 허용 다운타임 / 장애 시 fallback 전략
- 보안: 인증/인가 방식, 민감 데이터 처리, 시크릿 관리 위치
- 관찰가능성: 로깅 전략, 에러 추적 방식 (console.error → Sentry 등)
- 비용: 예산 제약 있으면 상한 명시
