# Loop Catalog (8 loop × 컬럼 풀스펙)

> **Status**: ACTIVE
> **Origin**: `DCN-CHG-20260430-30` (loop-procedure.md split)
> **Scope**: dcness 8 loop 의 *행별 풀스펙* SSOT. 각 loop 의 entry_point / task_list / advance / clean_enum / branch_prefix / Step 4.5 적용 / Step 별 allowed_enums / 분기 / sub_cycles 단일 source.
> **Cross-ref**: 실행 절차 (Step 0~8 mechanics) = [`loop-procedure.md`](loop-procedure.md). 시퀀스 mini-graph + 결정표 = [`orchestration.md`](orchestration.md) §2~§7.

---

## 1. 한눈 인덱스

| loop | entry_point | task_list (Step 1) | advance | clean_enum | expected_steps |
|------|-------------|--------------------|---------|------------|----------------|
| `feature-build-loop` (§3.1, §2) | `product-plan` | product-planner / plan-reviewer / ux-architect:UX_FLOW / validator:UX_VALIDATION / architect:SYSTEM_DESIGN / validator:DESIGN_VALIDATION / architect:TASK_DECOMPOSE | `PRODUCT_PLAN_READY` → `PLAN_REVIEW_PASS` → `UX_FLOW_READY` → `PASS` → `SYSTEM_DESIGN_READY` → `DESIGN_REVIEW_PASS` → `READY_FOR_IMPL` | advance 동일 | 7 |
| `impl-task-loop` (§2.1, §3) | `impl` | architect:MODULE_PLAN / test-engineer / engineer:IMPL / validator:CODE_VALIDATION / pr-reviewer | `READY_FOR_IMPL` → `TESTS_WRITTEN` → `IMPL_DONE` → `PASS` → `LGTM` | advance 동일 | 5 |
| `impl-ui-design-loop` (§2.2, §4) | `impl` (UI 감지) | architect:MODULE_PLAN / designer / design-critic / test-engineer / engineer:IMPL / validator:CODE_VALIDATION / pr-reviewer | `READY_FOR_IMPL` → `DESIGN_READY_FOR_REVIEW` → `VARIANTS_APPROVED` → `TESTS_WRITTEN` → `IMPL_DONE` → `PASS` → `LGTM` | advance 동일 | 7 |
| `quick-bugfix-loop` (§3.5, §5) | `quick` | qa / architect:LIGHT_PLAN / engineer:IMPL / validator:BUGFIX_VALIDATION / pr-reviewer | `FUNCTIONAL_BUG`/`CLEANUP` → `LIGHT_PLAN_READY` → `IMPL_DONE` → `PASS` → `LGTM` | advance 동일 | 5 |
| `qa-triage` (§3.6, §6) | `qa` | qa | (5 enum 모두 — 라우팅 추천) | advance 개념 X | 1 |
| `ux-design-stage` (§3.2, §7) | `ux` | ux-architect:UX_FLOW / designer:SCREEN(THREE_WAY) / design-critic | `UX_FLOW_READY` → `DESIGN_READY_FOR_REVIEW` → `VARIANTS_APPROVED` | advance 동일 | 3 |
| `ux-refine-stage` (§3.3, §8) | `ux` (REFINE) | ux-architect:UX_REFINE / designer:SCREEN(THREE_WAY) / design-critic | `UX_REFINE_READY` → `DESIGN_READY_FOR_REVIEW` → `VARIANTS_APPROVED` | advance 동일 | 3 |
| `direct-impl-loop` (§3.4, §9) | `impl_driver` (future) | `impl-task-loop` 동일 | `impl-task-loop` 동일 | `impl-task-loop` 동일 | 5 |

§3.X = orchestration.md mini-graph 행. §N = 본 문서 행별 풀스펙.

---

## 2. `feature-build-loop` 풀스펙

**branch_prefix**: commit X (spec/design 종료, 구현 진입은 별도 루프).
**Step 4.5 적용**: X.

**Step 별 allowed_enums** (`end-step --allowed-enums`):
| step | agent[:mode] | allowed_enums |
|---|---|---|
| 2 | product-planner | `PRODUCT_PLAN_READY,CLARITY_INSUFFICIENT,PRODUCT_PLAN_CHANGE_DIFF,PRODUCT_PLAN_UPDATED,ISSUES_SYNCED` |
| 3 | plan-reviewer | `PLAN_REVIEW_PASS,PLAN_REVIEW_CHANGES_REQUESTED` |
| 4 | ux-architect:UX_FLOW | `UX_FLOW_READY,UX_FLOW_PATCHED,UX_REFINE_READY,UX_FLOW_ESCALATE` |
| 5 | validator:UX_VALIDATION | `PASS,FAIL` |
| 6 | architect:SYSTEM_DESIGN | `SYSTEM_DESIGN_READY` |
| 6.5 | validator:DESIGN_VALIDATION | `DESIGN_REVIEW_PASS,DESIGN_REVIEW_FAIL,DESIGN_REVIEW_ESCALATE` |
| 7 | architect:TASK_DECOMPOSE | `READY_FOR_IMPL` |

**분기**:
- `PRODUCT_PLAN_UPDATED` → plan-reviewer skip + ux-architect 직행 (이전 PLAN_REVIEW_PASS 활용)
- `PRODUCT_PLAN_CHANGE_DIFF` → plan-reviewer 변경분만 재심사
- `CLARITY_INSUFFICIENT` → 사용자 역질문 후 product-planner 재호출
- `ISSUES_SYNCED` → 동기화 완료, 종료
- `PLAN_REVIEW_CHANGES_REQUESTED` → product-planner 재진입 (cycle ≤ 2)
- `UX_REFINE_READY` → designer SCREEN 분기 (ux-design-stage 또는 ux-refine-stage 진입 권장)
- `UX_FLOW_ESCALATE` → 사용자 위임
- validator UX `FAIL` → ux-architect 재진입 (cycle ≤ 2)
- `DESIGN_REVIEW_FAIL` → architect:SYSTEM_DESIGN 재진입 (cycle ≤ 2)
- `DESIGN_REVIEW_ESCALATE` → 사용자 위임

**sub_cycles**: 위 분기에서 재호출 시 step 이름 컨벤션 = `<agent>-RETRY-<n>` (별도 begin/end-step 1쌍, DCN-30-25).

---

## 3. `impl-task-loop` 풀스펙

**branch_prefix decision rule**:
- task 내 신규 기능 (src 신규 파일 또는 인터페이스 추가) → `feat/<task-slug>`
- 리팩토링 / 정리 / 테스트 보강 only → `chore/<task-slug>`
- 버그픽스 (의도 vs 실제 격차 수정) → `fix/<task-slug>`
- 메인 Claude 가 task 의 ## 변경 요약 / engineer prose 보고 결정.

**3-commit 구조** (`loop-procedure.md §3.4` 참조 — catastrophic gate §2.3.6~§2.3.8):
| stage | 시점 | 내용 |
|---|---|---|
| commit1 (docs) | MODULE_PLAN READY_FOR_IMPL 직후 | docs/impl/NN.md 등 + `record-stage-commit docs` |
| commit2 (tests) | TESTS_WRITTEN 직후 | test 파일 + `record-stage-commit tests` |
| commit3 (src) + PR | CODE_VALIDATION PASS 직후 | src 파일 + push + `gh pr create` + `record-stage-commit src` |
| merge | LGTM 직후 | `gh pr merge` (NO --squash — 3 commit 히스토리 보존) |

**Step 4.5 적용**: ✓ (engineer `IMPL_DONE` 직후, validator 진입 *전* — `loop-procedure.md` §4 참조).

**Step 별 allowed_enums**:
| step | agent[:mode] | allowed_enums |
|---|---|---|
| 2 | architect:MODULE_PLAN | `READY_FOR_IMPL,SPEC_GAP_FOUND,TECH_CONSTRAINT_CONFLICT` |
| 3 | test-engineer | `TESTS_WRITTEN,SPEC_GAP_FOUND` |
| 4 | engineer:IMPL | `IMPL_DONE,IMPL_PARTIAL,SPEC_GAP_FOUND,TESTS_FAIL,IMPLEMENTATION_ESCALATE` |
| 5 | validator:CODE_VALIDATION | `PASS,FAIL,SPEC_MISSING` |
| 6 | pr-reviewer | `LGTM,CHANGES_REQUESTED` |

**분기**:
- `IMPL_PARTIAL` → engineer:IMPL-SPLIT-<n> 재호출 (split < 3, 새 context window — DCN-30-34). cycle 초과 시 `IMPLEMENTATION_ESCALATE` (작업 분해 부족 — architect TASK_DECOMPOSE 재진입 권고).
- `SPEC_GAP_FOUND` → architect:SPEC_GAP cycle (≤ 2) → engineer 재진입
- `TESTS_FAIL` → engineer:IMPL-RETRY-<n> (attempt < 3, cycle 초과 → `IMPLEMENTATION_ESCALATE`)
- `SPEC_MISSING` → architect:SPEC_GAP
- `TECH_CONSTRAINT_CONFLICT` / `IMPLEMENTATION_ESCALATE` → 사용자 위임
- `CHANGES_REQUESTED` → engineer:POLISH-<n> cycle (≤ 2)
- `validator:FAIL` → engineer:IMPL-RETRY-<n>

**sub_cycles**:
- `architect:SPEC_GAP` (engineer/test-engineer SPEC_GAP_FOUND 시) — allowed_enums = `SPEC_GAP_RESOLVED,PRODUCT_PLANNER_ESCALATION_NEEDED,TECH_CONSTRAINT_CONFLICT`
- `engineer:POLISH-<n>` (CHANGES_REQUESTED 시, ≤ 2) — allowed_enums = `POLISH_DONE,IMPLEMENTATION_ESCALATE`
- `engineer:IMPL-RETRY-<n>` (TESTS_FAIL/FAIL 시, attempt < 3) — allowed_enums = engineer:IMPL 동일
- `engineer:IMPL-SPLIT-<n>` (IMPL_PARTIAL 시, split < 3, DCN-30-34) — allowed_enums = engineer:IMPL 동일. prose 의 `## 남은 작업` 컨텍스트로 진입.

**state-aware skip** (DCN-CHG-30-13): task 파일 끝에 `MODULE_PLAN_READY` 마커 박혀있으면 Step 2 (architect:MODULE_PLAN) skip — TaskUpdate completed("skipped") + prose 종이는 task 파일 자체를 `<RUN_DIR>/architect-MODULE_PLAN.md` 로 복사. catastrophic 룰 §2.3.3 통과용.

---

## 4. `impl-ui-design-loop` 풀스펙

**branch_prefix decision rule**: `impl-task-loop` 와 동일 (`feat` / `chore` / `fix`).
**Step 4.5 적용**: ✓ (engineer `IMPL_DONE` 직후).

**Step 별 allowed_enums**:
| step | agent[:mode] | allowed_enums |
|---|---|---|
| 2 | architect:MODULE_PLAN | `impl-task-loop` 동일 |
| 3 | designer:SCREEN(THREE_WAY) | `DESIGN_READY_FOR_REVIEW,DESIGN_LOOP_ESCALATE` |
| 4 | design-critic | `VARIANTS_APPROVED,VARIANTS_ALL_REJECTED,UX_REDESIGN_SHORTLIST` |
| 5 | test-engineer | `impl-task-loop` 동일 |
| 6 | engineer:IMPL | `impl-task-loop` 동일 |
| 7 | validator:CODE_VALIDATION | `impl-task-loop` 동일 |
| 8 | pr-reviewer | `impl-task-loop` 동일 |

**분기**:
- `VARIANTS_ALL_REJECTED` → designer:SCREEN 재호출 (round < 3)
- `UX_REDESIGN_SHORTLIST` → ux-architect:UX_REFINE (round ≥ 3, ux-refine-stage 진입)
- `DESIGN_LOOP_ESCALATE` → 사용자 위임
- 나머지 = `impl-task-loop` 분기 동일

**sub_cycles**: `impl-task-loop` 동일 + `designer:SCREEN-ROUND-<n>` (variants 재생성, round < 3).

---

## 5. `quick-bugfix-loop` 풀스펙

**branch_prefix decision rule**:
- qa enum `FUNCTIONAL_BUG` → `fix/<slug>`
- qa enum `CLEANUP` → `chore/<slug>`
- 그 외 → 자동 진행 X (라우팅 추천 후 종료)

**Step 4.5 적용**: △ (light path — stories.md 갱신은 사용자 결정. backlog 변경 X).

**Step 별 allowed_enums**:
| step | agent[:mode] | allowed_enums |
|---|---|---|
| 2 | qa | `FUNCTIONAL_BUG,CLEANUP,DESIGN_ISSUE,KNOWN_ISSUE,SCOPE_ESCALATE` |
| 3 | architect:LIGHT_PLAN | `LIGHT_PLAN_READY,SPEC_GAP_FOUND,TECH_CONSTRAINT_CONFLICT` |
| 4 | engineer:IMPL | `IMPL_DONE,IMPL_PARTIAL,SPEC_GAP_FOUND,TESTS_FAIL,IMPLEMENTATION_ESCALATE` |
| 5 | validator:BUGFIX_VALIDATION | `PASS,FAIL` |
| 6 | pr-reviewer | `LGTM,CHANGES_REQUESTED` |

**qa 분기**:
- `DESIGN_ISSUE` → 종료 + ux-design-stage 추천 (구현 후)
- `KNOWN_ISSUE` → 종료
- `SCOPE_ESCALATE` → 사용자 위임 (분류 모호)

**sub_cycles**: `impl-task-loop` 와 동일 (`SPEC_GAP` / `POLISH` / `IMPL-RETRY`). test-engineer 단계가 없으므로 TESTS_FAIL 은 engineer 자체 검증 실패 의미.

---

## 6. `qa-triage` 풀스펙

**branch_prefix**: commit X (분류만, 코드 변경 X).
**Step 4.5 적용**: X.

**Step 별 allowed_enums**:
| step | agent[:mode] | allowed_enums |
|---|---|---|
| 2 | qa | `FUNCTIONAL_BUG,CLEANUP,DESIGN_ISSUE,KNOWN_ISSUE,SCOPE_ESCALATE` |

**enum 별 라우팅 추천** (advance 개념 없음 — 메인이 사용자 결정 받음):
- `FUNCTIONAL_BUG` → `quick-bugfix-loop` (`/quick`) 또는 `impl-task-loop`
- `CLEANUP` → `quick-bugfix-loop` (`/quick`) 또는 engineer 직접
- `DESIGN_ISSUE` → `ux-design-stage` (`/ux`) 또는 designer 직접
- `KNOWN_ISSUE` → 종료
- `SCOPE_ESCALATE` → 사용자 위임 (큰 변경 / 다중 모듈)

**sub_cycles**: 없음. AMBIGUOUS 시 [`process/dcness-guidelines.md`](process/dcness-guidelines.md) §6 cascade.

---

## 7. `ux-design-stage` 풀스펙

**branch_prefix**: commit X (design handoff, 코드 X).
**Step 4.5 적용**: X.

**Step 별 allowed_enums**:
| step | agent[:mode] | allowed_enums |
|---|---|---|
| 2 | ux-architect:UX_FLOW | `UX_FLOW_READY,UX_FLOW_PATCHED,UX_REFINE_READY,UX_FLOW_ESCALATE` |
| 3 | designer:SCREEN(THREE_WAY) | `DESIGN_READY_FOR_REVIEW,DESIGN_LOOP_ESCALATE` |
| 4 | design-critic | `VARIANTS_APPROVED,VARIANTS_ALL_REJECTED,UX_REDESIGN_SHORTLIST` |

**designer mode**: THREE_WAY 권장 (3 variant + critic 심사). 사용자 발화에 "한 안만" / "ONE" 키워드 시 ONE_WAY (allowed_enums = `DESIGN_READY_FOR_REVIEW,DESIGN_LOOP_ESCALATE`, design-critic 단계 제거 → expected_steps = 2).

**분기**:
- `VARIANTS_APPROVED` → 사용자 PICK 1개 (메인이 사용자에게 variant 번호 받음) → DESIGN_HANDOFF 패키지 출력 → 종료
- `VARIANTS_ALL_REJECTED` → designer 재호출 (round < 3)
- `UX_REDESIGN_SHORTLIST` → ux-refine-stage 진입
- `UX_REFINE_READY` (ux-architect) → ux-refine-stage 진입
- `DESIGN_LOOP_ESCALATE` / `UX_FLOW_ESCALATE` → 사용자 위임

**sub_cycles**: `designer:SCREEN-ROUND-<n>` (round < 3).

---

## 8. `ux-refine-stage` 풀스펙

**branch_prefix**: commit X.
**Step 4.5 적용**: X.

**Step 별 allowed_enums**:
| step | agent[:mode] | allowed_enums |
|---|---|---|
| 2 | ux-architect:UX_REFINE | `UX_REFINE_READY,UX_FLOW_ESCALATE` |
| 2.5 | (사용자 승인) | — (메인이 사용자에게 ux refine 결과 검토 요청. 거절 시 ux-architect 재호출) |
| 3 | designer:SCREEN(THREE_WAY) | `DESIGN_READY_FOR_REVIEW,DESIGN_LOOP_ESCALATE` |
| 4 | design-critic | `VARIANTS_APPROVED,VARIANTS_ALL_REJECTED,UX_REDESIGN_SHORTLIST` |

**designer mode**: ux-design-stage 와 동일 (THREE_WAY 권장 / "한 안만" 시 ONE_WAY).

**Step 2.5 — 사용자 승인**: ux-architect UX_REFINE_READY 후 designer 진입 *전* 메인이 사용자에게 refine 결과 prose 발췌 + 진행 여부 확인. 사용자 거절 시 ux-architect 재호출 (cycle ≤ 2). step 컨벤션 = `user-approval-2.5` (helper begin/end-step 비대상 — 사용자 단계).

**분기**: `ux-design-stage` 와 동일.

---

## 9. `direct-impl-loop` 풀스펙

`impl-task-loop` 와 100% 동일. 차이점:
- entry_point = `impl_driver` CLI (현재 미구현, 후속 Task 예정)
- 사용자 task 경로 직접 명시 (skill UI 없음)

allowed_enums / 분기 / sub_cycles / branch_prefix decision rule / Step 4.5 = §3 (`impl-task-loop`) 인용.

---

## 10. 다중 task chain (`impl-loop`)

`/impl-loop` = `impl-task-loop` × N. outer task `impl-<i>: <task>` + inner 5 sub-task `b<i>.<agent>` (DCN-CHG-30-12). 각 task clean → 자동 7a + 다음 task. caveat → 멈춤 + 사용자 위임 (Step 2.5 — `commands/impl-loop.md` 참조).

## 11. catastrophic 룰 정합

[`orchestration.md`](orchestration.md) §2.3 4룰 + §7.1 HARNESS_ONLY_AGENTS = `hooks/catastrophic-gate.sh` 강제. 본 카탈로그의 각 loop sequence 가 이 룰 자연 충족 (validator → pr-reviewer 직전 PASS / engineer 직전 plan READY / TASK_DECOMPOSE 직전 DESIGN_REVIEW_PASS / PRD 변경 후 plan-reviewer + ux-architect 검토).

---

## 12. 참조

- [`loop-procedure.md`](loop-procedure.md) — Step 0~8 mechanics SSOT
- [`orchestration.md`](orchestration.md) §2~§7 — 시퀀스 mini-graph + 결정표 + retry + escalate + handoff
- [`process/dcness-guidelines.md`](process/dcness-guidelines.md) — echo / Step 기록 / yolo / AMBIGUOUS / worktree / 결과 출력 / 권한 요청 / Karpathy
