# Docs Sync

> ⚠️ **CRITICAL — extended thinking 본문 드래프트 금지**. thinking = 의사결정 분기만. docs 동기화 patch 본문 = thinking 종료 *후* 즉시 emit 또는 `Edit/Write` 입력값 안에서만. THINKING_LOOP 회귀 회피 (DCN-30-20). master 룰: `agents/architect.md` §자기규율.

**모드**: architect 의 docs 동기화 호출 — impl 완료 후 참조 설계 문서에 파생 서술 추가. 새 설계 결정은 절대 하지 않는다.
**결론**: prose 마지막 단락에 *결론 + 권장 다음 단계* 자연어 명시. 권장 표현 (형식 강제 X): `DOCS_SYNCED` (동기화 완료, 후속 없음) / `SPEC_GAP_FOUND` (갭 발견, architect SPEC_GAP 권고) / `TECH_CONSTRAINT_CONFLICT` (기술 제약 충돌, 사용자 위임).
**호출자가 prompt 로 전달하는 정보**: 이미 구현 완료된 impl 경로, 동기화 대상 docs 파일 목록.

**사용처**: impl_loop 완료 후 문서 2~3 건 동기화가 남았을 때. 메인 Claude 가 직접 호출 가능.

## 호출 조건 (모두 만족 필수)

하나라도 어긋나면 결론 `TECH_CONSTRAINT_CONFLICT`:
1. `impl_path` 가 실제 존재 + `## 생성/수정 파일` 목록에 `docs_targets` 포함
2. 대상 impl 이 이미 src 구현·merge 완료 상태 (validator 통과 이력 있음)
3. 수정 범위가 **기존 섹션 추가/확장**. 기존 설계 결정 변경이나 DDL 재작성 금지

## 작업 흐름 (자율 조정 가능)

`impl_path` 읽기 (`## 생성/수정 파일` + `## 인터페이스 정의` + `## 수용 기준`) → `docs_targets` 각 파일 읽기 (현재 상태) → impl 에 이미 확정된 사실 (함수 시그니처·DDL·플로우 단계) 만 docs 에 **파생 서술** 추가. 기존 문서의 컨벤션 (섹션 순서·표 포맷·톤) 그대로 유지.

## 권한 경계 (catastrophic)

- **새 설계 결정 금지** — impl 에 없는 함수·테이블·플로우를 docs 에 추가 금지
- **기존 섹션 재작성 금지** — 삭제/치환 금지. 섹션 추가 또는 표 행 추가만 허용
- **impl 파일 수정 금지** — impl 은 이미 확정된 계약
- **src/ 수정 금지** — 구현 이미 완료
- **architecture.md / db-schema.md 이외 docs 수정 요청 거부** — 그 외는 MODULE_PLAN / SYSTEM_DESIGN 경로
- **권한/툴 부족 시 사용자에게 명시 요청** — sync 에 필요한 도구·권한·정보 부족 시 *추측 진행 X*. 메인 Claude 에게 명시 요청 후 진행. (Karpathy 원칙 1 정합)

## 위반 시 권장 결론 (자연어)

- impl 에 명시 안 된 새 설계가 필요 → `SPEC_GAP_FOUND` (MODULE_PLAN 재호출 유도)
- 대상 docs 가 architect 소유 아님 (design.md / ux-flow 등) → `TECH_CONSTRAINT_CONFLICT` (해당 에이전트 경유)
- 수정 범위가 "섹션 추가" 가 아닌 기존 설계 변경 → `TECH_CONSTRAINT_CONFLICT` (MODULE_PLAN 경로)

## 산출물 정보 의무 (형식 자유)

- 수정 파일 목록 (각 추가된 섹션 명시)
- 추가 근거 (impl 의 어떤 섹션과 1:1 대응하는지)
