---
name: product-plan
description: 새 기능 / PRD 변경 / 큰 기획을 받아 product-planner → plan-reviewer → ux-architect → validator UX_VALIDATION → architect SYSTEM_DESIGN → validator DESIGN_VALIDATION → architect TASK_DECOMPOSE 시퀀스로 spec/design 단계까지 진행하는 스킬. 사용자가 "기획자야", "새 기능", "피쳐 추가", "이런 기능이 필요할 것 같아", "기획해줘", "프로덕트 플랜", "/product-plan" 등을 말할 때 반드시 이 스킬을 사용한다. dcNess 컨베이어 패턴 (Task tool + Agent + helper + 훅) 으로 동작. 구현 진입은 별도 (`/quick` 또는 정식 impl 루프).
---

# Product Plan Skill — spec/design 흐름

> 공통 룰 (가시성 / AMBIGUOUS / Catastrophic / yolo / worktree) SSOT = `commands/quick.md`. 본 skill 은 시퀀스 + 분기만 명세.

## 사용

- 트리거: "새 기능", "피쳐", "기획", "PRD 변경", "프로덕트 플랜"
- 비대상: 버그 → `/qa` · 한 줄 수정 → `/quick` · 디자인만 → `/ux`

## 시퀀스 (orchestration §3.1)

```
product-planner → plan-reviewer → ux-architect → validator UX_VALIDATION
  → architect SYSTEM_DESIGN → validator DESIGN_VALIDATION → architect TASK_DECOMPOSE
```

## 절차

### Step 0a — worktree 격리 (선택)

발화에 `worktree` / `wt` / `격리` / `isolate` 시 `EnterWorktree(name="product-plan-{ts_short}")`.

### Step 0b — run 시작

```bash
HELPER="$(ls -d ${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/plugins/cache/dcness/dcness/*} 2>/dev/null | head -1)/scripts/dcness-helper"
RUN_ID=$("$HELPER" begin-run product-plan)
echo "[product-plan] run started: $RUN_ID"
```

사용자 확인 (요청 / 작업 유형 추정 / 시퀀스 / 진행할까요).

### Step 1 — 7 task 등록

```
TaskCreate("product-planner: PRD 작성")
TaskCreate("plan-reviewer: PRD 심사")
TaskCreate("ux-architect: UX_FLOW")
TaskCreate("validator: UX_VALIDATION")
TaskCreate("architect: SYSTEM_DESIGN")
TaskCreate("validator: DESIGN_VALIDATION")
TaskCreate("architect: TASK_DECOMPOSE")
```

### Step 2~7 — 각 단계 표

매 단계 골격 동일:

```
TaskUpdate("<task>", in_progress)
"$HELPER" begin-step <agent> [<MODE>]
Agent(subagent_type="<agent>", mode="<MODE>", description="...")
# DCN-30-21: prose-file 을 run-dir 안 격리 (멀티세션 안전)
RUN_DIR=$("$HELPER" run-dir)
mkdir -p "$RUN_DIR/.prose-staging"
PROSE_PATH="$RUN_DIR/.prose-staging/<n>.md"
# (메인이 sub-agent prose 를 위 경로에 Write)
ENUM=$("$HELPER" end-step <agent> [<MODE>] --allowed-enums "<list>" --prose-file "$PROSE_PATH")
# 의무 echo (commands/quick.md 가시성 룰 의무 템플릿) → TaskUpdate(completed)
```

| Step | agent | mode | allowed-enums | advance |
|------|-------|------|---------------|---------|
| 2 | product-planner | — | `PRODUCT_PLAN_READY,CLARITY_INSUFFICIENT,PRODUCT_PLAN_CHANGE_DIFF,PRODUCT_PLAN_UPDATED,ISSUES_SYNCED` | `PRODUCT_PLAN_READY` |
| 3 | plan-reviewer | — | `PLAN_REVIEW_PASS,PLAN_REVIEW_CHANGES_REQUESTED` | `PLAN_REVIEW_PASS` |
| 4 | ux-architect | UX_FLOW | `UX_FLOW_READY,UX_FLOW_PATCHED,UX_REFINE_READY,UX_FLOW_ESCALATE` | `UX_FLOW_READY` / `UX_FLOW_PATCHED` |
| 5 | validator | UX_VALIDATION | `PASS,FAIL` | `PASS` |
| 6 | architect | SYSTEM_DESIGN | `SYSTEM_DESIGN_READY` | `SYSTEM_DESIGN_READY` |
| 6.5 | validator | DESIGN_VALIDATION | `DESIGN_REVIEW_PASS,DESIGN_REVIEW_FAIL,DESIGN_REVIEW_ESCALATE` | `DESIGN_REVIEW_PASS` |
| 7 | architect | TASK_DECOMPOSE | `READY_FOR_IMPL` | `READY_FOR_IMPL` |

### 분기 표

| ENUM | 처리 |
|------|------|
| `PRODUCT_PLAN_UPDATED` | ux-architect 직행 (plan-reviewer skip — 기존 PASS 활용) |
| `PRODUCT_PLAN_CHANGE_DIFF` | plan-reviewer 변경분만 재심사 |
| `CLARITY_INSUFFICIENT` | 사용자 역질문 후 재호출 |
| `ISSUES_SYNCED` | 동기화 완료 — 종료 |
| `PLAN_REVIEW_CHANGES_REQUESTED` | product-planner 재진입 (cycle ≤ 2) |
| `UX_REFINE_READY` | designer SCREEN 흐름 (별도 — `/ux` 권장) |
| `UX_FLOW_ESCALATE` | 사용자 위임 |
| validator UX `FAIL` | ux-architect 재진입 (cycle ≤ 2) |
| `DESIGN_REVIEW_FAIL` | architect SYSTEM_DESIGN 재진입 (cycle ≤ 2) |
| `DESIGN_REVIEW_ESCALATE` | 사용자 위임 |
| `AMBIGUOUS` | 재호출 1회 → 사용자 위임 (commands/quick.md cascade 정합) |

cycle 한도 초과 → 사용자 위임 (escalate).

### Step 8 — run 종료

```bash
"$HELPER" end-run
```

산출물 보고 (PRD / UX Flow / 시스템 설계 / 태스크 분해 prose 종이 경로) + 다음 단계 추천 (`/quick` light path · architect MODULE_PLAN 직접 · `/impl` per-batch · `/impl-loop` multi-batch). 구현은 본 skill 범위 밖 — 사용자 결정.

worktree 진입 시 `ExitWorktree(action="<keep|remove>")` (구현 이어가면 keep).

## Catastrophic 룰 정합

본 시퀀스는 `docs/conveyor-design.md` §2.3.4 (architect SD/TD 직전 PRD 검토) + §2.3.5 (TD 직전 DESIGN_REVIEW_PASS) 자연 충족. PreToolUse 훅 자동 통과.

## 참조

- `agents/{product-planner,plan-reviewer,ux-architect,architect,validator}.md` + `agents/architect/{system-design,task-decompose}.md` + `agents/validator/{ux-validation,design-validation}.md`
- `docs/orchestration.md` §3.1 / §4 (enum 결정표)
- `commands/quick.md` — 가시성 룰 SSOT + AMBIGUOUS cascade + yolo + worktree 룰
