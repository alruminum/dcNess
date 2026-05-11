# Loop Execution Procedure (메인 Claude 컨베이어 mechanics)

> **Status**: ACTIVE
> **Scope**: dcness 8 loop 의 *공통 실행 절차* SSOT — Step 0~8 mechanics. 메인 Claude 가 skill 트리거 또는 직접 발화로 루프 시작 시 본 문서를 컨베이어 매뉴얼처럼 따른다.
> **Cross-ref**: 8 loop 별 행별 풀스펙 (allowed_enums / 분기 / sub_cycles / branch_prefix) + 시퀀스 mini-graph + 결정표 = [`orchestration.md`](orchestration.md) §2~§4. 에이전트 호출 결과 echo + 세션 주입 강조 룰 = [`dcness-rules.md`](dcness-rules.md).

---

## 0. 진입 모델

skill 트리거 또는 직접 발화 → 메인 Claude 가 **[`orchestration.md`](orchestration.md) §4.1 인덱스 + 해당 loop 풀스펙 sub-section** 보고 task 리스트 동적 구성 → §1~§6 mechanics 따름.

- **skill 경유**: `commands/<skill>.md` 의 `Loop` 필드가 orchestration §4 행 가리킴. skill 은 input 정형화 + 라우팅 추천만 — 절차는 본 SSOT, loop spec 은 orchestration §4.
- **직접 발화** ("이거 quick 으로 가자"): orchestration.md §3 mini-graph + §4.1 인덱스 보고 메인이 자율 구성. 강제 X.
- **dcness-rules.md (SessionStart inject)**: 본 문서 + catalog 모두 read 의무 명시. 매 세션 진입 시 메인 자동 인지.

---

## 1. Step 0 — worktree + begin-run

### 1.1 worktree 분기 (impl 류 루프 한정)

**행동형 skill 중 *코드 변경 batch* (`/quick` `/impl` `/impl-loop` `/auto-loop`) 진입 시만 EnterWorktree 자동 호출**. 동시 다중 세션 충돌 회피 + 메인 working tree 보호.

**`/product-plan` / 모듈 설계 / 문서·시드 작업은 워크트리 X** — 본 작업은 충돌 회피 목적 부재. 메인 working tree 에서 별 branch 따고 직접 진행.

```
EnterWorktree(name="<skill>-{ts_short}")   # impl 류만
```

**거부 표현 시에만 건너뜀** — 사용자 발화에 정규식 `워크트리\s*(빼|없|말)` 매치 (예: "워크트리 빼고", "워크트리 없이", "워크트리 말고") 시 EnterWorktree 호출 0, 일반 cwd 그대로 진행.

수동 `git worktree add` 우회 금지 — CC permission 시스템이 EnterWorktree 만 자동 권한 처리. 수동 워크트리는 sub-agent Write 거부 회귀 (#255 W1).

종료 시 squash 흡수 검사 후 자동:

```bash
UNMERGED_DIFF=$(git diff "main..$WORKTREE_BRANCH" -- ':^.claude' 2>/dev/null)
if [ -z "$UNMERGED_DIFF" ]; then
  ExitWorktree(action="remove", discard_changes=true)
else
  ExitWorktree(action="keep")
fi
```

자세히 = [`../archive/conveyor-design.md`](../archive/conveyor-design.md) §13.

### 1.2 begin-run

```bash
HELPER="$(ls -d ${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/plugins/cache/dcness/dcness/*} 2>/dev/null | sort -V | tail -1)/scripts/dcness-helper"
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
"$HELPER" end-step <agent> [<MODE>]   # prose-only mode (이슈 #284 정착 후 권장, stdout=PROSE_LOGGED)
# legacy compat: ENUM=$("$HELPER" end-step <agent> [<MODE>] --allowed-enums "<csv>")
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
| advance enum (catalog 행의 `advance` 컬럼) | 다음 step 있으면 진행 / **마지막 step이면 사용자 대기 없이 즉시 Step 7** |
| `SPEC_GAP_FOUND` | module-architect (보강 케이스) cycle (≤2) 또는 사용자 위임 |
| `TESTS_FAIL` / code-validator `FAIL` | engineer 재시도 (attempt < 3) |
| code-validator `ESCALATE` (사유: spec 부재) | module-architect (보강 케이스) |
| code-validator `ESCALATE` (사유: 재시도 한도 초과 등) | 사용자 위임 |
| `*_ESCALATE` (hard) | 사용자 위임 (escalate) |
| `*_ESCALATE` (soft) / `CLARITY_INSUFFICIENT` | 비-yolo: 사용자 위임 / yolo: `auto-resolve` |
| `CHANGES_REQUESTED` | engineer POLISH cycle (≤2) |
| `AMBIGUOUS` | 재호출 1회 (결론 enum 명시 요청) → 재호출도 AMBIGUOUS 시 사용자 위임 (enum 후보 + prose 발췌) |
| architecture-validator `FAIL` | system-architect 재진입 (cycle ≤2) |
| `PRODUCT_PLAN_UPDATED` | plan-reviewer 변경분 재심사 (skip 분기 폐기 — 변경의 성격 무관 항상 호출). PASS 시 ux-architect. |
| `PLAN_REVIEW_FAIL` | product-planner 재진입 (cycle ≤2) |
| `PLAN_REVIEW_ESCALATE` | 사용자 위임 (외부 검증 불가 / 권한 경계 밖 / 동일 finding 반복 / URL 부재 PASS 시도) |

cycle 한도 = orchestration.md §5.

### 3.3.1 retry / POLISH 분기 시 task 재활용 (MUST)

위 표의 **재시도 / 재호출 / cycle / POLISH** 분기로 진입할 때, 신규 `TaskCreate` 금지 — *기존 task 를 `in_progress` 로 되돌린다*.

| 분기 | 재활용 대상 task | 행동 |
|---|---|---|
| `TESTS_FAIL` → engineer 재시도 | 직전 engineer IMPL task | `TaskUpdate(<task>, in_progress)` |
| `CHANGES_REQUESTED` → engineer POLISH | 직전 engineer IMPL task | `TaskUpdate(<task>, in_progress)` |
| POLISH 후 pr-reviewer 재실행 | 직전 pr-reviewer task | `TaskUpdate(<task>, in_progress)` |
| `IMPL_PARTIAL` → engineer 재호출 | 직전 engineer IMPL task | `TaskUpdate(<task>, in_progress)` |
| architecture-validator `FAIL` → system-architect 재진입 | 직전 system-architect task | `TaskUpdate(<task>, in_progress)` |
| ux-architect self-check FAIL → ux-architect 재진입 | 직전 ux-architect task | `TaskUpdate(<task>, in_progress)` (prose 내부 cycle — 별도 task X) |
| `AMBIGUOUS` 재호출 1회 | 직전 동일 agent task | `TaskUpdate(<task>, in_progress)` |
| `SPEC_GAP_FOUND` → module-architect (보강) | 신규 task (다른 agent) | `TaskCreate` 가능 |

이유: retry / POLISH 는 *동일 step 의 재실행*. 신규 TaskCreate 시 같은 step 이 task list 에 중복 등장 → 진행 추적 오염. cycle 카운터는 step occurrence (`<agent>[-<MODE>]-N.md`) 로 보존되므로 task 는 1개로 유지.

**MUST 순서** (retry / POLISH 진입 시):

```
TaskUpdate(<기존 task>, in_progress)   # 신규 TaskCreate 금지
"$HELPER" begin-step <agent> [<MODE>]   # occurrence 자동 증가 → -N.md
Agent(...)
ENUM=$("$HELPER" end-step ...)
TaskUpdate(<기존 task>, completed)
```

### yolo 모드

발화에 `yolo` / `auto` / `끝까지` / `막힘 없이` / `다 알아서` 키워드 시 ON.

| 상황 | 비-yolo | yolo |
|---|---|---|
| `CLARITY_INSUFFICIENT` / `*_ESCALATE` (soft) / `AMBIGUOUS` | 사용자 위임 | `auto-resolve` 적용 |
| `SPEC_GAP_FOUND` | 사용자 위임 | module-architect (보강 케이스) cycle (≤2) |
| `TESTS_FAIL` / code-validator FAIL | 재시도 (≤3) | 동일 |
| `IMPL_PARTIAL` | engineer 재호출 (split ≤ 3) | 동일 — 새 context window |
| `CHANGES_REQUESTED` | 사용자 위임 | engineer POLISH (cycle ≤2) |
| Step 7 caveat (NICE TO HAVE only, MUST FIX 0) | 사용자 위임 | 7a 자동 |
| catastrophic 룰 | hard safety | hard safety (yolo 우회 X) |

```bash
RESOLVE_JSON=$("$HELPER" auto-resolve "<agent>:<enum_or_mode>")
# JSON: {"action":..., "hint":..., "next_enum":...}
# unmapped 시 yolo 도 사용자 위임 fallback
```

---

## 3.4 impl-task-loop 3-commit 구조 (orchestration §4.3 한정)

`impl-task-loop` / `impl-ui-design-loop` / `direct-impl-loop` 에서 루프 종료 전 3 단계 commit + PR create 를 강제 (catastrophic gate §2.3.6~§2.3.8, `hooks.py`).

| 시점 | stage | 포함 파일 | 커밋 메시지 예 |
|---|---|---|---|
| (default) test-engineer 시작 직전 / (fallback) module-architect READY 직후 | docs | `docs/impl/NN.md` (default 면 이미 정식 위치, fallback 이면 새로 작성됨) | `docs: impl plan <task-slug>` |
| TESTS_WRITTEN 직후 | tests | `src/tests/**`, `*.test.*` | `test: tests for <task-slug>` |
| code-validator PASS 직후 | src | `src/**`, stories.md 등 | `feat/fix/chore: <task-slug>` |
| LGTM 직후 | — (merge) | 새 커밋 없음 | — |

> default 모드 = task 파일이 이미 정식 위치에 있음 (feature-build-loop §4.2 Step 7 module-architect × N 산출물). branch 새로 만들고 *기존* `docs/impl/NN-*.md` 를 stage 만 하는 commit (변경 0 일 수도 있으니 `git add -A docs/impl/` 로 의도 표시 + commit). fallback 모드 = 위치 부재 → module-architect 1번 호출 → 새로 작성된 파일을 stage.

### commit 골격

```bash
# commit1 (default = test-engineer 시작 직전 / fallback = module-architect READY 직후) — 브랜치 최초 생성
BRANCH="<prefix>/<task-slug>"
git checkout -b "$BRANCH" main
git add docs/impl/NN-*.md          # 플랜 문서 (default 시 변경 없음 — 정식 위치 stage 만)
git commit --allow-empty -m "docs: impl plan <task-slug>"  # default 일 때 변경 없으면 --allow-empty
"$HELPER" record-stage-commit docs  # stage_commits.docs 기록

# commit2 (TESTS_WRITTEN 직후)
git add src/tests/**  # test 파일
git commit -m "test: tests for <task-slug>"
"$HELPER" record-stage-commit tests

# commit3 (code-validator PASS 직후) — push + PR create
git add src/**  # src 변경 + stories.md/backlog.md (Step 4.5 결과)
git commit -m "<type>: <task-slug>"
"$HELPER" record-stage-commit src
git push -u origin "$BRANCH"

# PR body: Part of vs Closes 자동 판단 (issue-lifecycle.md §1.4 적용 절차)
# 본 task 의 *부모 Story 섹션* 에서만 [ ] 카운트 — 다른 Story 의 미완 task 와 섞이지 X.
# 기존 stories.md 전체 grep 은 #320 #2 false positive 사단 (Story 1개 task 케이스 → false Part of).
# stories.md SSOT 형식: 각 Story 헤더 직하 `**GitHub Issue:** [#MMM](url)` 마커 (issue-lifecycle.md §1.3).
STORY_REMAINING=$(awk -v issue="#${STORY_ISSUE}" '
  /\*\*GitHub Issue:\*\*/ {
    if ($0 ~ "\\[" issue "\\]") {flag=1; next}
    else {flag=0}
  }
  flag && /\[ \]/ {count++}
  END {print count+0}
' "$STORIES_FILE")

if [ "$STORY_REMAINING" = "0" ]; then
  # 본 task 가 부모 Story 의 마지막 → Closes
  PR_BODY="Closes #${STORY_ISSUE}"
  # 에픽 마지막 story 사전 체크 (issue-lifecycle.md §2.2)
  EPIC_OPEN_STORIES=$(gh issue list --label "epic-${EPIC_NUM}-${EPIC_SLUG}" --state open --json number --jq 'length' 2>/dev/null || echo 0)
  if [ "$EPIC_OPEN_STORIES" = "1" ]; then
    # 본 story 1개만 OPEN — close 시 epic 도 close 예정
    PR_BODY="${PR_BODY}
Closes #${EPIC_ISSUE}"
  fi
else
  PR_BODY="Part of #${STORY_ISSUE}"
fi
gh pr create --title "<type>: <task-slug> (#${STORY_ISSUE})" --body "$PR_BODY"
```

### Step 7a (impl-task-loop)

PR 이미 생성된 상태 — merge only, **NO --squash** (3 commit 히스토리 보존):

```bash
gh pr merge || echo "[impl] merge 대기 — CI / reviewers"
git checkout main && git pull --ff-only 2>/dev/null || true
```

---

## 4. Step 4.5 — stories.md / backlog.md sync (impl 계열 한정)

`impl-task-loop` / `impl-ui-design-loop` / `direct-impl-loop` / `impl-loop` 의 inner task 에 한정. engineer `IMPL_DONE` 직후, code-validator 진입 *전*. 메인 직접 mechanical edit (agent 위임 X — 도메인 외).

> **범위 외 path 사용자 책임 (#292 root cause 일부)** — 본 Step 4.5 자동 sync 는 위 4 loop 한정. 다음 path 들은 *자동 sync 없음* — 메인이 별도 처리:
>
> - `/quick` (`quick-bugfix-loop`) — 작은 버그픽스 / cleanup 용. 일반적으로 stories.md task 와 직접 매핑 안 됨. 단 *드물게* stories.md task 를 다루는 경우 메인이 PR 머지 후 stories.md `[x]` 직접 박을 것.
> - engineer 직접 호출 (skill 우회) / 메인 직접 commit — *사용자 우회 path*. dcness 룰 미적용 영역.
> - **dcness 도입 *이전* 작업분** — 룰 도입 전 commit 들의 stories.md 잔재. 1회 backfill 이 정상 (예: jajang PR #232 패턴 — `gh issue list --state closed` 매핑 → unchecked task 일괄 `[x]`). 이후 path 가 정상화되면 drift 0 유지.
>
> drift 검출은 `/run-review` / `/audit-redo` 가 사후 안내 (현재 detector 부재 — 후속 추적).

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

> **트리거**: 마지막 step advance enum 확인 직후 사용자 대기 없이 즉시 호출 — 루프 종류 무관.

```bash
STATUS=$("$HELPER" finalize-run --expected-steps <N> --auto-review)
"$HELPER" end-run
echo "$STATUS"
```

`<N>` = catalog 행 `expected_steps` 컬럼. `--auto-review` 가 in-process 로 `harness.run_review` 호출 → review 리포트가 STATUS JSON 뒤에 chained 됨.

- review 결과는 `<run_dir>/review.md` 에 저장 + stderr 로 `[REVIEW_READY]` 신호 출력. 메인 Claude 가 guidelines §4 따라 세션에 그대로 출력.
- **`end-run` 안전망**: `finalize-run` 미호출 상태로 `end-run` 실행 시 자동으로 `finalize-run --auto-review` 대신 실행.
- `--auto-review` 생략 시 (사용자 명시 opt-out) — `dcness-review --run-id $RUN_ID --repo $(pwd)` 수동 호출 의무 (guidelines §3).
- **loop-insights 자동 누적** (issue #225): `--auto-review` 가 켜지면 동일 라이프사이클로 `redo-log` + WASTE/GOOD findings → `.claude/loop-insights/<agent>[-<mode>].md` 누적. 다음 run 의 `begin-step` 이 자동 read & 주입. 명시 opt-out 시 `--no-accumulate` 추가.

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

📝 메모리 candidate (#149):
- <caveat 발생 사유의 회고 — feedback / project type 후보. 다음 세션 회귀 방지용>
- <waste finding 의 반복 패턴 (예: ECHO_VIOLATION 2회+, MISSING_SELF_VERIFY 등)>
- <pr-reviewer NICE TO HAVE 중 자주 등장하는 항목>
- 후보 없음 시 "없음" 1줄

커밋/PR 진행할까요? (branch → PR → regular merge 자동) + 메모리 저장 진행?
```

worktree 처리도 사용자 결정.

**메모리 candidate 의무 (#149)**: caveat 발생 = 회귀 방지 신호. prose 본문에만 적고 끝내면 다음 세션에서 동일 caveat 재발. 메인은 위 양식의 *📝 메모리 candidate* 섹션을 *반드시* emit (없으면 "없음" 명시) — 사용자가 저장 여부 결정. 양식 없이 7b 보고 종료 = 룰 위반. 7a (clean) 도 review report 의 waste finding 이 있으면 같은 양식 적용.

**yolo 시**: `has_must_fix == false` + enum unexpected 만 (CHANGES_REQUESTED 1건 등) → 자동 7a 시도. `has_must_fix` 또는 `has_ambiguous` true → yolo 도 7b. yolo 라도 메모리 candidate 양식은 emit (사용자 위임 X — 본인이 저장 후 진행).

---

## 6. Step 8 — review 결과 인지

`--auto-review` stdout 자동 출력. 메인이 guidelines §4 룰대로 character-for-character echo. review 리포트의 must-fix / waste finding / per-Agent metric 즉시 인지 + 다음 run 회귀 방지에 활용.

review_main 실패 (예외) 시 helper stderr WARN — STATUS JSON 자체는 정상 출력. 메인이 사후 인지 후 수동 `dcness-review` 1회 재시도 권장.

---

## 7. Loop 카탈로그 (cross-ref)

8 loop 별 풀스펙 (`entry_point` / `task_list` / `advance` / `clean_enum` / `expected_steps` / `branch_prefix` / Step 별 `allowed_enums` / 분기 / `sub_cycles`) = [`orchestration.md`](orchestration.md) §4.

**메인 Claude 진입 시 의무**: orchestration §4.1 인덱스 → 해당 loop sub-section read.

### 7.1 catastrophic 룰 정합

[`orchestration.md`](orchestration.md) §2.3 5룰 + handoff-matrix §4.1 HARNESS_ONLY_AGENTS = `hooks/catastrophic-gate.sh` 강제. orchestration §4 의 각 loop sequence 가 이 룰 자연 충족 (code-validator → pr-reviewer 직전 PASS / engineer 직전 module-architect `READY` enum / feature-build-loop §4.2 Step 6 (module-architect × N) 진입 직전 architecture-validator PASS / PRD 변경 후 plan-reviewer + ux-architect 검토).

> Note: 이전 §7.0 인덱스 + §7.2~§7.10 행별 풀스펙은 [`orchestration.md`](orchestration.md) §4 로 흡수 (loop-catalog.md 폐기, 8 → 7 SSOT).

---

## 8. 참조

- [`orchestration.md`](orchestration.md) §2~§4 — 시퀀스 mini-graph / 8 loop 행별 풀스펙 / handoff cross-ref
- [`dcness-rules.md`](dcness-rules.md) — echo / Step 기록 / yolo / AMBIGUOUS / worktree / 결과 출력 / 권한 요청 / Karpathy
- [`../archive/conveyor-design.md`](../archive/conveyor-design.md) §2 / §3 / §7 — 컨베이어 디자인 + catastrophic gate (역사 자료)
- `harness/session_state.py` — helper CLI (`begin-run` / `end-run` / `begin-step` / `end-step` / `finalize-run` / `run-dir` / `auto-resolve`)
- `harness/run_review.py` — review 엔진 (`--auto-review` 호출 대상)
- `commands/<skill>.md` — skill 진입점 (input 정형화 + Loop 추천)
