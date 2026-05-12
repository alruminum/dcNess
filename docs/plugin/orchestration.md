# Orchestration Rules — dcNess SSOT

> **Status**: ACTIVE
> **Scope**: dcNess 가 plugin 으로 배포돼 *사용자 프로젝트* 에서 활성화될 때의 시퀀스 / 진입 경로 / 8 loop 행별 풀스펙 SSOT.
> **본 문서 = "what"** (어떤 시퀀스 / 어떤 loop). **mechanics ("how")** = [`loop-procedure.md`](loop-procedure.md). **agent 측 강제 ("who")** = [`handoff-matrix.md`](handoff-matrix.md).

---

## 0. 정체성 — 강제하는 것 / 강제 안 하는 것

> **🔴 대 원칙** ([`dcness-rules.md`](dcness-rules.md) §1 §1 직접 인용):
> **harness 가 강제하는 것은 단 2가지 — (1) 작업 순서, (2) 접근 영역. 그 외 모두 agent 자율.**
> - **작업 순서** = 시퀀스 (code-validator → engineer → pr-reviewer 등) + retry 정책
> - **접근 영역** = file path 경계 (agent-boundary ALLOW/READ_DENY) + 외부 시스템 mutation 차단 (push, gh issue, plugin 디렉토리)
> - **출력 형식 / handoff 형식 / preamble 구조 / marker / status JSON / Flag = agent 자율, harness 강제 X.**

본 SSOT 는 위 2 개 강제 영역만 정의. 형식 강제 (마커 / status JSON / Flag) 는 [`dcness-rules.md`](dcness-rules.md) §1 에 의해 폐기 — 본 문서 안에서도 그 어휘는 사용하지 않는다.

### 0.1 형식 변환 메모 (RWHarness → dcness)

- 마커 (`---MARKER:X---`) → **prose 마지막 단락 enum 단어** + `harness/signal_io.py interpret_signal`
- 핸드오프 페이로드 → **`.claude/harness-state/<run_id>/<agent>[-<MODE>].md` prose 디렉토리** (구조 자유)
- Flag 시스템 → **`.attempts.json` 단순 카운터** (recovery state 만)
- enum 해석 = `harness/interpret_strategy.py` heuristic-only (LLM fallback 폐기 — ambiguous 시 메인이 cascade)

---

## 1. 적용 모드

### 1.1 Plugin 사용자 프로젝트 모드 (본 SSOT 정 scope)

dcNess 가 plugin (`dcness@dcness`) 으로 사용자 프로젝트에 활성화된 환경. 다음 모두 강제:

- 본 문서 §2 게이트 시퀀스 (catastrophic 보존)
- handoff-matrix §4 권한 매트릭스 (agent-boundary hook 으로 강제)
- proposal §2.5 catastrophic 원칙 (src/ 외 mutation 차단, plugin-write-guard, READ_DENY)

### 1.2 메인 dcNess 자체 작업 모드 (현재 본 저장소)

dcNess 저장소 자체에서 메인 Claude 가 직접 작업하는 환경. 본 문서는 *권고*.

- CLAUDE.md §0 정합 — "system-architect / module-architect / code-validator / engineer 위임 강제 없음"
- 거버넌스 (main-block + git-naming + pytest) 만 강제 (`CLAUDE.md §1~§2`)
- 시퀀스 / 권한 매트릭스는 *읽고 따르는 가이드*. 위반 시 hook 차단 X.

---

## 2. 게이트 시퀀스 (큰 흐름)

### 2.1 최소 패스 (구현 루프)

```mermaid
flowchart TD
    entry{진입}
    plan[fallback: module-architect]
    test[test: test-engineer attempt 0]
    impl[impl: engineer attempt 0..3]
    cv[code-validator]
    review[review: pr-reviewer]
    merge[merge: PASS 후 자동 + regular]
    cleanup[post-commit cleanup]

    entry -->|impl/NN-*.md 정식 경로 존재<br/>= architect-loop 통과물| test
    entry -->|impl 부재 = 즉석 task| plan
    plan -->|PASS| test
    test -->|PASS| impl
    test -->|SPEC_GAP_FOUND| sg[module-architect 보강]
    impl -->|IMPL_DONE| cv
    impl -->|SPEC_GAP_FOUND| sg
    impl -->|TESTS_FAIL| impl
    impl -->|IMPLEMENTATION_ESCALATE| esc((escalate))
    sg -->|PASS| impl
    sg -->|ESCALATE| esc
    cv -->|PASS| review
    cv -->|FAIL| impl
    cv -->|ESCALATE| esc
    review -->|PASS| merge
    review -->|FAIL| polish[engineer POLISH]
    polish -->|POLISH_DONE| review
    merge --> cleanup
```

> default 진입 = test-engineer (impl/NN-*.md 정식 경로 존재 = architect-loop §4.2 가 module-architect × N 마쳐 본문 detail 까지 채운 산출물). fallback (즉석 task / 정식 경로 부재) 만 module-architect 호출.

### 2.2 UI 작업 추가 시 design 단계 삽입

```mermaid
flowchart TD
    plan[plan: module-architect]
    design[design: designer 1 시안]
    pick[사용자 직접 PICK]
    test[test: test-engineer]
    impl[...]

    plan --> design
    design -->|PASS| pick
    design -->|ESCALATE| esc((escalate))
    pick -->|OK| test
    pick -->|NG, 다시| design
    test --> impl
```

`[design]` 단계가 `[plan]` 과 `[test]` 사이에 삽입. designer 1 시안 → 사용자 직접 PICK (Pencil 캔버스 또는 `design-variants/<screen>-v<N>.html`). 거절 시 사용자가 designer 재호출 자유 결정 — 명시 round 한도 X.

### 2.3 catastrophic 시퀀스 (보존 의무)

다음은 *어떤 동적 결정* 으로도 우회 금지 — `hooks/catastrophic-gate.sh` 가 PreToolUse 강제:

1. **src/ 변경 후 code-validator PASS 없이 pr-reviewer 호출 금지** (§2.3.1)
2. **engineer 가 module-architect `PASS` enum 발화 없이 src/ 작성 금지** (§2.3.3 — 신규 / 보강 / 버그픽스 모든 케이스 동일)
3. **PRD 변경 후 plan-reviewer PASS 없이 `/architect-loop` 진입 금지** (§2.3.4 — PRD 검증은 `/product-plan` 책임. 자연어 룰 — 메인 영역 강제)
4. **module-architect × N (architect-loop §4.2 Step 6) 진입 직전 architecture-validator PASS 없이 진입 금지** (§2.3.5 — architect-loop 한정 코드 강제)

이는 proposal §2.5 원칙 4 ("흐름 강제는 catastrophic 시퀀스만") 의 catastrophic 백본.

---

## 3. 진입 경로별 시나리오 (mini-graph 6 개)

> 8 loop 행별 풀스펙 = 본 문서 §4. 본 §3 = mini-graph (what), §4 = 행별 풀스펙 (how) 1:1.
> 7 loop name (`architect-loop` §3.1.5, `impl-task-loop` §2.1, `impl-ui-design-loop` §2.2, `qa-triage` §3.5, `ux-design-stage` §3.2, `ux-refine-stage` §3.3, `direct-impl-loop` §3.4) — §4 행 ID.
> 실행 절차 (Step 0~8 mechanics) = [`loop-procedure.md`](loop-procedure.md).

### 3.1 신규 기능 / PRD 변경 → `/product-plan` (§4.2)

```mermaid
flowchart LR
    qa[qa] --> main[메인 Claude<br/>그릴미 대화로 PRD/stories.md 직접 Write]
    main --> pr[plan-reviewer<br/>FULL 모드 외부 검증]
    pr -->|PASS| commit[PR 생성 + 머지<br/>+ epic/story 이슈 등록]
    pr -->|FAIL| confirm[메인 + 사용자<br/>findings 항목별 confirm + Edit patch]
    confirm --> pr
    pr -->|ESCALATE| esc((escalate))
    commit --> done((종료 — 사용자 결정))
    done -.->|다음 단계 권장| arch[/architect-loop §4.10/]
```

진입: `/product-plan` 스킬 또는 사용자 "기능 추가" 발화. 종료 후 사용자가 `/architect-loop` 호출 결정 (자동 진입 X).

### 3.1.5 PRD 머지 후 설계 단계 → `/architect-loop` (§4.10)

```mermaid
flowchart LR
    entry[/architect-loop 진입/] --> ux[ux-architect UX_FLOW<br/>+ 5 카테고리 self-check]
    ux -->|UX_FLOW_READY| c1[commit 1: ux-flow.md]
    ux -->|UX_FLOW_ESCALATE| esc((escalate))
    c1 --> sd[system-architect<br/>+ self-check<br/>+ impl 목차 표]
    sd -->|PASS| dv[architecture-validator<br/>Placeholder Leak + Spike Gate]
    dv -->|PASS| c2[commit 2: architecture.md + adr.md]
    dv -->|FAIL| sd
    dv -->|ESCALATE| esc
    c2 --> mp[module-architect × K<br/>impl 목차 행마다 1 호출]
    mp -->|PASS × K, 각 호출 후 commit| done[PR 생성 + 머지]
    mp -->|SPEC_GAP_FOUND / ESCALATE| esc
```

architect-loop = 1 epic 처리 단위. 워크트리 ON 자동 진입. PRD 머지 + epic/story 이슈 등록은 진입 전제 (`/product-plan` 책임). catastrophic §2.3.5 — module-architect × K 진입 직전 architecture-validator PASS 필수. 종료 = 1 PR (ux-flow + arch+adr + impl K = K+2 commit). 진입: 사용자 `/architect-loop <epic-path>` 명시.

### 3.2 UI 만 변경 → `ux-design-stage` (§4.6, 하네스 루프 없음)

```mermaid
flowchart LR
    ux[ux 스킬] --> designer
    designer -->|PASS| handoff((DESIGN_HANDOFF))
```

엔지니어 호출은 *사용자 결정*. 시퀀스 게이트 없음.

### 3.3 화면 리디자인 → `ux-refine-stage` (§4.7)

```mermaid
flowchart LR
    ux[ux 스킬 REFINE 감지] --> uxa[ux-architect UX_REFINE]
    uxa -->|UX_REFINE_READY| user((사용자 승인))
    user --> dr[designer SCREEN]
    dr -->|PASS| handoff((DESIGN_HANDOFF))
```

### 3.4 일반 구현 직접 호출 → `direct-impl-loop` (§4.8)

```mermaid
flowchart LR
    cli["impl_driver --impl <path> --issue <N>"] --> impl[구현 루프 §2.1]
```

`impl_driver` 코드는 후속 Task — §6 옵션 (a)/(b)/(c) 중 채택 후 구현.

### 3.5 버그 보고 분류 → `qa-triage` (§4.5)

```mermaid
flowchart LR
    qa[qa 스킬] --> qaa[qa agent]
    qaa -->|FUNCTIONAL_BUG| lp[impl-task-loop §4.3 fallback]
    qaa -->|CLEANUP| lp
    qaa -->|DESIGN_ISSUE| ds[designer 시퀀스 §3.2/3.3]
    qaa -->|KNOWN_ISSUE| stop((종료))
    qaa -->|SCOPE_ESCALATE| esc((escalate))
```

FUNCTIONAL_BUG / CLEANUP 둘 다 `impl-task-loop` fallback path 진입 (impl 부재 시 module-architect 선두 추가). TDD Guard (`hooks/tdd-guard.sh`) 강제로 light path 별도 분기 폐기.

---

## 4. 8 loop 행별 풀스펙

> *행별 풀스펙* SSOT (entry_point / task_list / advance / clean_enum / branch_prefix / Step 별 allowed_enums / 분기 / sub_cycles).
> 시퀀스 mini-graph + 진입 경로 = §3. 실행 절차 = [`loop-procedure.md`](loop-procedure.md). Step 4.5 sync 룰 = 폐기 (2026-05-12, 본 SSOT 단일화).

### 4.1 한눈 인덱스

| loop | entry_point | task_list (Step 1) | advance | clean_enum | expected_steps |
|------|-------------|--------------------|---------|------------|----------------|
| `architect-loop` (§3.1.5, §4.2) | `architect-loop` (사용자 명시) | ux-architect:UX_FLOW (self-check) / system-architect (self-check) / architecture-validator / module-architect × K | `UX_FLOW_READY` → `PASS` → `PASS` → `PASS × K` | advance 동일 | 3 + K (K = system-architect impl 목차 행 수) |
| `impl-task-loop` (§2.1, §4.3) | `impl` | (default) test-engineer / engineer:IMPL / code-validator / pr-reviewer · (fallback: impl 부재 시 module-architect 선두 추가) | `PASS` → `IMPL_DONE` → `PASS` → `PASS` | advance 동일 | 4 (default) / 5 (fallback) |
| `impl-ui-design-loop` (§2.2, §4.4) | `impl` (UI 감지) | (default) designer / 사용자 PICK / test-engineer / engineer:IMPL / code-validator / pr-reviewer · (fallback: impl 부재 시 module-architect 선두 추가) | `PASS` → 사용자 PICK → `PASS` → `IMPL_DONE` → `PASS` → `PASS` | advance 동일 | 6 (default) / 7 (fallback) |
| `qa-triage` (§3.5, §4.5) | `qa` | qa | (5 enum 모두 — 라우팅 추천) | advance 개념 X | 1 |
| `ux-design-stage` (§3.2, §4.6) | `ux` | ux-architect:UX_FLOW / designer / 사용자 PICK | `UX_FLOW_READY` → `PASS` → 사용자 PICK | advance 동일 | 3 |
| `ux-refine-stage` (§3.3, §4.7) | `ux` (REFINE) | ux-architect:UX_REFINE / designer / 사용자 PICK | `UX_REFINE_READY` → `PASS` → 사용자 PICK | advance 동일 | 3 |
| `direct-impl-loop` (§3.4, §4.8) | `impl_driver` (future) | `impl-task-loop` 동일 | `impl-task-loop` 동일 | `impl-task-loop` 동일 | 5 |

### 4.2 `architect-loop` 풀스펙

**branch_prefix**: `docs/<epic-slug>`. **워크트리**: ON 자동 (`EnterWorktree(name="architect-{ts_short}")` — [`loop-procedure.md`](loop-procedure.md) §1.1).

**전제 조건** (진입 전 충족 의무):
- PRD/stories.md 이미 머지 (`/product-plan` 책임)
- epic + story 이슈 등록 완료 (`scripts/create_epic_story_issues.sh`)
- 사용자가 `/architect-loop <epic-path>` 명시 호출 (자동 진입 X)

**Step 별 allowed_enums + commit**:
| step | agent[:mode] | allowed_enums | commit |
|---|---|---|---|
| 2 | ux-architect:UX_FLOW (5 카테고리 self-check 의무) | `UX_FLOW_READY,UX_FLOW_PATCHED,UX_REFINE_READY,UX_FLOW_ESCALATE` | commit 1 (`[docs] ux-flow <epic-slug>`) — PASS 직후 |
| 3 | system-architect (self-check 의무) | `PASS,ESCALATE` (산출물에 `## impl 목차` 표 — Story → impl 매핑 + K 행 + `task_index: i/total` 열) | (working tree only) |
| 3.5 | architecture-validator | `PASS,FAIL,ESCALATE` | commit 2 (`[docs] architecture + adr <epic-slug>`) — PASS 직후 |
| 4.1 ~ 4.K | module-architect (신규 케이스, occurrence 1..K) | `PASS,SPEC_GAP_FOUND,ESCALATE` | commit 3..K+2 (`[docs] impl <NN>-<slug>`) — 각 PASS 직후 |

**module-architect × K 단계 (Step 4)**:
- 입력 = system-architect 산출물의 `## impl 목차` 표. 메인이 표 행 (NN, 파일명, 대응 Story, `task_index = i/total`, 의존) 순회하며 module-architect 1번씩 호출
- 각 호출이 `docs/milestones/vNN/epics/epic-NN-*/impl/<NN>-<slug>.md` 새로 작성. **frontmatter `story: <N>, task_index: <i>/<total>` 의무** — impl-task-loop PR body Closes/Part of 판정 입력 ([`issue-lifecycle.md`](issue-lifecycle.md) §1.4)
- 호출 순서 = impl 목차 의존 순서 (선행 impl 본문이 후행 `## 의존성` 입력 → 순차)
- K 호출 모두 `PASS` → architect-loop clean 종료 (Step 5)

**Step 5 — commit / push / PR / 머지**:
- `git push -u origin docs/<epic-slug>` + `gh pr create` (PR body = 설계 산출물 요약, `Part of #<epic-issue>`)
- `bash scripts/pr-finalize.sh` 머지 (squash 금지 — 커밋 히스토리 보존)
- `ExitWorktree` (squash 흡수 검사 후 자동 keep/remove)

**분기**:
- ux-architect self-check FAIL → ux-architect 재진입 (cycle ≤ 2, prose 내부)
- `UX_REFINE_READY` → designer 분기 (ux-design-stage / ux-refine-stage 권장)
- `UX_FLOW_ESCALATE` → 사용자 위임
- architecture-validator `FAIL` → system-architect 재진입 (cycle ≤ 2)
- architecture-validator `ESCALATE` → 사용자 위임
- module-architect `SPEC_GAP_FOUND` → module-architect (보강 케이스) cycle (≤ 2) → 신규 케이스 재진입
- module-architect `ESCALATE` → 사용자 위임

**sub_cycles**: 위 분기 재호출 시 동일 agent 로 별도 begin/end-step 1쌍. occurrence 카운터가 파일명 충돌 자동 처리 ([`dcness-rules.md`](dcness-rules.md) §3.4). module-architect × K 의 K 호출 = `module-architect.md` / `module-architect-2.md` ... 자동 명명.

### 4.3 `impl-task-loop` 풀스펙

**branch_prefix decision rule**:
- task 내 신규 기능 (src 신규 파일 또는 인터페이스 추가) → `feat/<task-slug>`
- 리팩토링 / 정리 / 테스트 보강 only → `chore/<task-slug>`
- 버그픽스 (의도 vs 실제 격차 수정) → `fix/<task-slug>`
- 메인 Claude 가 task 의 ## 변경 요약 / engineer prose 보고 결정.

**진입 모드 — default vs fallback**:

| 모드 | 조건 | 시작 step | 합계 step |
|---|---|---|---|
| default | task 경로 매치 + 정식 위치 (`docs/milestones/v\d+/epics/epic-\d+-*/impl/\d+-*.md`) 파일 존재 | test-engineer | 4 |
| fallback | 위 매치 실패 (즉석 task / direct-impl-loop / impl 부재) | module-architect | 5 |

**근거**: architect-loop §4.2 의 Step 4 (module-architect × K) 가 정식 위치 impl 파일 본문 detail 까지 채움. 즉 정식 경로 + 파일 존재 = 본문 detail 보장 + architecture-validator PASS 통과물. module-architect 재호출 redundant. 위치 자체가 도장.

**commit 구조** ([`loop-procedure.md`](loop-procedure.md) §3.4):
| stage | 시점 | 내용 |
|---|---|---|
| branch + commit (src) + PR | code-validator PASS 직후 | branch 새로 + src 파일 + push + `gh pr create` |
| merge | PASS 직후 | `gh pr merge` |

> `docs/impl/NN.md` 는 `/architect-loop` 산출물이 *미리 머지* 한 상태 (main 안). impl-task-loop 안에서 별도 commit X.

**Step 별 allowed_enums (default 모드)**:
| step | agent[:mode] | allowed_enums |
|---|---|---|
| 2 | test-engineer | `PASS,SPEC_GAP_FOUND` |
| 3 | engineer:IMPL | `IMPL_DONE,IMPL_PARTIAL,SPEC_GAP_FOUND,TESTS_FAIL,IMPLEMENTATION_ESCALATE` |
| 4 | code-validator | `PASS,FAIL,ESCALATE` |
| 5 | pr-reviewer | `PASS,FAIL` |

**fallback 모드**: 위 step 앞에 `module-architect` (allowed_enums = `PASS,SPEC_GAP_FOUND,ESCALATE`) 1 step 추가.

**분기**:
- `IMPL_PARTIAL` → engineer IMPL 재호출 (split < 3, 새 context window — DCN-30-34). 초과 시 `IMPLEMENTATION_ESCALATE` (작업 분해 부족 — system-architect 재진입 권고 / impl 목차 분할 재검토).
- `SPEC_GAP_FOUND` → module-architect (보강 케이스) cycle (≤ 2) → engineer 재진입
- `TESTS_FAIL` → engineer IMPL 재시도 (attempt < 3, 초과 → `IMPLEMENTATION_ESCALATE`)
- code-validator `ESCALATE` → 본문 사유 prose 보고 메인 분기: spec 부재면 module-architect (보강), 재시도 한도 초과면 사용자 위임
- module-architect `ESCALATE` / `IMPLEMENTATION_ESCALATE` → 사용자 위임
- `FAIL` → engineer POLISH cycle (≤ 2)
- code-validator `FAIL` → engineer IMPL 재시도

**sub_cycles** (재호출 시 begin-step 은 동일 agent 사용 — occurrence 카운터가 `<agent>-N.md` 자동 처리. `dcness-rules.md §3.4`):
- `module-architect` (engineer/test-engineer SPEC_GAP_FOUND 시, 보강 케이스) — allowed_enums = `PASS,ESCALATE`
- `engineer POLISH` (FAIL 시, ≤ 2 회) — allowed_enums = `POLISH_DONE,IMPLEMENTATION_ESCALATE`
- `engineer IMPL` 재시도 (TESTS_FAIL/FAIL 시, attempt < 3) — engineer IMPL 동일
- `engineer IMPL` split (IMPL_PARTIAL 시, split < 3, DCN-30-34) — engineer IMPL 동일. prose 의 `## 남은 작업` 컨텍스트로 진입.

### 4.4 `impl-ui-design-loop` 풀스펙

**branch_prefix**: §4.3 와 동일 (`feat` / `chore` / `fix`).

**진입 모드 — default vs fallback**: §4.3 룰 그대로 (정식 경로 + 파일 존재 시 default = module-architect skip).

**Step 별 allowed_enums (default 모드)**:
| step | agent[:mode] | allowed_enums |
|---|---|---|
| 2 | designer | `PASS,ESCALATE` |
| 2.5 | (사용자 PICK) | — (메인이 시안 경로 안내 + 사용자 OK/NG. NG 시 designer 재호출 자유) |
| 3 | test-engineer | §4.3 동일 |
| 4 | engineer:IMPL | §4.3 동일 |
| 5 | code-validator | §4.3 동일 |
| 6 | pr-reviewer | §4.3 동일 |

**fallback 모드**: 위 step 앞에 `module-architect` (allowed_enums = `PASS,SPEC_GAP_FOUND,ESCALATE`) 1 step 추가.

**Step 2.5 — 사용자 PICK**: designer PASS 후 test-engineer 진입 *전* 메인이 사용자에게 시안 경로 (Pencil 캔버스 또는 `design-variants/<screen>-v<N>.html`) + node-id 안내 + OK/NG 받음. NG 시 designer 재호출 — round 한도 명시 X (사용자 자유 결정). step 컨벤션 = `user-pick-2.5` (helper begin/end-step 비대상).

**분기**:
- `ESCALATE` → 사용자 위임
- 나머지 = §4.3 분기 동일

**sub_cycles**: §4.3 동일 + `designer-ROUND-<n>` (사용자 NG 시 재생성, 사용자 자유 결정).

### 4.5 `qa-triage` 풀스펙

**branch_prefix**: commit X (분류만, 코드 변경 X).

**Step 별 allowed_enums**:
| step | agent[:mode] | allowed_enums |
|---|---|---|
| 2 | qa | `FUNCTIONAL_BUG,CLEANUP,DESIGN_ISSUE,KNOWN_ISSUE,SCOPE_ESCALATE` |

**enum 별 라우팅 추천** (advance 개념 없음 — 메인이 사용자 결정 받음):
- `FUNCTIONAL_BUG` → `impl-task-loop` (`/impl`) fallback path (impl 부재 시 module-architect 선두 추가)
- `CLEANUP` → `impl-task-loop` (`/impl`) fallback path
- `DESIGN_ISSUE` → `ux-design-stage` (`/ux`) 또는 designer 직접
- `KNOWN_ISSUE` → 종료
- `SCOPE_ESCALATE` → 사용자 위임 (큰 변경 / 다중 모듈)

**sub_cycles**: 없음. AMBIGUOUS 시 [`dcness-rules.md`](dcness-rules.md) §6 cascade.

### 4.6 `ux-design-stage` 풀스펙

**branch_prefix**: commit X (design handoff, 코드 X).

**Step 별 allowed_enums**:
| step | agent[:mode] | allowed_enums |
|---|---|---|
| 2 | ux-architect:UX_FLOW | `UX_FLOW_READY,UX_FLOW_PATCHED,UX_REFINE_READY,UX_FLOW_ESCALATE` |
| 3 | designer | `PASS,ESCALATE` |
| 3.5 | (사용자 PICK) | — (메인이 시안 경로 안내 + OK/NG. NG 시 designer 재호출 자유) |

**designer 환경 감지**: `docs/design.md` frontmatter `medium: pencil|html` 따라 분기. 박힘 X 면 designer Step 0 에서 detect + 사용자 역질문 (가용 시).

**분기**:
- `PASS` + 사용자 OK → DESIGN_HANDOFF 패키지 (이슈 코멘트 + design.md + 시안 파일) → 종료
- `PASS` + 사용자 NG → designer 재호출 (사용자 자유 결정)
- `UX_REFINE_READY` (ux-architect) → ux-refine-stage 진입
- `ESCALATE` / `UX_FLOW_ESCALATE` → 사용자 위임

**sub_cycles**: `designer-ROUND-<n>` (사용자 NG 시 재생성, 사용자 자유 결정).

### 4.7 `ux-refine-stage` 풀스펙

**branch_prefix**: commit X.

**Step 별 allowed_enums**:
| step | agent[:mode] | allowed_enums |
|---|---|---|
| 2 | ux-architect:UX_REFINE | `UX_REFINE_READY,UX_FLOW_ESCALATE` |
| 2.5 | (사용자 승인) | — (메인이 사용자에게 ux refine 결과 검토 요청. 거절 시 ux-architect 재호출) |
| 3 | designer | `PASS,ESCALATE` |
| 3.5 | (사용자 PICK) | — (§4.6 동일) |

**designer 환경 감지**: §4.6 동일.

**Step 2.5 — 사용자 승인**: ux-architect UX_REFINE_READY 후 designer 진입 *전* 메인이 사용자에게 refine 결과 prose 발췌 + 진행 여부 확인. 거절 시 ux-architect 재호출 (cycle ≤ 2). step 컨벤션 = `user-approval-2.5` (helper begin/end-step 비대상).

**분기**: §4.6 동일.

### 4.8 `direct-impl-loop` 풀스펙

§4.3 (`impl-task-loop`) 와 100% 동일. 차이점:
- entry_point = `impl_driver` CLI (현재 미구현, 후속 Task 예정)
- 사용자 task 경로 직접 명시 (skill UI 없음)

allowed_enums / 분기 / sub_cycles / branch_prefix decision rule = §4.3 인용.

### 4.9 다중 task chain (`impl-loop`)

`/impl-loop` = `impl-task-loop` × N. outer task `impl-<i>: <task>` + inner sub-task `b<i>.<agent>` (DCN-CHG-30-12). default = 4 sub-task (test-engineer / engineer / code-validator / pr-reviewer), fallback = 5 (module-architect 선두 추가). 각 task clean → 자동 7a + 다음 task. caveat → 멈춤 + 사용자 위임 (Step 2.5 — `commands/impl-loop.md` 참조).

---

## 5. Catastrophic vs 자율 영역

> proposal §2.5 원칙 4: **"impl_loop 시퀀스 (code-validator → engineer → pr-reviewer) = 보존, 시퀀스 *내부* 행동 = agent 자율"**

### 5.1 보존 (catastrophic — 코드 강제)

- §2.3 catastrophic 시퀀스 5 항목 (code-validator / architecture-validator / pr-reviewer 우회 금지 등)
- handoff-matrix §4.1 ALLOW_MATRIX (Write 경계)
- handoff-matrix §4.2 READ_DENY_MATRIX (Read 격리)
- handoff-matrix §4.3 DCNESS_INFRA_PATTERNS (인프라 보호)
- handoff-matrix §3 escalate 결론은 자동 복구 금지

### 5.2 자율 (agent 결정)

- prose 출력 형식 (markdown / 평문 / 표 자유)
- handoff 페이로드 형식 (prose 디렉토리 path 만 강제, 본문 구조 자유)
- preamble 구조 / agent prompt 안 thinking 분량
- agent 가 어떤 도구를 어떤 순서로 호출할지 (단 handoff-matrix §4 권한 매트릭스 안에서)
- mode 별 결론 enum 외 추가 emit (예: code-validator 가 PASS 외 보강 설명)

### 5.3 권고 (강제 X, 측정 + 사용자 개입)

- handoff-matrix §1 결정표의 "다음 trigger" — driver 자동 호출 시 따름. 메인 직접 작업 모드는 *권고*.
- handoff-matrix §2 retry 한도 — 카운터 측정. 한도 도달 시 escalate, 사용자 결정.
- 휴리스틱 hit rate 90%+ 목표 (`scripts/analyze_metrics.mjs` fitness)

---

## 6. 코드 Driver — 메인-주도 컨베이어 + PreToolUse 훅

> **메인 클로드 = 시퀀스 결정자. 컨베이어 (Python) = 멍청한 순회기. catastrophic backbone = PreToolUse 훅 강제.**

- 메인이 handoff-matrix §1 결정표 보고 `list[Step]` 짜서 컨베이어 호출
- 컨베이어 = 시퀀스 순회 + Agent 호출 + `signal_io.interpret_signal` 로 enum 추출 + `Step.advance_when` 비교
- enum ∈ advance_when 이면 다음 step. 아니면 `ConveyorPause` 반환 (예외 아님) — 메인이 받아 자율 처리
- §2.3 catastrophic 시퀀스 = `hooks/catastrophic-gate.sh` (PreToolUse Agent) 가 코드 hardcode 0 으로 강제
- 형식 강제 LLM 출력 (JSON 등) **사용 안 함** — proposal §2.5 (prose-only) 정합

상세 디자인 + 폐기된 옵션 카탈로그 (3 옵션 — RWHarness fork / 정적 dict / Orchestration Agent) = [`../archive/conveyor-design.md`](../archive/conveyor-design.md).

---

## 7. 참조

- [`handoff-matrix.md`](handoff-matrix.md) — agent 결정표 / Retry / Escalate / 접근 권한 SSOT
- [`loop-procedure.md`](loop-procedure.md) — 루프 실행 Step 0~8 mechanics
- [`dcness-rules.md`](dcness-rules.md) §1 — 본 SSOT 의 강제 영역 정의 현행 SSOT (대 원칙 + Anti-Pattern 5원칙)
- [`../archive/status-json-mutate-pattern.md`](../archive/status-json-mutate-pattern.md) — Prose-Only 원전 proposal (Phase 분할 / §11.4 도입 기준 / Risks) (역사 자료)
- [`../archive/conveyor-design.md`](../archive/conveyor-design.md) — 코드 driver 디자인 + 폐기된 옵션 카탈로그 (역사 자료)
- [`dcness-rules.md`](dcness-rules.md) — cross-cutting 룰 (echo / yolo / self-verify)
- [`../../CLAUDE.md`](../../CLAUDE.md) — 작업 절차 + 게이트 SSOT
- [`../archive/plugin-dryrun-guide.md`](../archive/plugin-dryrun-guide.md) — plugin 배포 dry-run (역사 자료)
- [`../archive/migration-decisions.md`](../archive/migration-decisions.md) §2.1 — RWHarness 모듈 분류 (impl_loop.py DISCARD) (역사 자료)
- `agents/*.md` — 각 agent prose writing guide + 결론 enum 출처 (system-architect / module-architect / engineer / test-engineer / code-validator / architecture-validator / designer / ux-architect / plan-reviewer / pr-reviewer / qa)
- `harness/signal_io.py` / `harness/interpret_strategy.py` — interpret_signal + heuristic
- `scripts/analyze_metrics.mjs` — fitness 측정
- RWHarness `docs/harness-spec.md` §4.2/§4.3 + `harness-architecture.md` §3 — 시퀀스 / 핸드오프 매트릭스 출처
