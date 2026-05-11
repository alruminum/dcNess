---
name: impl-loop
description: impl task list (feature-build-loop §4.2 Step 7 module-architect × N 산출물) 를 순차 자동 chain 으로 처리하는 스킬. 사용자가 "전부 구현", "/impl-loop", "task 다 돌려", "epic 전체 구현", "/product-plan 후 자동", "끝까지 구현" 등을 말할 때 반드시 이 스킬을 사용한다. 각 task 마다 /impl 의 정식 루프 실행 + clean run 만 자동 진행 + caveat 시 사용자 위임. /product-plan 종료 후 N 개 task 한 번에 처리하고 싶을 때.
---

# Impl Loop Skill

## Loop
`impl-task-loop × N` ([orchestration.md §4.9](../docs/plugin/orchestration.md) — 다중 task chain).
inner = `impl-task-loop` (orchestration §4.3) per task.

## Inputs (메인이 사용자에게 받아야 할 정보)
- task list 또는 epic 경로 (예: `docs/milestones/v0.2/epics/epic-01-*/impl/*.md` glob)
- 진행 정책 — clean 자동 / caveat 멈춤 (default) 또는 yolo (orchestration §4.3 sub_cycles 자동 시도)
- attempt 한도 확인 (`/impl` 와 동일 default)

## 비대상 (다른 skill 추천)
- task 1개 → `/impl`
- spec / design → `/product-plan`

## Outer / inner 컨벤션 (DCN-30-12)
- outer task: `impl-<i>: <task 파일명>` (task list 길이 만큼 등록)
- inner sub-task: `b<i>.<agent>` prefix 의무 (loop-procedure.md §2 inner skip 금지)

## 후속 라우팅
- 각 task clean → 자동 7a + 다음 task
- caveat → 멈춤 + 사용자 위임 (재호출 또는 수동 처리)
- 전체 완료 → 보고 (처리 N/N + 각 PR URL)

## 사전 read (skill 진입 즉시)
`docs/plugin/loop-procedure.md` + `docs/plugin/orchestration.md` §4.3 + §4.9 + `docs/plugin/handoff-matrix.md` + `docs/plugin/issue-lifecycle.md` read 후 진행.

## 워크트리 (기본 켜짐)
Skill 진입 시 *outer* 단계에서 자동 `EnterWorktree(name="impl-loop-{ts_short}")` 1회. 모든 inner task 가 같은 워크트리 안에서 진행. 사용자 발화에 정규식 `워크트리\s*(빼|없|말)` 매치 시에만 건너뜀. 자세히 = [`docs/plugin/loop-procedure.md`](../docs/plugin/loop-procedure.md) §1.1.

## impl 파일 사전 read 의무 (MUST — module-architect 7 원칙 정합)

`/impl` 와 동일 — 각 task 진입 시 engineer / test-engineer 가 impl 파일의 `## 사전 준비` 섹션 따라 read 의무 (`docs/architecture.md` / `docs/adr.md` / `docs/prd.md` + 의존 task 머지 PR). 자세히 = [`commands/impl.md`](impl.md) §impl 파일 사전 read 의무.

## Pre-flight gate (각 task 진입 직전)
[`docs/plugin/issue-lifecycle.md`](../docs/plugin/issue-lifecycle.md) §6 매치 강제 — 부모 epic stories.md 의 epic/story 이슈 매치 부재 시 해당 task STOP + 사용자 보고. silent skip 금지.

각 task 진입 *직전* 1회 확인 (`/impl` "진입 직전 — task 진행 상태 1회 확인" 동일, issue #346):

```bash
TASK_SLUG=$(basename "<task-path>" .md)
git log --oneline --grep "$TASK_SLUG" | head -5
tail -50 "<task-path>"
```

이미 머지됨 발견 시 → 해당 task skip + 다음 task 진입. 부분 진행 + tail section 후속 결정 → 진행 컨텍스트 inject + 정상 진입.

## 절차
[`docs/plugin/loop-procedure.md`](../docs/plugin/loop-procedure.md) §1~§6 + [`docs/plugin/orchestration.md`](../docs/plugin/orchestration.md) §4.3 (inner) + §4.9 (chain 정책) 따름.

## 한계
- task 의존성 자동 판단 X (v1 = 무조건 직렬, SD impl 목차 순서 / list 순서 = 의존 표현)
- multi-task resume 미구현 — caveat 후 재실행 시 처음부터 (단 commit 된 task 는 정식 위치 + 파일 존재 자동 검출 → default 모드 = test-engineer 직진)

## 안티패턴 (회귀 방지)
- ❌ task N 개를 `Bash run_in_background=true` 로 동시 spawn 후 `pgrep` / `ps -p` / `tail` 로 ScheduleWakeup polling — v1 spec = 직렬. 메인이 wake 하면서 누적 컨텍스트 cache_read 비용 폭주 ([#216](https://github.com/alruminum/dcNess/issues/216) — pre-dcness RWH 시기 사례 \$1,531 / 단일 세션). ScheduleWakeup tool 가이드 (default 1200~1800s, 270s 금지) 도 동일 권고.
- ❌ 단일 세션에 8 task 누적 진행 — 컨텍스트 4M+ 토큰까지 부풀어 모든 후속 wake 가 거대 cache_read. task 단위 새 세션 + `/smart-compact` resume 권장.
