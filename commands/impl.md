---
name: impl
description: impl task (architect-loop §4.2 Step 4 module-architect × K 산출물) 1개를 받아 정식 impl 루프 (default = test-engineer → engineer → code-validator → pr-reviewer · fallback = module-architect 선두 추가) 자동 진행하는 스킬. 사용자가 "구현해줘", "/impl <task>", "이 task 구현", "impl 루프", "버그픽스", "한 줄 수정" 등을 말할 때 반드시 이 스킬을 사용한다. /architect-loop 의 후속 — architect-loop 가 `impl/NN-*.md` 본문 detail 까지 채운 산출물의 task list 1개씩 처리. 버그픽스 케이스 = /issue-report 분류 후 본 스킬 fallback path (module-architect 선두 추가) 진입.
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
- spec / design 단계 → `/product-plan` (PRD) 또는 `/architect-loop` (설계)
- 다중 task 자동 chain → `/impl-loop`
- task 부재 (계획 X) → `/issue-report` (분류 후 impl-task-loop fallback) 또는 `/product-plan`

## 진입 모드 — default vs fallback (위치 도장)
- task 경로 매치 + 정식 위치 (`docs/milestones/v\d+/epics/epic-\d+-*/impl/\d+-*.md`) 파일 존재 → **default**: test-engineer 직진 (module-architect skip).
- 매치 실패 / 파일 부재 → **fallback**: module-architect 1번 호출 후 test-engineer 진입.
- 근거: architect-loop §4.2 의 Step 4 (module-architect × K) 가 정식 위치 impl 파일 본문 detail 까지 채움. 정식 경로 + 파일 존재 = 통과 보장 (위치 자체가 도장).

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

## 부모 이슈 본문 read 의무 (MUST)

Pre-flight gate 통과 후, 매치된 epic / story / task 이슈 번호 *각 본문 read 의무*:

```bash
gh issue view <epic-num> | head -80
gh issue view <story-num> | head -80
gh issue view <task-num> | head -80
```

이슈 본문에 수용 기준 / 추가 컨텍스트 / 결정 사항이 박혀있을 수 있음. read 안 하면 *impl 파일 누락 컨텍스트* 미인지 위험.

근거: `/impl-loop` 헤드리스 자식 세션 명령문 의무와 정합 ([#375](https://github.com/alruminum/dcNess/issues/375)). 메인 직접 호출 시도 같은 룰.

## impl 파일 사전 read 의무 (MUST — module-architect 7 원칙 정합)

`/impl` 진입 시 engineer / test-engineer 가 impl 파일의 `## 사전 준비` 섹션 따라 다음 파일 read 의무 (`agents/module-architect.md` §impl 파일 7 원칙):

1. `docs/architecture.md` — 모듈 구조 / 시그니처 / 의존성 흐름
2. `docs/adr.md` — 핵심 설계 결정 (부재 시 silent skip)
3. `docs/prd.md` — 비즈니스 요구사항
4. (의존 task 있을 시) 이전 step 머지 PR — impl 파일의 *의존 task slug* 따라 `gh pr list --search "<slug>" --state merged --json url --jq '.[0].url'` 호출 후 read

→ agent prompt 에 impl 파일 경로 박으면 agent 가 자체 read. *메인 Claude 가 사전 inject* 불필요 (impl 파일 안 진입 prompt 가 강제).

**추가 — 메인 직접 read 의무 (강조)**: agent prompt 경로 박는 것 외에 메인 Claude 가 *진입 전* `docs/architecture.md` + `docs/adr.md` 본문 *다시 read* 의무. 이번 task 와 연관된 모듈 / 결정 사항 확인 후 진입 (의도 모르고 덮어쓰는 회귀 회피). `/impl-loop` 헤드리스 자식 세션 명령문 의무와 정합 ([#375](https://github.com/alruminum/dcNess/issues/375)).

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
[`docs/plugin/loop-procedure.md`](../docs/plugin/loop-procedure.md) §1~§6 + [`docs/plugin/orchestration.md`](../docs/plugin/orchestration.md) §4.3 (`impl-task-loop` 풀스펙) 따름. UI 감지 시 §4.4 (`impl-ui-design-loop`).
