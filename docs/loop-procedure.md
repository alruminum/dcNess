# Loop Execution Procedure (메인 Claude 컨베이어 mechanics)

> **Status**: ACTIVE
> **Origin**: `DCN-CHG-20260430-27`
> **Scope**: dcness 8 loop 의 *공통 실행 절차* SSOT. 메인 Claude 가 skill 트리거 또는 직접 발화로 루프 시작 시 본 문서를 컨베이어 매뉴얼처럼 따른다.
> **Cross-ref**: [`orchestration.md`](orchestration.md) §2~§7 (시퀀스 카탈로그 / 결정표 / 권한 매트릭스), [`process/dcness-guidelines.md`](process/dcness-guidelines.md) (echo / yolo / worktree / AMBIGUOUS 등 cross-cutting 룰).

---

## 0. 진입 모델

skill 트리거 또는 직접 발화 → 메인 Claude 가 **§7 매트릭스** 보고 task 리스트 동적 구성 → §1~§6 mechanics 따름.

- **skill 경유**: `commands/<skill>.md` 의 `Loop` 필드가 §7 행 가리킴. skill 은 input 정형화 + 라우팅 추천만 — 절차는 본 SSOT.
- **직접 발화** ("이거 quick 으로 가자"): orchestration.md §3 mini-graph + 본 SSOT §7 보고 메인이 자율 구성. 강제 X.
- **dcness-guidelines.md (SessionStart inject)**: 본 문서 read 의무 명시. 매 세션 진입 시 메인 자동 인지.

---

## 1. Step 0 — worktree (선택) + begin-run

### 1.1 worktree 분기

발화에 `worktree` / `wt` / `격리` / `isolate` 키워드 시 진입. 상세 = guidelines §7.

### 1.2 begin-run

```bash
HELPER="$(ls -d ${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/plugins/cache/dcness/dcness/*} 2>/dev/null | head -1)/scripts/dcness-helper"
RUN_ID=$("$HELPER" begin-run <entry_point> [--issue-num N])
echo "[<entry>] run started: $RUN_ID"
```

`<entry_point>` = §7 매트릭스 행의 `entry_point` 컬럼 (예: `quick`, `impl`, `impl-loop`, `qa`, `product-plan`). begin-run 동작: sid auto-detect + run_id 발급 + `live.json.active_runs` 슬롯 + `.by-pid-current-run/{cc_pid}` 박음.

---

## 2. Step 1 — TaskCreate

§7 매트릭스 행의 `task_list` 컬럼대로 일괄 등록. `/impl-loop` inner 의 경우 prefix `b<i>.` 의무 (DCN-CHG-30-12).

```
TaskCreate("<agent>: <mode 또는 짧은 설명>")
... (loop 정의 수만큼)
```

---

## 3. Step 2~N — agent 호출 골격

### 3.1 표준 1 step 시퀀스 (per-agent 의무)

```
TaskUpdate("<task>", in_progress)
"$HELPER" begin-step <agent> [<MODE>]
Agent(subagent_type="<agent>", mode="<MODE>", description="...")
RUN_DIR=$("$HELPER" run-dir)
mkdir -p "$RUN_DIR/.prose-staging"
PROSE_PATH="$RUN_DIR/.prose-staging/<step>.md"
# 메인이 sub-agent prose 본문을 위 경로에 Write
ENUM=$("$HELPER" end-step <agent> [<MODE>] --allowed-enums "<csv>" --prose-file "$PROSE_PATH")
# guidelines §1 의무 echo (5~12 줄)
TaskUpdate("<task>", completed)
```

### 3.2 prose-staging 컨벤션 (DCN-30-21)

`/tmp/dcness-*.md` 절대 사용 금지 (멀티세션 race). `<RUN_DIR>/.prose-staging/<step>.md` 만 유효.

`<step>` 명명:
- 단순: `<agent>` (예: `qa.md`)
- mode 보유: `<agent>-<MODE>` (예: `architect-MODULE_PLAN.md`)
- POLISH 사이클 (cycle ≤ 2): `engineer-POLISH-1`, `engineer-POLISH-2`
- 재호출 (TESTS_FAIL → engineer attempt 1+): `engineer-IMPL-RETRY-1`, `engineer-IMPL-RETRY-2`

각각 별도 begin/end-step 1쌍 (DCN-30-25 안전망).

### 3.3 ENUM 분기

| ENUM | 처리 |
|------|------|
| advance enum (§7 행의 `advance` 컬럼) | 다음 step |
| `SPEC_GAP_FOUND` | architect SPEC_GAP cycle (≤2) 또는 사용자 위임 |
| `TESTS_FAIL` / validator `FAIL` | engineer 재시도 (attempt < 3) |
| `SPEC_MISSING` | architect SPEC_GAP |
| `*_ESCALATE` (hard) | 사용자 위임 (escalate) |
| `*_ESCALATE` (soft) / `CLARITY_INSUFFICIENT` | 비-yolo: 사용자 위임 / yolo: `auto-resolve` |
| `CHANGES_REQUESTED` | engineer POLISH cycle (≤2) |
| `AMBIGUOUS` | guidelines §6 cascade (재호출 1회 → 사용자 위임) |
| `DESIGN_REVIEW_FAIL` / `UX_FAIL` | 직전 architect/ux-architect 재진입 (cycle ≤2) |
| `PRODUCT_PLAN_UPDATED` | plan-reviewer skip → ux-architect 직행 |

cycle 한도 = orchestration.md §5. yolo 매핑 = guidelines §5 + helper `auto-resolve` JSON.

---

## 4. Step 4.5 — stories.md / backlog.md sync (impl 계열 한정)

`impl-batch-loop` / `impl-ui-design-loop` / `direct-impl-loop` / `impl-loop` 의 inner batch 에 한정. engineer `IMPL_DONE` 직후, validator 진입 *전*. 메인 직접 mechanical edit (agent 위임 X — 도메인 외).

### 4.5.1 epic 경로 추출

```bash
EPIC_DIR=$(dirname $(dirname "<batch path>"))
STORIES_FILE="$EPIC_DIR/stories.md"
BACKLOG_FILE="$(dirname $(dirname $EPIC_DIR))/../backlog.md"
```

(실제 경로는 milestone 구조에 따라 메인이 `find` / `Glob` 으로 확인.)

### 4.5.2 갱신 룰

- batch 가 다룬 Story 의 task `[ ]` → `[x]`. batch ## 관련 Story / ## 적용 범위 메타로 식별.
- Story 하위 모두 `[x]` 면 Story 자체 `[x]`.
- stories.md 의 모든 Story `[x]` 면 backlog.md 의 epic 라인 `[x]`. 부분 진행 시 backlog 손대지 않음.

### 4.5.3 가시성

```
[<entry>] step 4.5 — stories.md / backlog.md sync
- stories.md: Story 1 [ ] → [x] (8 task 모두 완료)
- backlog.md: epic-01 라인 [ ] → [x]
```

---

## 5. Step 7 — finalize-run + clean 매트릭스 + commit/PR

### 5.1 finalize-run --auto-review 호출 (DCN-30-27 자동 트리거)

```bash
STATUS=$("$HELPER" finalize-run --expected-steps <N> --auto-review)
"$HELPER" end-run
echo "$STATUS"
```

`<N>` = §7 매트릭스 `expected_steps` 컬럼. `--auto-review` 가 in-process 로 `harness.run_review` 호출 → review 리포트가 STATUS JSON 뒤에 chained 됨. 메인 Claude 가 guidelines §4 따라 stdout character-for-character echo (Bash collapsed 회피).

`--auto-review` 생략 시 (사용자 명시 opt-out) — `dcness-review --run-id $RUN_ID --repo $(pwd)` 수동 호출 의무 (guidelines §3).

### 5.2 STATUS JSON 구조

```
{
  run_id, session_id,
  steps[{agent, mode, enum, must_fix, prose_excerpt}],
  has_ambiguous, has_must_fix, step_count
}
```

### 5.3 clean 판정 매트릭스

다음 모두 충족 → **clean** (자동 7a):
1. `has_ambiguous == false` && `has_must_fix == false`
2. step enum 매트릭스: §7 매트릭스 `clean_enum` 컬럼 모두 정합
3. git 안전 가드:
   - `git status --porcelain` 에 `.env` / `secrets.*` / `credentials.*` 없음
   - unstaged + untracked ≤ 10
   - submodule 변경 없음

clean 아니면 **7b (caveat)**.

### 5.4 7a — Clean 자동 commit/PR

자동 진행 (사용자 확인 X):

```bash
CHANGED=$(git diff --name-only HEAD)
HAS_REMOTE=$(git remote get-url origin >/dev/null 2>&1 && echo yes || echo no)

BRANCH="<prefix>/<short-slug>"   # prefix = §7 매트릭스
git checkout -b "$BRANCH" main
git add $CHANGED
git commit -m "$(cat <<'EOF'
<한 줄 제목>

<2~3 줄 본문 — engineer prose_excerpt + run_id 참조>

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"

if [ "$HAS_REMOTE" = "yes" ]; then
  git push -u origin "$BRANCH"
  gh pr create --title "<제목>" --body "<요약 + Test plan + run_id>"
  gh pr merge --squash --auto 2>/dev/null || gh pr merge --squash || \
    echo "[<entry>] PR merge 차단 — branch protection / CI 대기"
  git checkout main && git pull --ff-only 2>/dev/null || true
fi
```

worktree 진입 시 squash 흡수 검사 후 `ExitWorktree(action="<keep|remove>")` (guidelines §7).

### 5.5 7b — Caveat 확인

```
[<entry>] 완료 (caveat)
- run_id: $RUN_ID · 변경: <src/ 변경 파일>
- prose 종이: .claude/harness-state/.sessions/{sid}/runs/$RUN_ID/

⚠️ Caveat: <has_ambiguous / has_must_fix / unexpected enum / sensitive untracked>

커밋/PR 진행할까요? (수동 — branch → PR → squash merge)
```

worktree 처리도 사용자 결정.

**yolo 시**: `has_must_fix == false` + enum unexpected 만 (CHANGES_REQUESTED 1건 등) → 자동 7a 시도. `has_must_fix` 또는 `has_ambiguous` true → yolo 도 7b.

---

## 6. Step 8 — review 결과 인지

`--auto-review` stdout 자동 출력. 메인이 guidelines §4 룰대로 character-for-character echo. review 리포트의 must-fix / waste finding / per-Agent metric 즉시 인지 + 다음 run 회귀 방지에 활용.

review_main 실패 (예외) 시 helper stderr WARN — STATUS JSON 자체는 정상 출력. 메인이 사후 인지 후 수동 `dcness-review` 1회 재시도 권장.

---

## 7. Loop × Step 매트릭스 (인덱스 + 행별 풀스펙)

§7.0 = 한눈 인덱스 (6 컬럼). 각 loop 의 **풀스펙** (allowed_enums / sub_cycles / 분기 / 4.5 sync 적용 / branch decision rule) 은 §7.1~§7.8 행별 sub-section 참조. **메인 Claude 가 진입 시 인덱스 → 해당 sub-section 까지 read 의무**.

### 7.0 한눈 인덱스

| loop | entry_point | task_list (Step 1) | advance | clean_enum | expected_steps |
|------|-------------|--------------------|---------|------------|----------------|
| `feature-build-loop` (§3.1, §7.1) | `product-plan` | product-planner / plan-reviewer / ux-architect:UX_FLOW / validator:UX_VALIDATION / architect:SYSTEM_DESIGN / validator:DESIGN_VALIDATION / architect:TASK_DECOMPOSE | `PRODUCT_PLAN_READY` → `PLAN_REVIEW_PASS` → `UX_FLOW_READY` → `PASS` → `SYSTEM_DESIGN_READY` → `DESIGN_REVIEW_PASS` → `READY_FOR_IMPL` | advance 동일 | 7 |
| `impl-batch-loop` (§2.1, §7.2) | `impl` | architect:MODULE_PLAN / test-engineer / engineer:IMPL / validator:CODE_VALIDATION / pr-reviewer | `READY_FOR_IMPL` → `TESTS_WRITTEN` → `IMPL_DONE` → `PASS` → `LGTM` | advance 동일 | 5 |
| `impl-ui-design-loop` (§2.2, §7.3) | `impl` (UI 감지) | architect:MODULE_PLAN / designer / design-critic / test-engineer / engineer:IMPL / validator:CODE_VALIDATION / pr-reviewer | `READY_FOR_IMPL` → `DESIGN_READY_FOR_REVIEW` → `VARIANTS_APPROVED` → `TESTS_WRITTEN` → `IMPL_DONE` → `PASS` → `LGTM` | advance 동일 | 7 |
| `quick-bugfix-loop` (§3.5, §7.4) | `quick` | qa / architect:LIGHT_PLAN / engineer:IMPL / validator:BUGFIX_VALIDATION / pr-reviewer | `FUNCTIONAL_BUG`/`CLEANUP` → `LIGHT_PLAN_READY` → `IMPL_DONE` → `PASS` → `LGTM` | advance 동일 | 5 |
| `qa-triage` (§3.6, §7.5) | `qa` | qa | (5 enum 모두 — 라우팅 추천) | advance 개념 X | 1 |
| `ux-design-stage` (§3.2, §7.6) | `ux` | ux-architect:UX_FLOW / designer:SCREEN(THREE_WAY) / design-critic | `UX_FLOW_READY` → `DESIGN_READY_FOR_REVIEW` → `VARIANTS_APPROVED` | advance 동일 | 3 |
| `ux-refine-stage` (§3.3, §7.7) | `ux` (REFINE) | ux-architect:UX_REFINE / designer:SCREEN(THREE_WAY) / design-critic | `UX_REFINE_READY` → `DESIGN_READY_FOR_REVIEW` → `VARIANTS_APPROVED` | advance 동일 | 3 |
| `direct-impl-loop` (§3.4, §7.8) | `impl_driver` (future) | `impl-batch-loop` 동일 | `impl-batch-loop` 동일 | `impl-batch-loop` 동일 | 5 |

### 7.1 `feature-build-loop` 풀스펙

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

### 7.2 `impl-batch-loop` 풀스펙

**branch_prefix decision rule**:
- batch 내 신규 기능 (src 신규 파일 또는 인터페이스 추가) → `feat/<batch-slug>`
- 리팩토링 / 정리 / 테스트 보강 only → `chore/<batch-slug>`
- 버그픽스 (의도 vs 실제 격차 수정) → `fix/<batch-slug>`
- 메인 Claude 가 batch 의 ## 변경 요약 / engineer prose 보고 결정.

**Step 4.5 적용**: ✓ (engineer `IMPL_DONE` 직후, validator 진입 *전* — §4 참조).

**Step 별 allowed_enums**:
| step | agent[:mode] | allowed_enums |
|---|---|---|
| 2 | architect:MODULE_PLAN | `READY_FOR_IMPL,SPEC_GAP_FOUND,TECH_CONSTRAINT_CONFLICT` |
| 3 | test-engineer | `TESTS_WRITTEN,SPEC_GAP_FOUND` |
| 4 | engineer:IMPL | `IMPL_DONE,SPEC_GAP_FOUND,TESTS_FAIL,IMPLEMENTATION_ESCALATE` |
| 5 | validator:CODE_VALIDATION | `PASS,FAIL,SPEC_MISSING` |
| 6 | pr-reviewer | `LGTM,CHANGES_REQUESTED` |

**분기**:
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

**state-aware skip** (DCN-CHG-30-13): batch 파일 끝에 `MODULE_PLAN_READY` 마커 박혀있으면 Step 2 (architect:MODULE_PLAN) skip — TaskUpdate completed("skipped") + prose 종이는 batch 파일 자체를 `<RUN_DIR>/architect-MODULE_PLAN.md` 로 복사. catastrophic 룰 §2.3.3 통과용.

### 7.3 `impl-ui-design-loop` 풀스펙

**branch_prefix decision rule**: `impl-batch-loop` 와 동일 (`feat` / `chore` / `fix`).
**Step 4.5 적용**: ✓ (engineer `IMPL_DONE` 직후).

**Step 별 allowed_enums**:
| step | agent[:mode] | allowed_enums |
|---|---|---|
| 2 | architect:MODULE_PLAN | `impl-batch-loop` 동일 |
| 3 | designer:SCREEN(THREE_WAY) | `DESIGN_READY_FOR_REVIEW,DESIGN_LOOP_ESCALATE` |
| 4 | design-critic | `VARIANTS_APPROVED,VARIANTS_ALL_REJECTED,UX_REDESIGN_SHORTLIST` |
| 5 | test-engineer | `impl-batch-loop` 동일 |
| 6 | engineer:IMPL | `impl-batch-loop` 동일 |
| 7 | validator:CODE_VALIDATION | `impl-batch-loop` 동일 |
| 8 | pr-reviewer | `impl-batch-loop` 동일 |

**분기**:
- `VARIANTS_ALL_REJECTED` → designer:SCREEN 재호출 (round < 3)
- `UX_REDESIGN_SHORTLIST` → ux-architect:UX_REFINE (round ≥ 3, ux-refine-stage 진입)
- `DESIGN_LOOP_ESCALATE` → 사용자 위임
- 나머지 = `impl-batch-loop` 분기 동일

**sub_cycles**: `impl-batch-loop` 동일 + `designer:SCREEN-ROUND-<n>` (variants 재생성, round < 3).

### 7.4 `quick-bugfix-loop` 풀스펙

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
| 4 | engineer:IMPL | `IMPL_DONE,SPEC_GAP_FOUND,TESTS_FAIL,IMPLEMENTATION_ESCALATE` |
| 5 | validator:BUGFIX_VALIDATION | `PASS,FAIL` |
| 6 | pr-reviewer | `LGTM,CHANGES_REQUESTED` |

**qa 분기**:
- `DESIGN_ISSUE` → 종료 + ux-design-stage 추천 (구현 후)
- `KNOWN_ISSUE` → 종료
- `SCOPE_ESCALATE` → 사용자 위임 (분류 모호)

**sub_cycles**: `impl-batch-loop` 와 동일 (`SPEC_GAP` / `POLISH` / `IMPL-RETRY`). test-engineer 단계가 없으므로 TESTS_FAIL 은 engineer 자체 검증 실패 의미.

### 7.5 `qa-triage` 풀스펙

**branch_prefix**: commit X (분류만, 코드 변경 X).
**Step 4.5 적용**: X.

**Step 별 allowed_enums**:
| step | agent[:mode] | allowed_enums |
|---|---|---|
| 2 | qa | `FUNCTIONAL_BUG,CLEANUP,DESIGN_ISSUE,KNOWN_ISSUE,SCOPE_ESCALATE` |

**enum 별 라우팅 추천** (advance 개념 없음 — 메인이 사용자 결정 받음):
- `FUNCTIONAL_BUG` → `quick-bugfix-loop` (`/quick`) 또는 `impl-batch-loop`
- `CLEANUP` → `quick-bugfix-loop` (`/quick`) 또는 engineer 직접
- `DESIGN_ISSUE` → `ux-design-stage` (`/ux`) 또는 designer 직접
- `KNOWN_ISSUE` → 종료
- `SCOPE_ESCALATE` → 사용자 위임 (큰 변경 / 다중 모듈)

**sub_cycles**: 없음. AMBIGUOUS 시 guidelines §6 cascade.

### 7.6 `ux-design-stage` 풀스펙

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

### 7.7 `ux-refine-stage` 풀스펙

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

### 7.8 `direct-impl-loop` 풀스펙

`impl-batch-loop` 와 100% 동일. 차이점:
- entry_point = `impl_driver` CLI (현재 미구현, 후속 Task 예정)
- 사용자 batch 경로 직접 명시 (skill UI 없음)

allowed_enums / 분기 / sub_cycles / branch_prefix decision rule / Step 4.5 = `impl-batch-loop` (§7.2) 인용.

### 7.9 다중 batch chain (`impl-loop`)

`/impl-loop` = `impl-batch-loop` × N. outer task `impl-<i>: <batch>` + inner 5 sub-task `b<i>.<agent>` (DCN-CHG-30-12). 각 batch clean → 자동 7a + 다음 batch. caveat → 멈춤 + 사용자 위임 (Step 2.5 — `commands/impl-loop.md` 참조).

### 7.10 catastrophic 룰 정합

[`orchestration.md`](orchestration.md) §2.3 4룰 + §7.1 HARNESS_ONLY_AGENTS = `hooks/catastrophic-gate.sh` 강제. 본 SSOT 의 각 loop sequence 가 이 룰 자연 충족 (validator → pr-reviewer 직전 PASS / engineer 직전 plan READY / TASK_DECOMPOSE 직전 DESIGN_REVIEW_PASS / PRD 변경 후 plan-reviewer + ux-architect 검토).

---

## 8. 참조

- [`orchestration.md`](orchestration.md) §2~§7 — loop 카탈로그 / 결정표 / retry / escalate / handoff
- [`process/dcness-guidelines.md`](process/dcness-guidelines.md) — echo / Step 기록 / yolo / AMBIGUOUS / worktree / 결과 출력 / 권한 요청 / Karpathy
- [`conveyor-design.md`](conveyor-design.md) §2 / §3 / §7 — 컨베이어 디자인 + catastrophic gate
- `harness/session_state.py` — helper CLI (`begin-run` / `end-run` / `begin-step` / `end-step` / `finalize-run` / `run-dir` / `auto-resolve`)
- `harness/run_review.py` — review 엔진 (`--auto-review` 호출 대상)
- `commands/<skill>.md` — skill 진입점 (input 정형화 + Loop 추천)
