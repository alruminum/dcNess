# Technical Epic

> ⚠️ **CRITICAL — extended thinking 본문 드래프트 금지**. thinking = 의사결정 분기만. epic 본문 / 영향도 분석 / 마이그레이션 단계 = thinking 종료 *후* 즉시 emit 또는 `Write` 입력값 안에서만. THINKING_LOOP 회귀 회피 (DCN-30-20). master 룰: `agents/architect.md` §자기규율.

**모드**: architect 의 기술 에픽 작성 호출 — 기술 부채/인프라/리팩토링/아키텍처 변경.
**결론**: prose 마지막 단락에 `SYSTEM_DESIGN_READY` 명시.
**호출자가 prompt 로 전달하는 정보**: 개선 목표 설명, 영향 범위.

기능 에픽 (비즈니스 가치 중심) 은 product-planner 영역이므로 제외.

**해당 유형**: DB 마이그레이션 / 스키마 정합성 복구 / 타입 안전성 개선 (타입 자동화·any 제거) / 성능·보안·의존성 개선 / 코드 구조 리팩토링.

## 작업 흐름 (자율 조정 가능)

다음 에픽 번호 확인 (GitHub Issues 우선: `mcp__github__list_issues` milestone=Epics / 폴백: `backlog.md`) → 에픽 + 스토리 이슈 등록 (GitHub `create_issue` + sub-issue 연결, milestone 반드시 포함 / 폴백: `docs/milestones/vNN/epics/epic-NN-*/stories.md` + `backlog.md` 행 추가) → 프로젝트 `CLAUDE.md` 에픽 목록 섹션 업데이트 → 필요 시 각 스토리에 대응 impl 파일 작성 (Module Plan 실행) → 결론 emit.

**Epic 제목 형식**: `[{milestone_name}] Epic N: 에픽 이름` (예: `[v1] Epic 3: 인증 시스템 리팩토링`).
**Story 제목 형식**: `[{milestone_name}] Story N: 스토리 설명`.

## Epic / Story 본문 정보 의무 (형식 자유)

**Epic**: 목적 (기술 목표) / 스토리 목록 / 완료 기준.
**Story**: 목표 (달성할 것) / 구현 태스크 / 완료 기준.

## 산출물 정보 의무 (형식 자유)

- 생성된 에픽 (이름)
- 스토리 N 개
- 업데이트된 파일 (backlog.md / CLAUDE.md)
