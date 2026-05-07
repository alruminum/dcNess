# Loop Execution Procedure (메인 Claude 컨베이어 mechanics)

> **Status**: ACTIVE
> **Scope**: dcness 8 loop 의 *공통 실행 절차* SSOT — Step 0~8 mechanics. 메인 Claude 가 skill 트리거 또는 직접 발화로 루프 시작 시 본 문서를 컨베이어 매뉴얼처럼 따른다.
> **Cross-ref**: 8 loop 별 행별 풀스펙 (allowed_enums / 분기 / sub_cycles / branch_prefix) + 시퀀스 mini-graph + 결정표 = [`orchestration.md`](orchestration.md) §2~§4. cross-cutting 룰 (echo / yolo / worktree / AMBIGUOUS) = [`dcness-rules.md`](dcness-rules.md).

---

## 0. 진입 모델

skill 트리거 또는 직접 발화 → 메인 Claude 가 **[`orchestration.md`](orchestration.md) §4.1 인덱스 + 해당 loop 풀스펙 sub-section** 보고 task 리스트 동적 구성 → §1~§6 mechanics 따름.

- **skill 경유**: `commands/<skill>.md` 의 `Loop` 필드가 orchestration §4 행 가리킴. skill 은 input 정형화 + 라우팅 추천만 — 절차는 본 SSOT, loop spec 은 orchestration §4.
- **직접 발화** ("이거 quick 으로 가자"): orchestration.md §3 mini-graph + §4.1 인덱스 보고 메인이 자율 구성. 강제 X.
- **dcness-rules.md (SessionStart inject)**: 본 문서 + catalog 모두 read 의무 명시. 매 세션 진입 시 메인 자동 인지.

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

[`orchestration.md`](orchestration.md) §4 행의 `task_list` 컬럼대로 일괄 등록. `/impl-loop` inner 의 경우 prefix `b<i>.` 의무 (DCN-CHG-30-12).

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
ENUM=$("$HELPER" end-step <agent> [<MODE>] --allowed-enums "<csv>")
# guidelines §1 의무 echo (5~12 줄)
TaskUpdate("<task>", completed)
```

begin-step stdout 에 `[INSIGHTS: <agent>/<mode>]` 섹션이 있으면 Agent prompt 끝에 그대로 포함시킨다. 해당 agent 의 과거 루프 학습 내용 — "하지 말 것" / "잘 됐던 것" — 이 프로젝트 레벨로 누적된 것.

메인이 prose를 직접 Write 할 필요 없음 — PostToolUse Agent hook 이 sub 종료 시 `tool_response.text` 에서 prose 를 자동으로 `<run_dir>/<agent>[-<MODE>].md` 에 저장하고 `live.json.current_step.prose_file` 에 경로 기록. `end-step` 이 이 경로를 자동 읽는다.

### 3.2 prose 파일 자동 명명 규칙

PostToolUse hook 이 `signal_io.signal_path` 기준으로 파일명 결정:
- 단순: `<run_dir>/<agent>.md`
- mode 보유: `<run_dir>/<agent>-<MODE>.md`
- 같은 (agent, mode) N번째 반복: `<run_dir>/<agent>[-<MODE>]-N.md`

각각 별도 begin/end-step 1쌍 필수 (DCN-30-25 안전망). `--prose-file` 명시적 전달은 legacy/override 용도로 여전히 허용.

### 3.3 ENUM 분기

| ENUM | 처리 |
|------|------|
| advance enum (catalog 행의 `advance` 컬럼) | 다음 step |
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

## 3.4 impl-task-loop 3-commit 구조 (orchestration §4.3 한정)

`impl-task-loop` / `impl-ui-design-loop` / `direct-impl-loop` 에서 루프 종료 전 3 단계 commit + PR create 를 강제 (catastrophic gate §2.3.6~§2.3.8, `hooks.py`).

| 시점 | stage | 포함 파일 | 커밋 메시지 예 |
|---|---|---|---|
| MODULE_PLAN READY_FOR_IMPL 직후 | docs | `docs/impl/NN.md` 등 | `docs: impl plan <task-slug>` |
| TESTS_WRITTEN 직후 | tests | `src/tests/**`, `*.test.*` | `test: tests for <task-slug>` |
| CODE_VALIDATION PASS 직후 | src | `src/**`, stories.md 등 | `feat/fix/chore: <task-slug>` |
| LGTM 직후 | — (merge) | 새 커밋 없음 | — |

### commit 골격

```bash
# commit1 (MODULE_PLAN 직후) — 브랜치 최초 생성
BRANCH="<prefix>/<task-slug>"
git checkout -b "$BRANCH" main
git add docs/impl/NN-*.md          # 플랜 문서
git commit -m "docs: impl plan <task-slug>"
"$HELPER" record-stage-commit docs  # stage_commits.docs 기록

# commit2 (TESTS_WRITTEN 직후)
git add src/tests/**  # test 파일
git commit -m "test: tests for <task-slug>"
"$HELPER" record-stage-commit tests

# commit3 (CODE_VALIDATION PASS 직후) — push + PR create
git add src/**  # src 변경 + stories.md/backlog.md (Step 4.5 결과)
git commit -m "<type>: <task-slug>"
"$HELPER" record-stage-commit src
git push -u origin "$BRANCH"

# PR body: Part of vs Closes 자동 판단
REMAINING=$(grep -c '\[ \]' "$STORIES_FILE" 2>/dev/null || echo 0)
if [ "$REMAINING" = "0" ]; then
  PR_BODY="Closes #<story_issue>"
  # 에픽 마지막 story 이면 "Closes #<epic_issue>" 도 추가
else
  PR_BODY="Part of #<story_issue>"
fi
gh pr create --title "<type>: <task-slug> (#<story_issue>)" --body "$PR_BODY"
```

### Step 7a (impl-task-loop)

PR 이미 생성된 상태 — merge only, **NO --squash** (3 commit 히스토리 보존):

```bash
gh pr merge || echo "[impl] merge 대기 — CI / reviewers"
git checkout main && git pull --ff-only 2>/dev/null || true
```

---

## 4. Step 4.5 — stories.md / backlog.md sync (impl 계열 한정)

`impl-task-loop` / `impl-ui-design-loop` / `direct-impl-loop` / `impl-loop` 의 inner task 에 한정. engineer `IMPL_DONE` 직후, validator 진입 *전*. 메인 직접 mechanical edit (agent 위임 X — 도메인 외).

### 4.5.1 epic 경로 추출

```bash
EPIC_DIR=$(dirname $(dirname "<task path>"))
STORIES_FILE="$EPIC_DIR/stories.md"
BACKLOG_FILE="$(dirname $(dirname $EPIC_DIR))/../backlog.md"
```

(실제 경로는 milestone 구조에 따라 메인이 `find` / `Glob` 으로 확인.)

### 4.5.2 갱신 룰

- task 가 다룬 Story 의 task `[ ]` → `[x]`. task ## 관련 Story / ## 적용 범위 메타로 식별.
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

`<N>` = catalog 행 `expected_steps` 컬럼. `--auto-review` 가 in-process 로 `harness.run_review` 호출 → review 리포트가 STATUS JSON 뒤에 chained 됨. 메인 Claude 가 guidelines §4 따라 stdout character-for-character echo (Bash collapsed 회피).

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
2. step enum 매트릭스: catalog 행 `clean_enum` 컬럼 모두 정합
3. git 안전 가드:
   - `git status --porcelain` 에 `.env` / `secrets.*` / `credentials.*` 없음
   - unstaged + untracked ≤ 10
   - submodule 변경 없음

clean 아니면 **7b (caveat)**.

### 5.4 7a — Clean 자동 commit/PR

> **impl-task-loop 제외**: 3-commit 구조 (§3.4) 에서 branch/commit3/push/PR 이미 완료. Step 7a = merge only (`gh pr merge` — NO --squash).

자동 진행 (사용자 확인 X, **impl-task-loop 외** 루프 적용):

```bash
CHANGED=$(git diff --name-only HEAD)
HAS_REMOTE=$(git remote get-url origin >/dev/null 2>&1 && echo yes || echo no)

BRANCH="<prefix>/<short-slug>"   # prefix = catalog 행
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
  gh pr merge --merge --auto 2>/dev/null || gh pr merge --merge || \
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

커밋/PR 진행할까요? (branch → PR → regular merge 자동)
```

worktree 처리도 사용자 결정.

**yolo 시**: `has_must_fix == false` + enum unexpected 만 (CHANGES_REQUESTED 1건 등) → 자동 7a 시도. `has_must_fix` 또는 `has_ambiguous` true → yolo 도 7b.

---

## 6. Step 8 — review 결과 인지

`--auto-review` stdout 자동 출력. 메인이 guidelines §4 룰대로 character-for-character echo. review 리포트의 must-fix / waste finding / per-Agent metric 즉시 인지 + 다음 run 회귀 방지에 활용.

review_main 실패 (예외) 시 helper stderr WARN — STATUS JSON 자체는 정상 출력. 메인이 사후 인지 후 수동 `dcness-review` 1회 재시도 권장.

---

## 7. Loop 카탈로그 (cross-ref)

8 loop 별 풀스펙 (`entry_point` / `task_list` / `advance` / `clean_enum` / `expected_steps` / `branch_prefix` / Step 별 `allowed_enums` / 분기 / `sub_cycles`) = [`orchestration.md`](orchestration.md) §4.

**메인 Claude 진입 시 의무**: orchestration §4.1 인덱스 → 해당 loop sub-section read.

### 7.1 catastrophic 룰 정합

[`orchestration.md`](orchestration.md) §2.3 4룰 + handoff-matrix §4.1 HARNESS_ONLY_AGENTS = `hooks/catastrophic-gate.sh` 강제. orchestration §4 의 각 loop sequence 가 이 룰 자연 충족 (validator → pr-reviewer 직전 PASS / engineer 직전 plan READY / TASK_DECOMPOSE 직전 DESIGN_REVIEW_PASS / PRD 변경 후 plan-reviewer + ux-architect 검토).

> Note: 이전 §7.0 인덱스 + §7.2~§7.10 행별 풀스펙은 [`orchestration.md`](orchestration.md) §4 로 흡수 (loop-catalog.md 폐기, 8 → 7 SSOT).

---

## 8. 참조

- [`orchestration.md`](orchestration.md) §2~§4 — 시퀀스 mini-graph / 8 loop 행별 풀스펙 / handoff cross-ref
- [`dcness-rules.md`](dcness-rules.md) — echo / Step 기록 / yolo / AMBIGUOUS / worktree / 결과 출력 / 권한 요청 / Karpathy
- [`../archive/conveyor-design.md`](../archive/conveyor-design.md) §2 / §3 / §7 — 컨베이어 디자인 + catastrophic gate (역사 자료)
- `harness/session_state.py` — helper CLI (`begin-run` / `end-run` / `begin-step` / `end-step` / `finalize-run` / `run-dir` / `auto-resolve`)
- `harness/run_review.py` — review 엔진 (`--auto-review` 호출 대상)
- `commands/<skill>.md` — skill 진입점 (input 정형화 + Loop 추천)
