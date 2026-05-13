---
name: impl-loop
description: impl task list (architect-loop §4.2 Step 4 module-architect × K 산출물) 를 *헤드리스 자식 세션 (`claude -p` cold start)* 으로 순차 처리하는 스킬. 메인 컨텍스트 누적 / N task 묶임 문제 해소. 사용자가 "전부 구현", "/impl-loop", "task 다 돌려", "epic 전체 구현", "/architect-loop 후 자동", "끝까지 구현" 등을 말할 때 반드시 이 스킬을 사용한다. 각 task 가 새 자식 세션 = 매 task 결과 = 1 PR + 1 이슈 close = `/run-review` 도 task 별 분리 분석 자연. clean run 만 자동 진행, 걸리는 게 생기면 (사용자 개입 필수) 즉시 정지. /architect-loop 종료 후 K 개 task 한 번에 처리하고 싶을 때.
---

# Impl Loop Skill — 헤드리스 자식 세션 chain

## Loop
`impl-task-loop × N` ([orchestration.md §4.9](../docs/plugin/orchestration.md) — 다중 task chain). 각 task = 새 `claude -p` 자식 세션 (cold start). 자식 세션 안의 inner loop = `impl-task-loop` (orchestration §4.3) — dcness skill `/impl` 본문 의무 따름.

## Inputs (메인이 사용자에게 받아야 할 정보)
- task list 또는 epic 경로 (예: `docs/milestones/v0.2/epics/epic-01-*/impl/*.md` glob)
- (선택) `--retry-limit N` — task 당 자동 재시도 한도 (default 3, 0 = 첫 실패 즉시 정지)
- (선택) `--escalate-on <signals>` — 즉시 정지 신호 (default `blocked`)
- (선택) `--timeout S` — 자식 세션 timeout 초 (default 1800 = 30분)

## 비대상 (다른 skill 추천)
- task 1개 → `/impl` (메인 turn 진행, 헤드리스 X — cold start 비용 회피)
- spec / design → `/product-plan` 또는 `/architect-loop`

## 워크트리 (기본 켜짐)
Skill 진입 시 *outer* 단계에서 자동 `EnterWorktree(name="impl-loop-{ts_short}")` 1회. 모든 자식 세션이 같은 outer worktree cwd 사용 — 직렬 진행이라 git 충돌 X. 사용자 발화에 정규식 `워크트리\s*(빼|없|말)` 매치 시에만 건너뜀. 자세히 = [`docs/plugin/loop-procedure.md`](../docs/plugin/loop-procedure.md) §1.1.

## 사전 read (lazy — 필요시만, #400)
정상 흐름은 본 skill 본문 + 인용된 docs §번호 만으로 진행. 본문에 박힌 catastrophic / Pre-flight gate 룰이 1차. *룰 모호 / 분기 발생* 시에만 `docs/plugin/loop-procedure.md` / `orchestration.md` §4.3 + §4.9 / `handoff-matrix.md` / `issue-lifecycle.md` 부분 read (grep + offset/limit). 통째 read 폐기 — 메인 cache_read baseline 감축.

## Pre-flight gate (skill 진입 직후, outer 1회)
[`docs/plugin/issue-lifecycle.md`](../docs/plugin/issue-lifecycle.md) §6 매치 강제 — 부모 epic stories.md 의 epic/story 이슈 매치 부재 시 즉시 STOP + 사용자 보고. silent skip 금지.

각 task 진입 직전 1회 확인 ([`commands/impl.md`](impl.md) "진입 직전 — task 진행 상태 1회 확인" 동일, issue #346):

```bash
TASK_SLUG=$(basename "<task-path>" .md)
git log --oneline --grep "$TASK_SLUG" | head -5
tail -50 "<task-path>"
```

이미 머지됨 발견 시 → 해당 task skip + 다음 task 진입. 부분 진행 + tail section 후속 결정 → 자식 세션이 `/dcness:impl <path>` 슬래시 직호출 받으면 `commands/impl.md` §진입 직전 task 진행 상태 1회 확인 룰 따라 자체 inject + 정상 진입.

## 절차 — 헤드리스 spawn

```bash
PLUGIN_ROOT="$(ls -d ${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/plugins/cache/dcness/dcness/*} 2>/dev/null | sort -V | tail -1)"
python3 "$PLUGIN_ROOT/scripts/impl_loop_headless.py" '<impl-glob>' \
  [--retry-limit 3] [--escalate-on blocked] [--timeout 1800]
```

스크립트 동작:

1. **glob 매치 + 정렬** — `impl/NN-*.md` prefix 기준 직렬 진행
2. **각 task 마다 새 `claude -p` 자식 세션 spawn** — cwd = outer worktree
3. **자식 세션 자동 컨텍스트** (실증 완료):
   - cwd `CLAUDE.md` auto-load (system-reminder `claudeMd` 섹션)
   - plug-in `SessionStart` hook 자동 inject (dcness 운영 룰 + `[dcness 활성 확인]` 토큰)
   - dcness skill 10개 자동 등록 (자식이 `/impl` 본문 의무 따름)
4. **자식 prompt = 슬래시 직호출** (#422 follow-up — chain 깊이 0):
   - 자식이 받는 user message = `/dcness:impl <task-path>` 1줄
   - CC 가 슬래시 파싱 → `commands/impl.md` 본문이 자식 system-reminder 에 자동 inject
   - 사전 read 의무 (architecture.md / adr.md / prd.md / 의존 task PR / 형제 story PR) /
     conveyor cycle (begin-run / begin-step / end-step / end-run) / enum 규칙
     모두 자식 instruction 으로 1st-class 도달
   - retry 시 `--append-system-prompt` 로 이전 에러 컨텍스트만 추가
   - 옛 [A]~[E] 5 묶음 자연어 본문 폐기 — 중복 + chain 3 단계 누락 위험
5. **결과 회수 3 layer**:
   - 1차 stdout 마지막 prose enum (PASS / FAIL / ESCALATE)
   - 2차 자식 종료 코드 (0 = clean / !=0 = error)
   - 3차 GitHub 이슈 close 확인 (`gh issue view <task-num> --json state`)
6. **enum 별 동작**:
   - `clean` → 다음 task 진입
   - `error` → 자동 재시도 (한도 `--retry-limit`, default 3)
   - `blocked` → 즉시 정지 + 사용자 위임

자식 세션 안의 작업 (코드 / 테스트 / commit / push / PR / 머지) = 자식 메인 자율. 메인은 *발사 + 결과 회수 + 분기* 만.

## 자식 세션 권한 / 분담

| 작업 | 자식 권한 |
|---|---|
| 코드 수정 (Edit / Write) | ✅ |
| 테스트 작성 / 실행 | ✅ |
| outer worktree branch 안 commit / push | ✅ (main-block hook 은 main 직접만 차단) |
| PR 생성 + 머지 (`gh pr create` + `gh pr merge --auto`) | ✅ |
| `Closes #<task-num>` trailer 로 이슈 자동 close | ✅ |
| main 직접 commit / push | ❌ |

## Outer / inner 컨벤션
- outer = 메인이 본 skill 호출 → outer worktree 생성 + spawn 스크립트 실행
- inner = 자식 세션 안에서 `/impl` 본문 의무 따라 진행 (test-engineer → engineer → code-validator → pr-reviewer)
- 각 자식 세션 = 1 PR + 1 이슈 close = `/run-review` 가 task 별 분리 분석 자연

## PR 생성 직전 — base 분기 체크 (자식 세션 의무, MUST)

각 자식 세션이 `gh pr create` 직전 `docs/stories.md` 상단 `**Base Branch:**` 줄 매치 1회 확인:
- 매치 → `gh pr create --base <매치 값>` (통합 브랜치 케이스)
- 매치 없음 → `gh pr create --base main` (default, trunk-based)

슬래시 직호출 시 자식이 [`commands/impl.md`](impl.md) §"PR 생성 직전 — base 분기 체크" 본문을 자동 instruction 으로 받음. 메인 outer 단계는 base 분기 결정 X — 자식 세션의 자율 영역.

## 후속 라우팅
- 각 task clean → 다음 task 자동 진입
- error → 자동 재시도 (한도까지). 한도 초과 시 정지 + 사용자 위임
- blocked → 즉시 정지 + 사용자 위임 (재호출 또는 수동 처리)
- 전체 완료 → 보고 (처리 N/N + 각 PR URL)

## 한계
- task 의존성 자동 판단 X (v1 = 무조건 직렬, SD impl 목차 순서 / list 순서 = 의존 표현)
- multi-task resume 미구현 — 한도 초과 / blocked 후 재실행 시 처음부터 (단 commit 된 task 는 [`commands/impl.md`](impl.md) §진입 직전 1회 확인 으로 자동 검출 → 자식 default 모드 = test-engineer 직진)
- 자식 세션 cold start cost — 매 task 30~120s latency 추가 (메인 컨텍스트 보호 가치와 trade-off)

## 안티패턴 (회귀 방지)
- ❌ task N 개를 `Bash run_in_background=true` 로 동시 spawn — v1 spec = 직렬. 동시 실행 시 git 충돌 + 메인이 wake 하면서 누적 컨텍스트 cache_read 비용 폭주 ([#216](https://github.com/alruminum/dcNess/issues/216) — pre-dcness RWH 시기 사례 \$1,531 / 단일 세션).
- ❌ 자식 세션 안에서 `claude -p` 재귀 호출 — 무한 spawn 위험. 자식은 *현재 task 한 개만* 처리.
- ❌ 자식이 PR body trailer 형식 강제 — 자식 메인 자율 영역 (issue-lifecycle.md §1.4 따름).
- ❌ escalate 신호 무시하고 다음 task 진행 — 사용자 부재 환경에서 추측 진행 = 폭주.

## 참고

- 본 스킬 구현: [`scripts/impl_loop_headless.py`](../scripts/impl_loop_headless.py)
- 실증 결과 (cwd = StockNoti 활성 프로젝트): plug-in `SessionStart` hook 자동 inject + skill 등록 + `[dcness 활성 확인]` 토큰 출력 확인 ([#375](https://github.com/alruminum/dcNess/issues/375))
- 그릴 D 가지 종합 — `claude -p` 자식 세션 spawn / GitHub 이슈 close 회수 / 워크트리 1 outer / 명령문 [A]~[E] inline
