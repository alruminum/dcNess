# Main Claude Rules — dcness 작업 시 의무 read

> **[필수 — 본 프로젝트 작업 *직전* read 의무]**
>
> 본 문서는 dcness 프로젝트에서 작업하는 메인 Claude 의 행동 룰 SSOT. SessionStart inject (DCN-30-26 / -40) 의 *backup 메커니즘* — inject 작동 0회였던 회귀 (DCN-30-40 발견) 재발 시에도 본 문서 read 로 룰 인지 보장.
>
> 글로벌 `~/.claude/CLAUDE.md` 와 *동일 레벨 강제*. `CLAUDE.md` (프로젝트) 에서 본 문서 reference — 미인지 진행 = 룰 위반.

---

## 0. 정체성 — 강제하는 것 / 강제 안 하는 것

> **🔴 대 원칙** (`docs/plugin/prose-only-principle.md` §1 / `docs/orchestration.md` §0 직접 인용):
> **harness 가 강제하는 것은 단 2가지 — (1) 작업 순서, (2) 접근 영역. 그 외 모두 agent 자율.**

- **작업 순서** = 시퀀스 (validator → engineer → pr-reviewer 등) + retry 정책
- **접근 영역** = file path 경계 (agent-boundary ALLOW / READ_DENY) + 외부 시스템 mutation 차단 (push, gh issue, plugin 디렉토리)
- **출력 형식 / handoff 형식 / preamble 구조 / marker / status JSON / Flag / 모든 형식적 강제 = agent 자율**. harness 가 강제하지 않는다.

dcness SSOT (orchestration / handoff-matrix / loop-procedure / skill-guidelines / self-guidelines / 본 문서) 는 위 2개 강제 영역만 정의. 형식 강제 (마커 / status JSON / Flag) 는 `docs/plugin/prose-only-principle.md` 에 의해 폐기 — 본 문서 안에서도 그 어휘는 사용하지 않는다.

### 적용 — 메인 Claude 의 자율 보존 책임

새 룰 / 메커니즘 도입 시 본 원칙 self-check:
- 작업 순서 또는 접근 영역 강제? → 정합 ✓
- 출력 형식 / preamble / marker 강제? → **자율 침해**, 재설계
- agent 가 자율 판단할 영역에 mechanical 강제? → 트레이드오프 명시 + 사용자 승인 후만

본 룰 위반 사례 — DCN-30-34 의 "## 자가 검증" 단일 anchor 형식 강제. 이후 DCN-30-38 에서 anchor 자율화로 정정 (substance 의무 / 형식 자율).

---

## 1. 실존 검증 강제 (제1룰)

> 출처: 글로벌 `~/.claude/CLAUDE.md` "🔴 제1 룰 — 제안 전 *실존 검증* 절대 강제". 본 절은 dcness 컨텍스트 재인용 + dcness §12 self-verify 원칙 (DCN-30-35) 통합.

### 룰 (MUST)

어떤 제안·계획·솔루션을 유저에게 내놓기 *전*, 추측하거나 기억에 의존하지 않고 거기 등장하는 모든 다음 항목을 **실제로 검증한 뒤 제안한다**:

- **CLI 플래그·옵션** (`--xxx`) — `<cli> --help` 또는 직접 실행해서 존재 확인
- **API 엔드포인트·필드** — 공식 문서 / SDK / 실측 호출로 확인
- **함수·클래스·모듈** — `grep` / `Glob` 로 코드에 실재하는지 확인
- **파일 경로** — `Read` / `ls` 실존 확인
- **환경변수·설정 키** — 실제 set 되는 위치 확인
- **라이브러리·도구 의존성** — 설치/사용 가능성 확인
- **테스트 / 빌드 결과** — 명령 실행 후 인용 (특히 *CI 통과 여부*)
- **파일 변경 결과** — Bash `sed -i` / `awk -i` 후 *전·후* 실측 (`git diff --stat` / 결과 grep)
- **자기 박은 메커니즘 작동 여부** — hook / inject / 자동화 도입 시 *실 작동 검증 후* 후속 PR 진행 (DCN-30-40 회귀 회고)

### 금지

- "아마 있을 거야", "보통 그렇게 동작해", "공식적으로 지원할 거야" 같은 **추측 기반 제안**
- 한 번 실측한 결과를 *시간 경과 후 재 단언* (예: "earlier tests passed" — 현재 시점 재검증 필요)
- 자기가 박은 룰 / 메커니즘이 *실 작동* 한다는 가정 하에 후속 작업 진행 (DCN-30-40 — SessionStart inject 작동 검증 없이 5+ PR 진행 → 가정 거짓 입증)
- "flaky 무관" 같은 추측 기반 fail dismissal — 실 원인 분석 후 단언

### 적용 시점

모든 user-facing 제안 / commit / PR 의 *제출 직전*. "이렇게 하면 어떨까요" 단계가 아닌 "이렇게 합니다" / "이게 답입니다" 단계엔 **검증 100% 완료 상태**.

### Why

추측 기반 제안 후 "실제론 없어요" 발견 → 같은 자리 재작업 + 유저 frustration. 제안 *전* 30초 검증이 사후 1시간 회복보다 압도적으로 싸다. dcness 자체에서 발견한 회귀 (I5 메인 sed misdiagnosis "130개 fix" → 실제 0개 / DCN-30-40 inject 0회) 가 본 룰 정직 적용 시 회피 가능했음.

### 안티패턴 (실측 사례)

❌ "벌써 30개 파일 변환됐을 것" — 실측 안 함 → 잘못된 숫자
❌ "보통 jest config 는 X 키 쓰니까" — 학습 데이터 의존 → hallucination (예: `setupFilesAfterFramework`)
❌ "이 함수 (대략) 어디 있을 것" — grep 안 함 → 잘못된 경로
❌ engineer 보고 즉시 신뢰 → 실측 안 함 (engineer.md § 자가 검증 echo 와 짝)
❌ Bash `sed -i` / `awk -i` / 광역 변환 후 *전·후* 실측 누락 — 메인이 sed 직후 "X개 fix" 단언 = I5 회귀 (DCN-30-37 `MAIN_SED_MISDIAGNOSIS` 자동 검출)
❌ 자기 박은 SessionStart inject 작동 가정 → 실측 검증 없이 후속 PR 진행 (DCN-30-26 → DCN-30-40 회귀, 5+ PR 의존성 깨짐)
❌ CI 결과 확인 안 함 → "local PASS" 만으로 머지 (DCN-30-40 후속 발견 — 7+ PR 동안 CI fail 누적)

---

## 2. dcness 인프라 — 메인 Claude 도 알아야 할 내용

### 2.1 행동지침 md 300줄 cap (DCN-30-30)

> 출처: `docs/internal/self-guidelines.md` §1.

dcness 행동지침 문서 (메인 Claude 또는 sub-agent 가 의사결정 시 *직접 read* 하는 md) 는 **파일당 300줄 cap**. 초과 시 책임 분리 축으로 split.

**대상**: skill prompt (`commands/*.md`) / agent prompt (`agents/**/*.md`) / SSOT (`docs/loop-procedure.md` / `docs/handoff-matrix.md` / `docs/orchestration.md`) / `docs/plugin/skill-guidelines.md` / `docs/internal/self-guidelines.md` / 본 문서.

**대상 외**: 역사 로그 (`document_update_record.md` / `change_rationale_history.md`) / `PROGRESS.md` / spec / proposals / 코드.

**Why**: 메인 Claude / sub-agent 가 매 결정 시 read → 토큰 누적 + thinking 시간 ↑. 300줄 = 한 read 임계.

**현재 cap 충족 상태** (사용자 verification 의무 — `wc -l` 실측):
| 파일 | 줄 수 (작성 시점) | cap |
|---|---|---|
| `docs/orchestration.md` | 464 | **500** (DCN-CHG-20260505-03 — loop-catalog 흡수 통합. 다른 SSOT 는 300 유지) |
| `docs/handoff-matrix.md` | 256 | 300 |
| `docs/loop-procedure.md` | 240 | 300 |
| `docs/plugin/skill-guidelines.md` | 232 | 300 |
| `docs/internal/self-guidelines.md` | 51 | 300 |

### 2.2 4 SSOT 위치 + 책임 축

| 파일 | 책임 | 메인 read 시점 |
|---|---|---|
| [`docs/orchestration.md`](../orchestration.md) | 시퀀스 mini-graph + **8 loop 행별 풀스펙** (entry / task_list / advance / clean_enum / branch_prefix / Step 별 allowed_enums / 분기 / sub_cycles) | 신규 작업 시 진입 경로 결정 + loop 진입 시 풀스펙 read |
| [`docs/handoff-matrix.md`](../handoff-matrix.md) | agent 측 강제 영역 (결정표 / Retry / Escalate / 접근 권한) | agent 호출 분기 / 한도 결정 시 |
| [`docs/loop-procedure.md`](../loop-procedure.md) | Step 0~8 mechanics (worktree → begin-run → TaskCreate → begin-step → Agent → end-step → finalize-run --auto-review) | 매 컨베이어 진행 |
| [`docs/plugin/skill-guidelines.md`](../plugin/skill-guidelines.md) | cross-cutting 룰 (echo / Step 기록 / yolo / AMBIGUOUS / worktree / 결과 출력 / 권한 요청 / Karpathy 참조 / **§10 self-verify 원칙**) | 모든 dcness skill 진행 시 |
| [`docs/internal/self-guidelines.md`](../internal/self-guidelines.md) | dcness self 협업 룰 (300줄 cap / §2 self-verify) | dcness 자체 작업 시 |

### 2.3 거버넌스

> 출처: `docs/internal/governance.md` (전체 룰).

- **Task-ID**: `DCN-CHG-YYYYMMDD-NN` (오늘 = `DCN-CHG-20260501-NN`)
- **Change-Type 7종**: `spec` / `agent` / `harness` / `hooks` / `ci` / `test` / `docs-only` (복수 가능, governance §2.2)
- **commit 절차**: branch → PR → squash merge. main 직접 push 금지. branch 는 merge 후에도 삭제하지 않음.
- **doc-sync gate**: `node scripts/check_document_sync.mjs` 통과 필수 — git pre-commit hook + Claude Code PreToolUse hook 동시 차단. `--no-verify` 등 우회 금지.
- **동반 갱신** (governance §2.6):
  - `docs/internal/document_update_record.md` (모든 변경 — WHAT)
  - `docs/internal/change_rationale_history.md` (spec / agent / harness / hooks / ci 변경 시 — WHY)
  - `PROGRESS.md` (harness / hooks / ci 변경 시)

### 2.4 핵심 강제 룰 — 매 작업 의무

> 출처: SessionStart inject directive (`hooks/session-start.sh`, DCN-30-40).

1. **매 Agent 호출 후 prose 5~12줄 의무 echo** (가시성 §1, skill-guidelines.md)
2. **begin-step / end-step 1:1 의무** (Step 기록 §2)
3. **추측 금지 + 실측 후 단언** (skill-guidelines.md §10 / self-guidelines.md §2 / 본 문서 §1 정합)
4. **finalize-run 시 `--auto-review` flag 의무** (loop-procedure §5.1)

### 2.5 sub-agent path 보호 (DCN-CHG-20260501-01)

> 출처: `harness/agent_boundary.py` + `hooks/file-guard.sh` + handoff-matrix §4.4.

PreToolUse 훅 `Edit|Write|Read|Bash` matcher 등록 — sub-agent 가 dcness 인프라 path (orchestration.md / handoff-matrix.md / loop-procedure.md / skill-guidelines.md / self-guidelines.md / hooks/ / harness/ 등) 변경 시도 시 차단. `agent_id` payload 로 메인 vs sub 구분 — 메인은 통과 (거버넌스 책임).

`is_infra_project()` 4 OR 신호로 dcness 자체 저장소 작업 시 해제 — 메인이 SSOT 편집 가능.

---

## 3. Karpathy 4 원칙 (전문)

> 출처: [Andrej Karpathy LLM coding pitfalls](https://x.com/karpathy/status/2015883857489522876).
> 마스터 인용: [andrej-karpathy-skills/skills/karpathy-guidelines/SKILL.md](https://github.com/forrestchang/andrej-karpathy-skills/blob/main/skills/karpathy-guidelines/SKILL.md) (MIT).
> dcness 적용: agent 별 분배 박힘 (DCN-30-17, `agents/*.md` 참조).

**Tradeoff**: 본 룰은 caution > speed. trivial 작업엔 judgment.

### 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them — don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

### 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

### 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it — don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

### 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

### dcness 적용 매핑

| 원칙 | 주 적용 agent | 보조 적용 |
|---|---|---|
| 1. Think Before | `product-planner`, `qa`, `test-engineer` | 전 agent |
| 2. Simplicity First | `architect`, `engineer` | `designer` |
| 3. Surgical Changes | `engineer`, `pr-reviewer` | — |
| 4. Goal-Driven Execution | `test-engineer`, `validator` | `qa`, `architect` |

각 agent prompt 안 customized 적용은 `agents/*.md §Karpathy 원칙` 참조.

---

## 4. 참조

- 글로벌: `~/.claude/CLAUDE.md` (제1룰 + 새 프로젝트 흐름 + 모듈 단위 작업 순서 + 커밋 절차)
- 프로젝트: `CLAUDE.md` (dcness 정체성 + 거버넌스 핵심 + 문서 지도)
- SSOT 4종 (DCN-CHG-20260505-03 후): `docs/plugin/orchestration.md` / `docs/plugin/handoff-matrix.md` / `docs/plugin/loop-procedure.md` / `docs/plugin/skill-guidelines.md` (+ `docs/internal/self-guidelines.md`)
- 거버넌스: `docs/internal/governance.md`
- 카탈로그: `docs/plugin/known-hallucinations.md` (외부 도구 hallucination 누적)
