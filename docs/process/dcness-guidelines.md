# dcness Guidelines (SSOT — 모든 dcness skill 공통)

> dcness plugin 활성 프로젝트 (`init-dcness` 등록) 의 매 세션에 SessionStart 훅이 본 내용을 system-reminder 로 inject. CC 자동 인지.
> 룰 추가 시 본 파일에만 append — skill 들은 cross-ref 만.
> Task-ID: DCN-CHG-20260430-26 (SSOT 분리 + hook inject).

## 1. 가시성 룰 (DCN-30-15) — MUST

매 Agent 호출 후 메인이 prose 5~12줄 의무 echo. 의무 템플릿:

```
[<task-id>.<agent>] echo

▎ <prose 의 ## 결론 / ## Summary / ## 변경 요약 섹션 본문 5~12줄>
▎ <섹션 부재 시 prose 첫 5~10줄 fallback>
▎ <필요 시 추가 본문 인용 — 12줄 cap>

결론: <ENUM>
```

- `<task-id>` = standalone 시 step 이름, `/impl-loop` 안 시 `b<i>.<agent>`
- `▎` 글자 (U+258E) 그대로 — 사용자 인식 패턴
- 5줄 미만 / 12줄 초과 = 룰 위반

### 자가 점검 (TaskUpdate(completed) 호출 *전* 4 항)

```
□ Agent prose 종이 (`<RUN_DIR>/.prose-staging/<step>.md`) read 했는가?
□ ## 결론 / ## Summary / ## 변경 요약 섹션 우선 추출했는가?
□ 의무 템플릿대로 5~12줄 echo 했는가?
□ 결론 enum 포함됐는가?
```

### 안티패턴 (절대 금지)

- ❌ 압축 paraphrase 1~2줄로 끝내기 ("결론: PASS, 다음 진입")
- ❌ table / code block 통째 생략 (행 수 줄여 인용)
- ❌ "토큰 아끼려" 결론만 echo
- ❌ 다음 Agent 호출 직전 echo (늦음 — end-step 직후 즉시)

## 2. Step 기록 룰 (DCN-30-25)

Agent 호출 1회 = `helper begin-step` + `helper end-step` 1쌍 의무.

### 메인 의무 시퀀스 (모든 sub-agent 호출에 동일)

```
"$HELPER" begin-step <agent> [<MODE>]    ← 의무 (skip 금지)
Agent(subagent_type=<agent>, ...)         ← prose 받음
RUN_DIR=$("$HELPER" run-dir)
PROSE_PATH="$RUN_DIR/.prose-staging/<step>.md"
# 메인이 prose 를 위 경로에 Write
ENUM=$("$HELPER" end-step <agent> [<MODE>] ...)  ← 의무 (skip 금지)
# 가시성 룰 의무 echo
```

### POLISH / 재호출 step 이름 컨벤션

- POLISH 사이클 (cycle ≤2): `engineer:POLISH-1`, `engineer:POLISH-2`
- 재호출 (TESTS_FAIL → engineer attempt 1+): `engineer:IMPL-RETRY-1`, `engineer:IMPL-RETRY-2`
- 각각 별도 begin/end-step 1쌍.

### 안티패턴 (jajang DCN-30-23 실측 사례)

- ❌ engineer 자체 commit/PR 만든 후 git status 확인 → end-step engineer 호출 *skip*
- ❌ pr-reviewer CHANGES_REQUESTED 받고 engineer POLISH Agent 호출 시 begin/end-step 안 둘러쌈
- ❌ Agent 호출 후 사용자 입력 받느라 end-step 보류 → 다음 step 진입 시 망각
- ❌ multi-batch 진행 중 batch 간 보고 작성 후 begin-step 다시 안 부름

### helper 안전망 (자동 검출)

- **drift WARN**: `end-step` 호출 시 live.json `current_step` 과 `args.agent` 불일치 → stderr WARN
- **step count WARN**: `finalize-run --expected-steps N` row count 미달 → stderr WARN
- 자동 보정 X — 메인이 사후 인지 + `/run-review` 진단

## 3. 루프 종료 시 `/run-review` 의무 (DCN-30-26)

`/quick` / `/impl` / `/impl-loop` / `/product-plan` 모든 skill 의 Step 7 (finalize-run + clean commit/PR) **직후 의무**:

```bash
# Step 7 commit/PR 끝난 후
python3 -m harness.run_review --run-id "$RUN_ID" --repo "$(pwd)"
```

또는 plugin scripts wrapper:
```bash
"$(dirname "$HELPER")/dcness-review" --run-id "$RUN_ID" --repo "$(pwd)"
```

- 잘한 점 + 잘못한 점 + per-Agent metrics 즉시 인지
- 회귀 (THINKING_LOOP / ECHO_VIOLATION / PLACEHOLDER_LEAK 등) 자동 발화
- skip 금지 — 사용자 보고 *전* 1회 의무

## 4. 결과 출력 룰 (DCN-30-26) — Bash collapsed 회피

`/run-review` 또는 임의 Bash 명령의 stdout 을 **텍스트 응답으로 character-for-character 복사**:

- Bash 출력 = CC UI 에서 collapsed (사용자가 ctrl+o 안 누르면 안 보임)
- 메인 Claude 가 텍스트 응답으로 *그대로* 복사 = 자동 가시
- **금지**:
  - 마크다운 테이블 → ASCII 박스 변환
  - 섹션 생략 / 축약 / 재배치
  - 자체 해석 ("핵심은~", "정리하면~") 본문 사이 삽입
- 리포트 *끝* 별도 줄에서 코멘트 1~3줄은 허용

근거: RWHarness `harness-review.md` 패턴 정합 + 가시성 룰 (DCN-30-15) 정신 동일.

## 5. yolo 모드

발화에 `yolo` / `auto` / `끝까지` / `막힘 없이` / `다 알아서` keyword 시 ON.

| 상황 | 비-yolo | yolo |
|---|---|---|
| `CLARITY_INSUFFICIENT` / `*_ESCALATE` (soft) / `AMBIGUOUS` | 사용자 위임 | `auto-resolve` 적용 |
| `SPEC_GAP_FOUND` | 사용자 위임 | architect SPEC_GAP cycle (≤2) |
| `TESTS_FAIL` / validator FAIL | 재시도 (≤3) | 동일 |
| `CHANGES_REQUESTED` | 사용자 위임 | engineer POLISH (cycle ≤2) |
| Step 7 caveat (NICE TO HAVE only, MUST FIX 0) | 사용자 위임 | 7a 자동 |
| catastrophic 룰 (PreToolUse §2.3) | hard safety | hard safety (yolo 우회 X) |

```bash
RESOLVE_JSON=$("$HELPER" auto-resolve "<agent>:<enum_or_mode>")
# JSON: {"action":..., "hint":..., "next_enum":...}
# unmapped 시 yolo 도 사용자 위임 fallback
```

## 6. AMBIGUOUS cascade

`end-step` stdout = `AMBIGUOUS` 시:
1. 재호출 1회 (결론 enum 명시 요청)
2. 재호출도 AMBIGUOUS → 사용자 위임 (enum 후보 + prose 발췌)

## 7. worktree 격리

발화에 `worktree` / `wt` / `격리` / `isolate` keyword 시:

```
EnterWorktree(name="<skill>-{ts_short}")
```

종료 시 squash 흡수 검사 후 자동:

```bash
UNMERGED_DIFF=$(git diff "main..$WORKTREE_BRANCH" -- ':^.claude' 2>/dev/null)
if [ -z "$UNMERGED_DIFF" ]; then
  ExitWorktree(action="remove", discard_changes=true)
else
  ExitWorktree(action="keep")
fi
```

자세히 = `docs/conveyor-design.md` §13.

## 8. (TBD) Epic / Story / Milestone 분할 기준

미정. 다음 후속 룰화 후보:
- 마일스톤 bump 임계 (PRD 변경량 / 외부 release 단위 등)
- 에픽 분할 단위 (사용자 플로우 / 기술 영역 / 사이즈)
- 스토리 분할 단위 (1 화면 / 1 기능 / 사이즈)
- 마일스톤 ↔ 에픽 ↔ 스토리 ↔ impl batch 계층 정의

현재 `~/.claude/CLAUDE.md` §4-6 의 *디렉토리 구조 + 명명 컨벤션* 만 박혀있음. 분할 *기준* 은 product-planner / architect 자율.

## 9. (TBD) Skill 외 커스텀 루프 가이드

미정. dcness skill 9개 (`/init-dcness` `/qa` `/quick` `/product-plan` `/impl` `/impl-loop` `/run-review` `/smart-compact` `/efficiency`) 외 시퀀스가 필요할 때 (예: 새 agent 조합 / 부분 단계 skip / 다른 순서) 가이드 룰화 후속.

`docs/orchestration.md` 의 §2 (시퀀스 카탈로그) + §3 (진입 경로) + §4 (결정표) 참조해 메인 자율 구성.

## 10. 권한/툴 부족 시 사용자 요청 (DCN-30-18 공통 지침)

목표 달성에 가용 도구·권한·정보 부족 시 *추측 진행 X*. 메인 Claude 에게:
- (a) 무엇이 부족
- (b) 왜 필요
- (c) 어떻게 얻을 수 있는지

명시 요청 후 사용자 권한 부여 받고 진행. (Karpathy 원칙 1 정합 — surface assumptions)

## 11. (참조) Karpathy 4 원칙 (DCN-30-17)

agent 별 적용:
- **원칙 1** — Think Before (가정 명시 / 다중 해석 / push back / 명확화) — product-planner / qa / 전 agent
- **원칙 2** — Simplicity First (요청 외 기능 X, 추상화 X) — architect / engineer
- **원칙 3** — Surgical Changes (요청한 것만, 인접 코드 X) — engineer / pr-reviewer
- **원칙 4** — Goal-Driven Execution (검증 가능 success criteria) — test-engineer / validator

각 agent prompt 에 적합한 원칙 박혀있음 (`agents/*.md` 참조).
