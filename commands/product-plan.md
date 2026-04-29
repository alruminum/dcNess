---
name: product-plan
description: 새 기능 / PRD 변경 / 큰 기획을 받아 product-planner → plan-reviewer → ux-architect → validator UX_VALIDATION → architect SYSTEM_DESIGN → architect TASK_DECOMPOSE 시퀀스로 spec/design 단계까지 진행하는 스킬. 사용자가 "기획자야", "새 기능", "피쳐 추가", "이런 기능이 필요할 것 같아", "기획해줘", "프로덕트 플랜", "/product-plan" 등을 말할 때 반드시 이 스킬을 사용한다. dcNess 컨베이어 패턴 (Task tool + Agent + helper + 훅) 으로 동작. 구현 진입은 별도 (`/quick` 또는 정식 impl 루프).
---

# Product Plan Skill — 새 기능 spec/design 흐름

> dcNess 컨베이어 패턴. PRD → 검토 → UX → 검증 → 시스템 설계 → 태스크 분해까지 *spec 단계만* 자동 진행. 구현은 사용자 결정 (다음 진입점).

## 언제 사용하는가

- 사용자 발화에 다음 keyword — "새 기능", "피쳐", "기획", "기획자", "기능 추가", "프로덕트 플랜", "이런 기능이 필요"
- 또는 PRD 변경이 동반된 작업
- 단순 버그픽스 / 코드 정리 → `/quick` 으로 라우팅

## 언제 사용하지 않음

- "버그", "오류", "이상해" → `/qa`
- "간단한 수정", "오타" → `/quick`
- "디자인", "레이아웃" 만의 변경 → `/ux` (구현 후) 또는 designer 직접 호출
- 기능 정의 명확 + 구현만 필요 → `/quick` 또는 architect MODULE_PLAN 직접

## 시퀀스 (orchestration.md §3.1)

```
product-planner → plan-reviewer → ux-architect → validator (UX_VALIDATION) →
architect (SYSTEM_DESIGN) → architect (TASK_DECOMPOSE) → 구현 진입 (별도)
```

각 단계마다 결론 enum:
- product-planner → `PRODUCT_PLAN_READY` (또는 `CLARITY_INSUFFICIENT` / `PRODUCT_PLAN_CHANGE_DIFF` / `PRODUCT_PLAN_UPDATED` / `ISSUES_SYNCED`)
- plan-reviewer → `PLAN_REVIEW_PASS` (또는 `PLAN_REVIEW_CHANGES_REQUESTED`)
- ux-architect → `UX_FLOW_READY` (또는 `UX_FLOW_PATCHED` / `UX_REFINE_READY` / `UX_FLOW_ESCALATE`)
- validator UX_VALIDATION → `PASS` (또는 `FAIL`)
- architect SYSTEM_DESIGN → `SYSTEM_DESIGN_READY`
- architect TASK_DECOMPOSE → `READY_FOR_IMPL`

## yolo 모드 — keyword 트리거

사용자 발화에 `yolo` / `auto` / `끝까지` / `막힘 없이` / `다 알아서` keyword 시 yolo ON.

yolo 시:
- `CLARITY_INSUFFICIENT` → product-planner 권고안 자동 채택 + 재호출
- `UX_FLOW_ESCALATE` → minimal UX_FLOW_PATCHED 자동 작성 후 advance
- `PLAN_REVIEW_CHANGES_REQUESTED` cycle 한도 (2) 초과 → 사용자 위임 (hard safety)
- `validator UX_VALIDATION FAIL` cycle 한도 (2) 초과 → 사용자 위임
- `AMBIGUOUS` → 1회 재호출, 그래도 모호 → 사용자 위임

helper auto-resolve 호출 (yolo 진행 시):
```bash
"$(ls -d ${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/plugins/cache/dcness/dcness/*} 2>/dev/null | head -1)/scripts/dcness-helper" auto-resolve "<agent>:<enum_or_mode>"
# 권장 액션 JSON. 메인이 그대로 적용.
```

catastrophic 룰 (PreToolUse 훅 §2.3.4) 은 그대로 — yolo 무관 hard safety.

## 가시성 룰 — 매 Agent 호출 후 메인 text echo (필수)

CC collapsed 회피 — Agent 호출 후 메인이 text reply 로 prose 핵심 5~12줄 echo
(DCN-CHG-30-11). prose 의 `## 결론` / `## Summary` / `## 변경 요약` 섹션 우선 인용.
`/product-plan` 의 7 step 모두 적용 — PRD diff / 심사 결론 / UX flow / 시스템 설계 /
DESIGN_VALIDATION 결과 / TASK_DECOMPOSE batch 목록 모두 사용자가 ctrl+o 안 눌러도
보이도록 echo. 자세한 룰은 `commands/quick.md` "가시성 룰" 참조.

## 절차 (Task tool + helper protocol)

### Step 0a — worktree 격리 진입 (선택, keyword 트리거)

사용자 발화에 `worktree` / `wt` / `격리` / `isolate` 포함 시만 worktree 진입 (옵션 C 트리거).
keyword 없으면 본 step skip → main repo cwd 그대로.

```
EnterWorktree(name="product-plan-{ts_short}")
```

진입 후 cwd = `.claude/worktrees/product-plan-.../`. `_default_base()` 가 main repo state
root 를 단일 source 로 보므로 SessionStart 훅 작성 by-pid / live.json 동작 정합 (`docs/conveyor-design.md` §13).

사용자 알림:
```
[product-plan] worktree 격리 진입 — cwd: .claude/worktrees/product-plan-...
```

### Step 0b — run 시작 + 사용자 확인

```bash
RUN_ID=$("$(ls -d ${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/plugins/cache/dcness/dcness/*} 2>/dev/null | head -1)/scripts/dcness-helper" begin-run product-plan)
echo "[product-plan] run started: $RUN_ID"
```

사용자에게 한 번 확인:
```
[product-plan] 실행 설정
- 요청: <유저 원문>
- 작업 유형: <신규 기능 / PRD 변경 / 기존 기능 확장 중 추정>
- 시퀀스: product-planner → plan-reviewer → ux-architect → validator UX → architect SYSTEM_DESIGN → architect TASK_DECOMPOSE
- 후속: 구현은 별도 진입 (사용자 결정)

진행할까요?
```

확인 못 받으면 대기.

### Step 1 — 7 task 생성

```
TaskCreate("product-planner: PRD 작성")
TaskCreate("plan-reviewer: PRD 심사")
TaskCreate("ux-architect: UX_FLOW")
TaskCreate("validator: UX_VALIDATION")
TaskCreate("architect: SYSTEM_DESIGN")
TaskCreate("validator: DESIGN_VALIDATION")
TaskCreate("architect: TASK_DECOMPOSE")
```

### Step 2 — product-planner

```
TaskUpdate("product-planner: PRD 작성", in_progress)
```

```bash
"$(ls -d ${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/plugins/cache/dcness/dcness/*} 2>/dev/null | head -1)/scripts/dcness-helper" begin-step product-planner
```

```
Agent(
  subagent_type="product-planner",
  description="<유저 원문>. PRD 작성해줘. 결론 enum: PRODUCT_PLAN_READY / CLARITY_INSUFFICIENT / PRODUCT_PLAN_CHANGE_DIFF / PRODUCT_PLAN_UPDATED / ISSUES_SYNCED."
)
```

```bash
ENUM=$("$(ls -d ${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/plugins/cache/dcness/dcness/*} 2>/dev/null | head -1)/scripts/dcness-helper" end-step product-planner \
    --allowed-enums "PRODUCT_PLAN_READY,CLARITY_INSUFFICIENT,PRODUCT_PLAN_CHANGE_DIFF,PRODUCT_PLAN_UPDATED,ISSUES_SYNCED" \
    --prose-file /tmp/dcness-pp-pp.md)
```

분기:
- `PRODUCT_PLAN_READY` → 다음 step (plan-reviewer)
- `PRODUCT_PLAN_UPDATED` → ux-architect 로 직행 (변경 반영, plan-reviewer skip 가능 — 기존 PASS 활용)
- `PRODUCT_PLAN_CHANGE_DIFF` → plan-reviewer 변경분만 재심사
- `CLARITY_INSUFFICIENT` → 사용자 역질문 후 재호출 (대기)
- `ISSUES_SYNCED` → 동기화 완료, 추가 진행 없음 (종료)
- `AMBIGUOUS` → cascade

advance:
```
TaskUpdate("product-planner: PRD 작성", completed)
```

### Step 3 — plan-reviewer

```
TaskUpdate("plan-reviewer: PRD 심사", in_progress)
```

```bash
"$(ls -d ${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/plugins/cache/dcness/dcness/*} 2>/dev/null | head -1)/scripts/dcness-helper" begin-step plan-reviewer
```

```
Agent(
  subagent_type="plan-reviewer",
  description="product-planner 의 PRD 심사해줘. 8 차원 (현실성·MVP·제약·UX 저니·숨은 가정·경쟁 맥락·과금 설계·기술 실현성). 결론 enum: PLAN_REVIEW_PASS / PLAN_REVIEW_CHANGES_REQUESTED."
)
```

```bash
ENUM=$("$(ls -d ${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/plugins/cache/dcness/dcness/*} 2>/dev/null | head -1)/scripts/dcness-helper" end-step plan-reviewer \
    --allowed-enums "PLAN_REVIEW_PASS,PLAN_REVIEW_CHANGES_REQUESTED" \
    --prose-file /tmp/dcness-pp-pr.md)
```

분기:
- `PLAN_REVIEW_PASS` → 다음 step (ux-architect)
- `PLAN_REVIEW_CHANGES_REQUESTED` → product-planner 재진입 (Step 2) — 1~2회 cycle, 무한 루프 방지
- `AMBIGUOUS` → cascade

### Step 4 — ux-architect (UX_FLOW)

```
TaskUpdate("ux-architect: UX_FLOW", in_progress)
```

```bash
"$(ls -d ${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/plugins/cache/dcness/dcness/*} 2>/dev/null | head -1)/scripts/dcness-helper" begin-step ux-architect UX_FLOW
```

```
Agent(
  subagent_type="ux-architect",
  mode="UX_FLOW",
  description="plan-reviewer PASS 받음. PRD 기반 UX Flow 작성. 결론 enum: UX_FLOW_READY / UX_FLOW_PATCHED / UX_REFINE_READY / UX_FLOW_ESCALATE."
)
```

```bash
ENUM=$("$(ls -d ${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/plugins/cache/dcness/dcness/*} 2>/dev/null | head -1)/scripts/dcness-helper" end-step ux-architect UX_FLOW \
    --allowed-enums "UX_FLOW_READY,UX_FLOW_PATCHED,UX_REFINE_READY,UX_FLOW_ESCALATE" \
    --prose-file /tmp/dcness-pp-ux.md)
```

분기:
- `UX_FLOW_READY` / `UX_FLOW_PATCHED` → 다음 step (validator UX_VALIDATION)
- `UX_REFINE_READY` → designer SCREEN 호출 흐름 (별도 — `/ux` 권장)
- `UX_FLOW_ESCALATE` → 사용자 위임
- `AMBIGUOUS` → cascade

### Step 5 — validator UX_VALIDATION

```
TaskUpdate("validator: UX_VALIDATION", in_progress)
```

```bash
"$(ls -d ${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/plugins/cache/dcness/dcness/*} 2>/dev/null | head -1)/scripts/dcness-helper" begin-step validator UX_VALIDATION
```

```
Agent(
  subagent_type="validator",
  mode="UX_VALIDATION",
  description="ux-architect 의 UX Flow 검증해줘. 결론 enum: PASS / FAIL."
)
```

```bash
ENUM=$("$(ls -d ${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/plugins/cache/dcness/dcness/*} 2>/dev/null | head -1)/scripts/dcness-helper" end-step validator UX_VALIDATION \
    --allowed-enums "PASS,FAIL" \
    --prose-file /tmp/dcness-pp-uxv.md)
```

분기:
- `PASS` → 다음 step (architect SYSTEM_DESIGN)
- `FAIL` → ux-architect 재진입 (Step 4)
- `AMBIGUOUS` → cascade

### Step 6 — architect SYSTEM_DESIGN

```
TaskUpdate("architect: SYSTEM_DESIGN", in_progress)
```

```bash
"$(ls -d ${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/plugins/cache/dcness/dcness/*} 2>/dev/null | head -1)/scripts/dcness-helper" begin-step architect SYSTEM_DESIGN
```

PreToolUse 훅 검사 (catastrophic-gate.sh):
- §2.3.4 — `product-planner.md` 존재 확인 → `plan-reviewer.md` 안 `PLAN_REVIEW_PASS` + `ux-architect.md` 안 `UX_FLOW_READY/PATCHED` 둘 다 필수. 시퀀스 정합 시 자동 통과.

```
Agent(
  subagent_type="architect",
  mode="SYSTEM_DESIGN",
  description="UX_VALIDATION PASS 받음. PRD + UX Flow 기반 시스템 설계. 결론 enum: SYSTEM_DESIGN_READY."
)
```

```bash
ENUM=$("$(ls -d ${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/plugins/cache/dcness/dcness/*} 2>/dev/null | head -1)/scripts/dcness-helper" end-step architect SYSTEM_DESIGN \
    --allowed-enums "SYSTEM_DESIGN_READY" \
    --prose-file /tmp/dcness-pp-sd.md)
```

advance: `SYSTEM_DESIGN_READY`.

### Step 6.5 — validator DESIGN_VALIDATION (DCN-CHG-20260430-05)

설계 루프의 검증 단계 — TASK_DECOMPOSE 진입 전 시스템 설계 구현 가능성 + 스펙 완결성 + 리스크 검증.

```
TaskUpdate("validator: DESIGN_VALIDATION", in_progress)
```

```bash
"$(ls -d ${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/plugins/cache/dcness/dcness/*} 2>/dev/null | head -1)/scripts/dcness-helper" begin-step validator DESIGN_VALIDATION
```

```
Agent(
  subagent_type="validator",
  mode="DESIGN_VALIDATION",
  description="architect SYSTEM_DESIGN 완료. 시스템 설계 검증해줘. 3 계층 체크리스트 (구현 가능성·스펙 완결성·리스크). 결론 enum: DESIGN_REVIEW_PASS / DESIGN_REVIEW_FAIL / DESIGN_REVIEW_ESCALATE."
)
```

```bash
ENUM=$("$(ls -d ${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/plugins/cache/dcness/dcness/*} 2>/dev/null | head -1)/scripts/dcness-helper" end-step validator DESIGN_VALIDATION \
    --allowed-enums "DESIGN_REVIEW_PASS,DESIGN_REVIEW_FAIL,DESIGN_REVIEW_ESCALATE" \
    --prose-file /tmp/dcness-pp-dv.md)
```

분기:
- `DESIGN_REVIEW_PASS` → 다음 step (architect TASK_DECOMPOSE)
- `DESIGN_REVIEW_FAIL` → architect SYSTEM_DESIGN 재진입 (Step 6) — **cycle 한도 2**, 초과 시 사용자 위임
- `DESIGN_REVIEW_ESCALATE` → 사용자 위임 (escalate)
- `AMBIGUOUS` → cascade

advance:
```
TaskUpdate("validator: DESIGN_VALIDATION", completed)
```

### Step 7 — architect TASK_DECOMPOSE

```
TaskUpdate("architect: TASK_DECOMPOSE", in_progress)
```

```bash
"$(ls -d ${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/plugins/cache/dcness/dcness/*} 2>/dev/null | head -1)/scripts/dcness-helper" begin-step architect TASK_DECOMPOSE
```

PreToolUse 훅:
- §2.3.4 — Step 6 와 동일 검사 (PRD + UX 검토 정합).
- §2.3.5 (DCN-CHG-20260430-05) — `validator-DESIGN_VALIDATION.md` 안 `DESIGN_REVIEW_PASS` 확인 → 통과 (Step 6.5 에서 박힘).

```
Agent(
  subagent_type="architect",
  mode="TASK_DECOMPOSE",
  description="SYSTEM_DESIGN 완료. epic stories → 기술 태스크 분해 + impl batch 작성. 결론 enum: READY_FOR_IMPL."
)
```

```bash
ENUM=$("$(ls -d ${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/plugins/cache/dcness/dcness/*} 2>/dev/null | head -1)/scripts/dcness-helper" end-step architect TASK_DECOMPOSE \
    --allowed-enums "READY_FOR_IMPL" \
    --prose-file /tmp/dcness-pp-td.md)
```

advance: `READY_FOR_IMPL`.

```
TaskUpdate("architect: TASK_DECOMPOSE", completed)
```

### Step 8 — run 종료 + 다음 단계 추천

```bash
"$(ls -d ${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/plugins/cache/dcness/dcness/*} 2>/dev/null | head -1)/scripts/dcness-helper" end-run
```

사용자에게:
```
[product-plan] spec/design 단계 완료
- run_id: $RUN_ID
- 산출물:
  - PRD: .claude/harness-state/.sessions/{sid}/runs/$RUN_ID/product-planner.md
  - UX Flow: .../ux-architect-UX_FLOW.md
  - 시스템 설계: .../architect-SYSTEM_DESIGN.md
  - 태스크 분해: .../architect-TASK_DECOMPOSE.md (impl batch 들 prose 안에)

다음 단계 (구현):
- 작은 단위 한 번에 → `/quick` (light path)
- impl batch 별 정식 루프 → architect MODULE_PLAN 직접 호출 또는 별도 진입점

진행할까요?
```

구현은 본 skill 범위 밖. 사용자 결정 받아 별도 skill / Agent 호출.

worktree 진입 (Step 0a) 했으면 종료 결정:

```
ExitWorktree(action="<keep|remove>")
```

기본 추천 — 후속 구현 진입 예정이면 `keep` (이어서 작업), spec/design 단독 종결이면 `remove`. 자동
결정 금지.

## AMBIGUOUS 처리 — 매 step 동일

`end-step` stdout `AMBIGUOUS` 면:
1. 재호출 (1회)
2. 그래도 AMBIGUOUS → 사용자 위임 (`/qa` cascade 정합)

## 재진입 / cycle 한도

- `PLAN_REVIEW_CHANGES_REQUESTED` → product-planner 재진입 — **2 cycle 한도**. 초과 시 사용자 위임.
- validator UX_VALIDATION FAIL → ux-architect 재진입 — **2 cycle 한도**.
- validator DESIGN_VALIDATION DESIGN_REVIEW_FAIL → architect SYSTEM_DESIGN 재진입 — **2 cycle 한도** (DCN-CHG-20260430-05).
- 한도 초과 = 사용자 결정 필요 (escalate).

## Catastrophic 룰 — 자동 정합

본 시퀀스는 §2.3 4룰 정합:
- §2.3.1 (pr-reviewer 직전 validator PASS) — pr-reviewer 본 skill 시퀀스 안 없음. 비대상.
- §2.3.3 (engineer 직전 plan READY) — engineer 본 skill 시퀀스 안 없음. 비대상.
- §2.3.4 (architect SD/TD 직전 PRD 검토) — Step 3 plan-reviewer + Step 4-5 ux-architect 가 자연 충족.

PreToolUse 훅이 매 Agent 직전 자동 검사. 시퀀스 정합 시 통과.

## 한계 / 후속

- **구현 자동 진입 X** — Step 8 에서 종료. 구현은 사용자 결정 (별도 진입).
- **architect TASK_DECOMPOSE 의 impl batch 들** — 각 batch 별 architect MODULE_PLAN 호출 자동화 X. v1 은 사용자가 batch 1개씩 처리.
- **UX_REFINE_READY 분기 미구현** — designer SCREEN 호출 자동화는 `/ux` 후속 도입.

## 참조

- `agents/product-planner.md` / `agents/plan-reviewer.md` / `agents/ux-architect.md`
- `agents/validator/ux-validation.md`
- `agents/architect.md` + `agents/architect/{system-design,task-decompose}.md`
- `docs/orchestration.md` §3.1 — 신규 기능 / PRD 변경 시퀀스
- `docs/orchestration.md` §4.1 / §4.2 / §4.3 / §4.4 — 결론 enum 결정표
- `docs/conveyor-design.md` §2 / §3 / §7 / §8 — Task tool + helper + 훅
- `commands/qa.md` / `commands/quick.md` — 다른 진입점
