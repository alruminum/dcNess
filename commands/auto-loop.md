---
name: auto-loop
description: impl task list 를 야간 자동 batch 로 처리하는 스킬. 매 task 마다 새 `claude -p` (cold start) 발사 → 컨텍스트 자동 클리어. 사용자가 "야간 자판기", "자고 일어나서 결과", "전체 epic 자동 실행", "/auto-loop", "밤새 돌려" 등을 말할 때 사용. /impl-loop 가 단일 세션 누적 (#216 사례 \$1,531) 이라면 본 스킬은 task 단위 cold start 로 컨텍스트 격리. 사용자 부재 환경 (야간) 가정 — escalate 신호 감지 시 즉시 정지.
---

# Auto Loop Skill — 야간 자판기

> impl task 디렉토리를 받아 매 task 마다 새 `claude -p` 프로세스 (cold start) 로 발사. dcness 활성 프로젝트의 SessionStart hook 이 자동 발화 → CLAUDE.md / docs / INSIGHTS / MEMORY 자동 inject. 매 task 끝나면 프로세스 종료 = 자동 컨텍스트 클리어.

## 언제 사용

- 사용자 발화: "야간 자판기", "/auto-loop", "자고 일어나서", "밤새 돌려", "전체 epic 자동"
- impl task 5+ 개를 *사용자 부재 환경* 에서 자동 진행하고 싶을 때
- 매 task 새 세션 = 컨텍스트 누적 0 (cache_read 폭주 회피, #216)

## 비대상

- 단일 task → `/impl`
- 대화 모드 chain → `/impl-loop` (사용자 옆에 있을 때)
- 한 줄 → `/quick`

## Inputs

- impl 디렉토리 경로 (예: `docs/milestones/v1/epics/epic-X/impl/`)
- (옵션) 매 호출 비용 cap (`--max-budget-usd <amount>` 기본 0.5)
- (옵션) 호출 모델 (기본 dcness 활성 모델)

## 사전 게이트 — issue-lifecycle.md §6 강제

skill 진입 즉시 메인 Claude 가 다음 매치 검증:

1. impl 디렉토리의 부모 stories.md 위치 추출 (`docs/milestones/vNN/epics/epic-NN-*/stories.md`)
2. stories.md 상단 매치 확인:
   - `**GitHub Epic Issue:** [#\d+]` (정식 등록), 또는
   - `**GitHub Epic Issue:** 미등록 (사유: …)` (issue-lifecycle.md §3 허용 모드)
3. 매치 0건 → 즉시 STOP + 사용자 보고. silent skip 금지.
4. 각 story 헤더 직하 `**GitHub Issue:** [#\d+]` 매치도 확인.

게이트 통과 후 자판기 발사.

## 핵심 동작

```bash
PLUGIN_ROOT="$(ls -d ${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/plugins/cache/dcness/dcness/*} 2>/dev/null | sort -V | tail -1)"
python3 "$PLUGIN_ROOT/scripts/auto_loop.py" <impl_dir> [--max-budget-usd 0.5]
```

자판기가 하는 일:
1. `<impl_dir>/*.md` 정렬 후 순차 처리 (파일명 prefix `NN-` 기준)
2. 각 파일마다 새 `claude -p` 프로세스 발사
   - dcness 활성 프로젝트라면 SessionStart hook 자동 발화 → CLAUDE.md / docs / SSOT inject
   - 매 호출 cold start = 자동 컨텍스트 클리어
3. prompt 에 inject:
   - 작업 본문 (impl/NN-foo.md 통째)
   - "(retry 시) 직전 시도 prose 파일 path"
4. 결과 prose 마지막 단락에서 결론 enum 추출
   - 정상 완료 (`IMPL_DONE` 등) → 다음 task 진행
   - escalate 계열 (`IMPLEMENTATION_ESCALATE`, `SPEC_GAP_FOUND`, `DESIGN_REVIEW_ESCALATE` 등) → 즉시 종료
   - 실패 (status 불명) → retry (최대 3회, prev_error path 자동 inject)
5. 매 호출 timestamp 기록 (stderr → log 파일)

## 자판기가 *안 하는* 것 (자율 영역)

- PR 생성 / 트레일러 분기 — 임시 메인 (claude -p 안) 이 자율 판단 (issue-lifecycle.md §1.4 따라)
- stories.md / backlog.md 체크박스 갱신 — 임시 메인이 자율 처리
- agent 호출 순서 결정 — 임시 메인이 dcness 룰 따라 자율
- escalate 결론 박을지 말지 — 임시 메인 자율

자판기는 *발사 + escalate 감지 + retry 카운팅* 만. 모든 작업 판단은 임시 메인 자율 = §1 자율성 정합.

## escalate enum 감지 (자판기 → 즉시 종료)

자판기가 결론 enum 보고 종료 결정:

| enum | 동작 |
|---|---|
| `IMPL_DONE` / `IMPL_PARTIAL` / `LIGHT_PLAN_READY` 등 정상 | 다음 task 진행 |
| `IMPLEMENTATION_ESCALATE` | 자판기 종료 |
| `SPEC_GAP_FOUND` | 자판기 종료 (architect SPEC_GAP 분기 — 야간엔 사용자 위임) |
| `DESIGN_REVIEW_ESCALATE` / `UX_REVIEW_ESCALATE` | 자판기 종료 |
| `VARIANTS_ALL_REJECTED` | 자판기 종료 |
| status 불명 (enum 추출 실패) | retry — 3회 후 자판기 종료 |

## 결과 보고

자판기 종료 시 stderr 에 1 페이지 요약:
- 처리 task: N/M
- 각 task: 이름 + 결과 enum + 소요 시간
- 종료 사유 (전체 완료 / escalate / retry 한도 초과)

## 워크트리

자판기는 *외부 프로세스* — 메인 Claude 의 워크트리 / 세션과 별개. 자판기 자체는 사용자 cwd 에서 발사. 매 `claude -p` 호출도 동일 cwd.

워크트리 분기는 *임시 메인 (claude -p 안)* 이 자율 판단:
- 매 호출이 dcness 활성 프로젝트로 진입 → SessionStart hook 발화 → 임시 메인이 dcness 룰 따라 워크트리 처리

## 비용 제어

- `--max-budget-usd <amount>` 매 호출 cap (기본 $0.5). 폭주 방지.
- *전체 batch 비용* = 매 호출 cap × task 수 + retry 비용

추정 (epic 1개 = 10 task 가정):
- Opus 4.7 (1M context): ~$8~10
- Haiku 4.5 (사용자 선택 옵션): 큰 폭 ↓ (quality 트레이드)

## 사전 read

- [`docs/plugin/issue-lifecycle.md`](../docs/plugin/issue-lifecycle.md) §6 (mid-flow 게이트) + §1.4 (PR 트레일러)
- [`docs/plugin/handoff-matrix.md`](../docs/plugin/handoff-matrix.md) (escalate enum 카탈로그)
- [`docs/plugin/dcness-rules.md`](../docs/plugin/dcness-rules.md) §1 (자율성 원칙)

## 한계 / v1 범위

- 의존성 자동 판단 X (impl 목차 순서 = 의존)
- task 병렬 실행 X (직렬만)
- 매 호출이 *별 다른 prompt* 라 prompt cache 효율 제한적
- Agent tool 호출 가능 여부 첫 호출에서 검증 (가능 = 하이브리드, 불가 = 단순 batch)

## 안티패턴 (회귀 방지)

- ❌ 단일 세션에 8 task 누적 — `/impl-loop` 의 #216 사례. 본 스킬이 그것의 cold start 자동화 버전.
- ❌ 자판기가 PR body 트레일러를 직접 박음 — *형식 강제*. 임시 메인 자율 영역.
- ❌ 자판기가 status JSON 신설 컨벤션 도입 — dcness §1 위반. GitHub 이슈 시스템 그대로 활용.
- ❌ escalate 신호 무시하고 다음 task 진행 — 사용자 부재 환경에서 추측 진행 = 폭주.
