---
name: impl
description: impl task (feature-build-loop §4.2 Step 6 module-architect × N 산출물) 1개를 받아 정식 impl 루프 (default = test-engineer → engineer → code-validator → pr-reviewer · fallback = module-architect 선두 추가) 자동 진행하는 스킬. 사용자가 "구현해줘", "/impl <task>", "이 task 구현", "impl 루프", "버그픽스", "한 줄 수정" 등을 말할 때 반드시 이 스킬을 사용한다. /product-plan 의 후속 — feature-build-loop 가 `impl/NN-*.md` 본문 detail 까지 채운 산출물의 task list 1개씩 처리. 버그픽스 케이스 = /qa 분류 후 본 스킬 fallback path (module-architect 선두 추가) 진입.
---

# Impl Skill

## Loop
`impl-task-loop` ([orchestration.md §2.1 / §4.3](../docs/plugin/orchestration.md)).
UI 디자인 mid-loop 필요 시 → `impl-ui-design-loop` (orchestration §4.4) 자동 전환.

## Inputs (메인이 사용자에게 받아야 할 정보)
- task 경로 (필수, 예: `docs/milestones/v0.2/epics/epic-01-*/impl/01-*.md`)
- 이슈 번호 (있으면)
- attempt 한도 확인 (engineer 3 / POLISH 2 / module-architect 보강 cycle 2 — 기본값)

## 비대상 (다른 skill 추천)
- spec / design 단계 → `/product-plan` (`feature-build-loop`)
- 다중 task 자동 chain → `/impl-loop`
- task 부재 (계획 X) → `/qa` (분류 후 impl-task-loop fallback) 또는 `/product-plan`

## 진입 모드 — default vs fallback (위치 도장)
- task 경로 매치 + 정식 위치 (`docs/milestones/v\d+/epics/epic-\d+-*/impl/\d+-*.md`) 파일 존재 → **default**: test-engineer 직진 (module-architect skip).
- 매치 실패 / 파일 부재 → **fallback**: module-architect 1번 호출 후 test-engineer 진입.
- 근거: feature-build-loop §4.2 의 Step 7 (module-architect × N) 이 정식 위치 impl 파일 본문 detail 까지 채움. 정식 경로 + 파일 존재 = 통과 보장. (옛 `MODULE_PLAN_READY` 마커 grep 룰 폐기 — 위치 자체가 도장.)

## 후속 라우팅
- 본 loop clean → 자동 commit/PR (branch prefix = orchestration §4.3 decision rule: feat/chore/fix)
- caveat → 사용자 결정 (수동 7b)
- multi-task chain 필요 → `/impl-loop`

## 사전 read (skill 진입 즉시)
`docs/plugin/loop-procedure.md` + `docs/plugin/orchestration.md` §4.3 + `docs/plugin/handoff-matrix.md` + `docs/plugin/issue-lifecycle.md` read 후 진행.

## 워크트리 (기본 켜짐)
Step 0 진입 시 자동 `EnterWorktree(name="impl-{ts_short}")`. 사용자 발화에 정규식 `워크트리\s*(빼|없|말)` 매치 시에만 건너뜀. 자세히 = [`docs/plugin/loop-procedure.md`](../docs/plugin/loop-procedure.md) §1.1.

## Pre-flight gate (Step 0 직후)
[`docs/plugin/issue-lifecycle.md`](../docs/plugin/issue-lifecycle.md) §6 매치 강제 — 부모 epic stories.md 상단 `**GitHub Epic Issue:** [#\d+]` 또는 `미등록 (사유: …)` 매치 0건 시 즉시 STOP + 사용자 보고. silent skip 금지.

## 진입 직전 — task 진행 상태 1회 확인 (MUST, issue #346)

본 task 가 *이미 머지된 상태* 인지 또는 *부분 진행 후 후속 정보* 가 plan 본문 (특히 tail section) 에 박혀있는지 1회 확인. 발견 시 wasted run 회피.

```bash
# 1. git log 에 task slug 머지 흔적
TASK_SLUG=$(basename "<task-path>" .md)
git log --oneline --grep "$TASK_SLUG" | head -5

# 2. plan tail section read — "Option α 채택 결과" / "§13.1" / "후속 갱신" 같은 후속 결정 기록
tail -50 "<task-path>"
```

결과 발견 시:
- 이미 머지됨 → 사용자 보고 + skill 종료 (재진입 X)
- 부분 진행 + 후속 결정 → tail section 내용을 진행 컨텍스트에 inject + 정상 진입

근거: jajang Epic 12 task 02 사례 (2026-05-09) — 이미 머지된 task 를 재진입 시도 → 3 분 + 컨텍스트 5% wasted. 진입 *전* 30 초 확인이 사후 회복보다 압도적 저비용.

## 절차
[`docs/plugin/loop-procedure.md`](../docs/plugin/loop-procedure.md) §1~§6 + [`docs/plugin/orchestration.md`](../docs/plugin/orchestration.md) §4.3 (`impl-task-loop` 풀스펙, Step 4.5 stories sync 포함) 따름. UI 감지 시 §4.4 (`impl-ui-design-loop`).
