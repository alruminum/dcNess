# Task Decompose

**모드**: architect 의 epic stories → 기술 구현 단위 분해 호출. product-planner 완료 후 호출.
**결론**: 각 분해된 impl 파일 작성 후 prose 마지막 단락에 `READY_FOR_IMPL` 명시 (×N batch 가능).
**호출자가 prompt 로 전달하는 정보**: Epic stories.md 경로, 설계 문서 경로.

## 작업 흐름 (자율 조정 가능)

스토리 목록 확인 (GitHub Issues 우선: `mcp__github__list_issues` milestone=Epics + label=현재버전 / 폴백: `docs/milestones/vNN/epics/epic-NN-*/stories.md`) → 프로젝트 `CLAUDE.md` (기술 스택·제약) → `docs/impl/00-decisions.md` → **Outline-First 절차** (architect.md §자기규율 참조: impl 목차 출력 → 한 파일씩 순차 Write) → 각 스토리에 대응 기술 태스크 도출 → 태스크 등록 (GitHub `update_issue` body 체크리스트 / 폴백: stories.md 체크박스) → impl 파일 작성 → READY_FOR_IMPL 게이트 통과 확인.

## 태스크 도출 기준

- 한 태스크 = engineer 가 한 번 루프로 구현 가능한 단위
- 파일 1~3 개 생성/수정 범위
- 명확한 PASS/FAIL 판단 가능

## 듀얼 모드 가드레일 — 디자인 토큰 우선 (필수 검사)

UI 컴포넌트 포함 epic 분해 시, **`docs/ux-flow.md` 에 §0 디자인 가이드 존재 + `docs/design-handoff.md` 미존재** = **듀얼 모드**.

가드레일:
- **impl `01-theme-tokens.md` 강제 신설** (다른 UI impl 보다 앞 순번)
  - 생성 파일: `src/theme/colors.ts`, `typography.ts`, `spacing.ts`, `index.ts`
  - 내용: ux-flow §0 의 모든 토큰을 추상 키로 노출 (예: `colors.background.primary`, `colors.accent.gold`, `typography.heading`, `spacing.lg`)
  - 직접 hex/rem/font-name 박는 것 금지 — 모든 컴포넌트는 `theme.*` 경유
- **이후 모든 UI impl 의존성 명시**: `## 의존성` 에 `src/theme/` 1 줄
- **수용 기준 추가**: "직접 색상값/폰트명/픽셀값 사용 금지 — 모두 `theme.*` 경유"

근거: 디자인 시안 도착 후 토큰값만 patch 하면 컴포넌트 갈아엎기 0.

design-handoff.md 있는 경우 (B 모드 = 디자인 후 구현) 는 스킵.

## 산출물 정보 의무 (형식 자유)

- impl 목차 outline (파일명 + 다룰 스토리 + depth + 1 줄 요약 + 의존·순서)
- 추가된 태스크 (Story → impl 매핑)
- 생성된 impl 파일 목록 (경로 + depth + 가드레일 표시 — 듀얼 모드 시 `01-theme-tokens.md`)

## 각 impl 파일 형식 의무 (DCN-CHG-20260430-13)

각 impl batch 파일 (`docs/milestones/vNN/epics/epic-NN-*/impl/NN-*.md`) 은 다음 섹션 박는다 — `/impl` skill 의 MODULE_PLAN step skip 판정 근거:

```markdown
## 생성/수정 파일
- `src/foo.py` — <변경 요약 1줄>
- ...

## 인터페이스
- `foo(a: int, b: int) -> int` — <signature + 반환 의미>
- ...

## 의사코드
```python
def foo(a, b):
    if b == 0:
        raise ValueError(...)
    return a // b
```

## 결정 근거
- <왜 이 인터페이스 / 분기 / 에러 처리 채택했는지>

## 다른 모듈과의 경계
- <다른 impl 과의 의존 / 충돌 / 순서>

## MODULE_PLAN_READY
```

마지막 줄에 `MODULE_PLAN_READY` 마커 박음 = "이 batch 자체가 MODULE_PLAN 수준 detail 충족". `/impl` 가 이 마커 grep 후 architect MODULE_PLAN step skip → test-engineer 직진 (DCN-CHG-20260430-13).

마커 박지 않으면 (또는 위 섹션 미충족) `/impl` 가 architect MODULE_PLAN 정상 호출 — 본 컨벤션이 *권장* 이지 의무 아님 (메인 자율 + state-aware skip).

근거: RWHarness 의 plan_loop 가 의도했던 "산출물 있으면 통과 + 없으면 다시 호출" 패턴 정합. 분기 0 추가 (skill prompt 의 마커 grep 1줄만 추가).
