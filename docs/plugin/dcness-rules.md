# dcness Rules (SSOT — 모든 dcness skill 공통)

> dcness plugin 활성 프로젝트 (`init-dcness` 등록) 의 매 세션에 SessionStart 훅이 본 내용을 system-reminder 로 inject. CC 자동 인지.
> 룰 추가 시 본 파일에만 append — skill 들은 cross-ref 만.

## 1. 라우팅 가이드

세션 시작 시 이 테이블 외 추가 read 하지 말 것 — skill 트리거 시 해당 skill 파일의 `## 사전 read` 섹션이 정확한 경로와 섹션 번호를 안내한다.

| 상황 | 읽어야 할 문서 | 섹션 |
|---|---|---|
| 루프 진입 / 시퀀스 결정 | [`orchestration.md`](orchestration.md) | §3 mini-graph + §4 해당 loop |
| Step 0~8 실행 절차 | [`loop-procedure.md`](loop-procedure.md) | 전체 |
| agent 호출 분기 / retry / escalate 한도 | [`handoff-matrix.md`](handoff-matrix.md) | §1~§3 |
| agent 접근 권한 (Write/Read 경계) | [`handoff-matrix.md`](handoff-matrix.md) | §4 |
| 실존 검증 룰 전문 + 안티패턴 | [`../internal/main-claude-rules.md`](../internal/main-claude-rules.md) | §1 |
| Karpathy 4원칙 전문 + agent 매핑 | [`../internal/main-claude-rules.md`](../internal/main-claude-rules.md) | §3 |
| dcness 자체 작업 룰 (300줄 cap 등) | [`../internal/self-guidelines.md`](../internal/self-guidelines.md) | 전체 |

skill 들은 input 정형화 + Loop 추천만, 절차는 loop-procedure, loop spec 은 orchestration §4.

## 2. 가시성 룰 — MUST

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

## 3. Step 기록 룰

Agent 호출 1회 = `helper begin-step` + `helper end-step` 1쌍 의무. 표준 시퀀스는 [`loop-procedure.md`](loop-procedure.md) §3.1.

### POLISH / 재호출 step 이름 컨벤션

- POLISH 사이클 (cycle ≤2): `engineer:POLISH-1`, `engineer:POLISH-2`
- 재호출 (TESTS_FAIL → engineer attempt 1+): `engineer:IMPL-RETRY-1`, `engineer:IMPL-RETRY-2`
- 각각 별도 begin/end-step 1쌍.

### 안티패턴

- ❌ engineer 자체 commit/PR 만든 후 git status 확인 → end-step engineer 호출 *skip*
- ❌ pr-reviewer CHANGES_REQUESTED 받고 engineer POLISH Agent 호출 시 begin/end-step 안 둘러쌈
- ❌ Agent 호출 후 사용자 입력 받느라 end-step 보류 → 다음 step 진입 시 망각
- ❌ multi-task 진행 중 task 간 보고 작성 후 begin-step 다시 안 부름

### helper 안전망 (자동 검출)

- **drift WARN**: `end-step` 호출 시 live.json `current_step` 과 `args.agent` 불일치 → stderr WARN
- **step count WARN**: `finalize-run --expected-steps N` row count 미달 → stderr WARN
- 자동 보정 X — 메인이 사후 인지 + `/run-review` 진단

## 4. run-review (opt-out fallback)

> primary path = `finalize-run --auto-review` ([`loop-procedure.md`](loop-procedure.md) §5.1). 본 섹션은 사용자가 `--auto-review` 를 명시 opt-out 한 경우의 fallback.

```bash
python3 -m harness.run_review --run-id "$RUN_ID" --repo "$(pwd)"
```

또는 plugin scripts wrapper:
```bash
"$(dirname "$HELPER")/dcness-review" --run-id "$RUN_ID" --repo "$(pwd)"
```

- skip 금지 — 사용자 보고 *전* 1회 의무

## 5. 결과 출력 룰 — Bash collapsed 회피

`/run-review` 또는 임의 Bash 명령의 stdout 을 **텍스트 응답으로 character-for-character 복사**:

- Bash 출력 = CC UI 에서 collapsed (사용자가 ctrl+o 안 누르면 안 보임)
- 메인 Claude 가 텍스트 응답으로 *그대로* 복사 = 자동 가시
- **금지**:
  - 마크다운 테이블 → ASCII 박스 변환
  - 섹션 생략 / 축약 / 재배치
  - 자체 해석 ("핵심은~", "정리하면~") 본문 사이 삽입
- 리포트 *끝* 별도 줄에서 코멘트 1~3줄은 허용

## 6. yolo 모드

발화에 `yolo` / `auto` / `끝까지` / `막힘 없이` / `다 알아서` keyword 시 ON.

| 상황 | 비-yolo | yolo |
|---|---|---|
| `CLARITY_INSUFFICIENT` / `*_ESCALATE` (soft) / `AMBIGUOUS` | 사용자 위임 | `auto-resolve` 적용 |
| `SPEC_GAP_FOUND` | 사용자 위임 | architect SPEC_GAP cycle (≤2) |
| `TESTS_FAIL` / validator FAIL | 재시도 (≤3) | 동일 |
| `IMPL_PARTIAL` | engineer 재호출 (split ≤ 3) | 동일 — 새 context window |
| `CHANGES_REQUESTED` | 사용자 위임 | engineer POLISH (cycle ≤2) |
| Step 7 caveat (NICE TO HAVE only, MUST FIX 0) | 사용자 위임 | 7a 자동 |
| catastrophic 룰 (PreToolUse §2.3) | hard safety | hard safety (yolo 우회 X) |

```bash
RESOLVE_JSON=$("$HELPER" auto-resolve "<agent>:<enum_or_mode>")
# JSON: {"action":..., "hint":..., "next_enum":...}
# unmapped 시 yolo 도 사용자 위임 fallback
```

## 7. AMBIGUOUS cascade

`end-step` stdout = `AMBIGUOUS` 시:
1. 재호출 1회 (결론 enum 명시 요청)
2. 재호출도 AMBIGUOUS → 사용자 위임 (enum 후보 + prose 발췌)

## 8. worktree 격리

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

자세히 = `docs/archive/conveyor-design.md` §13.

## 9. 권한/툴 부족 시 사용자 요청

목표 달성에 가용 도구·권한·정보 부족 시 *추측 진행 X*. 메인 Claude 에게:
- (a) 무엇이 부족
- (b) 왜 필요
- (c) 어떻게 얻을 수 있는지

명시 요청 후 사용자 권한 부여 받고 진행.

## 10. 감시자 Hat (권고)

builder + 감시자 두 hat. **감시자 우선**.

매 sub completion notification 받으면 1줄 평가 + 결정 권고:
`PASS` / `REDO_SAME` / `REDO_BACK` / `REDO_DIFF` + 사유.

평가 입력: `<result>` 응답 텍스트 + `<usage>` (tool 횟수 / 시간) + 필요 시 `agent-trace.jsonl` tail.

REDO 신호: result 부실 / tool_uses 비정상 (1 미만 or 같은 tool 5회) / boundary 위반 stderr / trace 의 exit≠0 무시.

**미진한 결과 통과 = 가장 비싼 실수** (다음 step 더 큰 redo 부름). 토큰 절약 본능 이기게.

매 cycle 종료 시 `harness.redo_log.append(sid, rid, {...})` 1줄 권고. `agent-trace.jsonl` 은 hook 자동 — 메인 평가 시 `harness.agent_trace.tail()` 참조.

루프 재구성 자유 — 정적 시퀀스 강제 X. architect MODULE_PLAN 재실행, 다른 sub 호출 등 적극.

학습 진화: 같은 (sub, mode) 의 redo 빈도 누적 시 `/audit-redo` skill 로 1차 prompt 풍부화 검토 (Layer 1 즉시 + Layer 2 인프라 환류).
