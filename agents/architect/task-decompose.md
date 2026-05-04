# Task Decompose

> ⚠️ **CRITICAL — extended thinking 본문 드래프트 금지** (DCN-CHG-20260430-39). thinking = 의사결정 분기만. impl 목차 / 각 impl 본문 / 의사코드 = thinking 종료 *후* 즉시 emit 또는 `Write` 입력값 안에서만. thinking 안에서 본문 회전 시 THINKING_LOOP 회귀 (DCN-30-20). master 룰: `agents/architect.md` §자기규율.

**모드**: architect 의 epic stories → 기술 구현 단위 분해 호출. product-planner 완료 후 호출.
**결론**: 각 분해된 impl 파일 작성 후 prose 마지막 단락에 `READY_FOR_IMPL` 명시 (×N task 가능).
**호출자가 prompt 로 전달하는 정보**: Epic stories.md 경로, 설계 문서 경로.

## 작업 흐름 (자율 조정 가능)

스토리 목록 확인 (GitHub Issues 읽기 — [`docs/issue-lifecycle.md`](../../docs/issue-lifecycle.md) §1 에 따라 product-planner 가 보장. 부재 시 issue-lifecycle §6 pre-flight gate STOP) → 프로젝트 `CLAUDE.md` (기술 스택·제약) → `docs/impl/00-decisions.md` → **Outline-First 절차** (architect.md §자기규율 참조: impl 목차 출력 → 한 파일씩 순차 Write) → 각 스토리에 대응 기술 태스크 도출 → 태스크 등록 (stories.md 체크박스) → impl 파일 작성 → READY_FOR_IMPL 게이트 통과 확인.

## 태스크 도출 기준

- 한 태스크 = engineer 가 한 번 루프로 구현 가능한 단위
- 파일 1~3 개 생성/수정 범위
- 명확한 PASS/FAIL 판단 가능
- **DCN-CHG-20260430-16 추가** — 분할 단위 정합 검증:
  - 각 task 가 *test-engineer 관점에서 명확히 테스트 가능* 한지 (`docs/domain-model.md` + `docs/architecture.md` 의 의존성 그래프 참조)
  - 같은 변경 이유로 묶이는가 (SRP 정합 — UI + 비즈니스 로직 한 task X)
  - 의존성 1 묶음 = 1 task (system-design 의 모듈 분할과 정합)
  - 분할 미달 시 architect SYSTEM_DESIGN 재진입 또는 SPEC_GAP escalate

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

## Story 이슈 — 생성 책임 X (product-planner 단독)

본 agent 는 story 이슈를 *생성하지 않는다*. story 이슈는 [`docs/issue-lifecycle.md`](../../docs/issue-lifecycle.md) §1.3 에 따라 `product-planner` 가 PRODUCT_PLAN_READY 직후 등록. 본 agent 는 *읽기만* — stories.md 상단/Story 헤더 직하의 `**GitHub Issue:** [#N](url)` 매치 사용.

매치 부재 시 (issue-lifecycle §6 pre-flight gate 위반) → 즉시 STOP, 메인이 사용자에게 product-planner 재진입 또는 §3 미등록 모드 명시 요청.

## 산출물 정보 의무 (형식 자유)

- impl 목차 outline (파일명 + 다룰 스토리 + depth + 1 줄 요약 + 의존·순서)
- 추가된 태스크 (Story → impl 매핑)
- 생성된 impl 파일 목록 (경로 + depth + 가드레일 표시 — 듀얼 모드 시 `01-theme-tokens.md`)
- 생성된 GitHub story 이슈 번호 목록 (Story 1 → #N, Story 2 → #M, …)

## impl 파일 명명 + H1 제목 (DCN-CHG-20260501-05)

### 파일명
`impl/NN-<slug>.md` — `NN` = 에픽 내 독립 순번 (전역 누적 X). `slug` = kebab-case 1줄 요약.

### H1 형식 (강제)
`# impl/NN — [Story Xa / #issue] <한 줄 요약>`

- `Story Xa` — Story 번호 + 분할 시 `a/b/c` 접미사 (예: `Story 4a`)
- `#issue` — GitHub Story 이슈 번호 (issue-lifecycle.md §3 미등록 모드 시 생략 허용)
- 둘 다 같은 `[ ]` 안 — 한눈 매핑.

**Why**: impl 단독 open / `grep` 시 H1 만으로 어느 Story / 이슈인지 즉시 파악. frontmatter 메타는 ToC 안 보임. 8 task ↑ epic 검색 시 H1 prefix 가 가장 빠름.

**예**:
- ✅ `# impl/01 — [Story 1a / #167] S04+S05 컴포넌트 mock __esModule 통일`
- ✅ `# impl/01 — [Story 1a] <요약>` (미등록 모드 — issue-lifecycle §3)
- ❌ `# impl/01 — S04+S05 …` (Story prefix 누락)
- ❌ `# impl/05 — google-signin (Story 4a)` (괄호 표기 — `[ ]` 강제)

### 자가 검증 (TASK_DECOMPOSE 종료 전)
모든 `impl/NN-*.md` H1 정규식 매치 확인:
```
^# impl/\d{2} — \[Story \d+[a-z]?( / #\d+)?\] 
```
정식 등록 epic 이면 `#\d+` 필수 (issue-lifecycle §3 미등록 모드 stories.md 명시 시만 생략 허용). 위반 1건이라도 발견 시 즉시 정정 후 종료.

## 각 impl 파일 형식 의무 (DCN-CHG-20260430-13)

각 impl task 파일 (`docs/milestones/vNN/epics/epic-NN-*/impl/NN-*.md`) 은 다음 섹션 박는다 — `/impl` skill 의 MODULE_PLAN step skip 판정 근거:

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

마지막 줄에 `MODULE_PLAN_READY` 마커 박음 = "이 task 자체가 MODULE_PLAN 수준 detail 충족". `/impl` 가 이 마커 grep 후 architect MODULE_PLAN step skip → test-engineer 직진 (DCN-CHG-20260430-13).

마커 박지 않으면 (또는 위 섹션 미충족) `/impl` 가 architect MODULE_PLAN 정상 호출 — 본 컨벤션이 *권장* 이지 의무 아님 (메인 자율 + state-aware skip).

근거: RWHarness 의 plan_loop 가 의도했던 "산출물 있으면 통과 + 없으면 다시 호출" 패턴 정합. 분기 0 추가 (skill prompt 의 마커 grep 1줄만 추가).

## 외부 도구 config 키 — 학습 데이터 노이즈 주의

task 에 외부 도구 (jest / tsconfig / eslint / vite / metro / babel / package.json scripts 등) config 키 등장 시 의심하면 [`docs/known-hallucinations.md`](../../docs/known-hallucinations.md) 카탈로그 확인 또는 공식 docs WebFetch 권고. 자율 판단 — 강제 X.

## 참조

- 이슈 생명주기 (생성·완료·미등록): [`docs/issue-lifecycle.md`](../../docs/issue-lifecycle.md)
