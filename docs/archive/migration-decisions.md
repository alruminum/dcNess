# Migration Decisions — RWHarness → dcNess

> **Status**: ACTIVE
> **Origin**: `docs/status-json-mutate-pattern.md` §11.2 framework 적용
> **Bootstrap**: DCN-CHG-20260429-05
> **Scope**: RWHarness 의 어느 모듈을 dcNess 로 가져올지 / 폐기할지 / 리팩터할지 module-level 결정 기록

## 0. 목적

`status-json-mutate-pattern.md` §11.2 framework 를 RWHarness 모듈 카탈로그에 적용한 결과를 단일 문서로 박는다. 모듈마다 다음 3 질문 중 하나로 분류:

1. **Catastrophic-prevention 인가?** — 돌이킬 수 없는 사고를 막는가? → **PRESERVE**
2. **발상 변경으로 자연 폐기되는가?** — Prose-Only Pattern / dcNess 메인 직접 작업 모드 적용 시 의미 잃는가? → **DISCARD**
3. **단순화 가능한가?** — 룰 누적·중복 패턴인가? → **REFACTOR**

본 문서는 **결정 기록** 이지 *재작성 금지의 헌법* 이 아니다. 분류가 잘못된 것으로 판명되면 별도 Task-ID 로 정정.

---

## 1. dcNess 정체성 정합 (분류 전 전제)

dcNess 는 RWHarness 와 다른 *모드* 다. 분류 전 다음 전제 박는다 (proposal §10 / §11.4):

- **메인 Claude 직접 작업 모드** — architect/validator/engineer 위임 강제 *없음*
- **RWHarness 가드 미적용** — agent-boundary / commit-gate hook 자체가 본 환경엔 동작 안 함 (사용자 프로젝트 가드 ≠ 본 저장소 가드)
- **Document Sync 거버넌스만 강제** — Task-ID + record/rationale/PROGRESS 동반
- **Plugin 배포 고려** (`DCN-CHG-20260429-04`) — RWHarness 와 공존 가능 설계

따라서 RWHarness 의 *위임 사이클 강제* 모듈군은 dcNess 환경에선 **자연 폐기** (proposal §11.4).

---

## 2. 분류 결과

> 출처: `~/project/RWHarness` (alruminum/realworld-harness@0.1.0-alpha)
> 본 분류는 *현 시점 결정*. RWHarness 가 변하면 본 표도 갱신 필요.

### 2.1 `harness/` (Python 코어)

| 모듈 | 결정 | 사유 |
|---|---|---|
| `core.py:551-680` `MARKER_ALIASES` + `parse_marker` + `diagnose_marker_miss` | **DISCARD** | 발상 변경으로 자연 폐기. `signal_io.interpret_signal` 이 대체. proposal §3 |
| `core.py:2040-2200` `generate_handoff` + `write_handoff` | **DISCARD** | prose 자체가 handoff. 별도 형식 없음. proposal §4.3 / §3 (Handoff) |
| `core.py:175-210` `class Flag` (enum) | **DISCARD** | 형식 강제의 한 형태 (boolean flag). proposal §1·§4.4 — recovery state 는 별도 카운터 (`.attempts.json`) 로 분리 |
| `core.py:1024-1043` `_AGENT_DISALLOWED` 매트릭스 | **DISCARD (dcNess 한정)** | `agent_call` subprocess 의 일부. dcNess 메인 직접 작업 모드엔 의미 없음 |
| `core.py` `agent_call` subprocess (claude CLI 격리) | **DISCARD (dcNess 한정)** | 메인 직접 작업 모드라 subagent 호출은 메인 Claude 의 `Agent` 도구 또는 `Task` 도구가 담당. RWHarness 의 별도 subprocess 격리는 ceremony |
| `core.py` `RunLogger` (JSONL 이벤트 로그) | **PRESERVE (검토)** | 도그푸딩 측정에 유용. dcNess 가 도그푸딩 환경 도입 시 같은 형식 채택. 단 Phase 1 진입 전엔 *보류* (불필요한 LOC) |
| `core.py` `StateDir` (path 추상) | **PARTIAL** | path 추상은 `signal_io.py` 에 이미 흡수. RWHarness `StateDir` 자체는 폐기, 신규 `signal_io.signal_path` 가 대체 |
| `core.py` `kill_check` / `HARNESS_KILL` | **PRESERVE (검토)** | 무한 루프 차단 catastrophic-prevention. 단 dcNess 가 subprocess 루프 안 돌리면 의미 없음. 후속 Task 검토 |
| `executor.py` (agent subprocess executor) | **DISCARD (dcNess 한정)** | `agent_call` 폐기와 동반 |
| `path_resolver.py` (claude CLI 경로 결정) | **DISCARD (dcNess 한정)** | 메인 작업 모드엔 메인 Claude 가 자기 CLI 안에서 동작 → 외부 CLI path 결정 불필요 |
| `providers.py` (provider config) | **DISCARD (dcNess 한정)** | 위 동일 |
| `config.py` `HarnessConfig` | **DISCARD (dcNess 한정)** | 위 동일. dcNess 는 환경변수 + plugin manifest 로 충분 |
| `notify.py` (알림 send) | **DISCARD (dcNess 한정)** | 메인 작업 모드라 사용자가 직접 인지 |
| `tracker.py` (Issue tracker integration) | **DISCARD (dcNess 한정)** | 본 저장소 거버넌스가 GitHub Issue 직접 사용 (`gh` CLI) — 별도 추상 불필요 |
| `helpers.py` (utility) | **검토** | 일부 함수 (`format_ref` 등) 는 유용. 필요 시 cherry-pick |
| `impl_loop.py` (validator → engineer → pr-reviewer 시퀀스) | **DISCARD (dcNess 한정)** | proposal §11.4 — "impl_loop subprocess 시퀀스 강제" 도입 안 함 |
| `impl_router.py` (모드 분기) | **DISCARD (dcNess 한정)** | impl_loop 동반 폐기 |
| `plan_loop.py` (checkpoint hash + planning 시퀀스) | **DISCARD (dcNess 한정)** | 위 동일 |
| `review_agent.py` (review 분기) | **DISCARD (dcNess 한정)** | 위 동일 |

### 2.2 `hooks/` (Claude Code hook)

| 모듈 | 결정 | 사유 |
|---|---|---|
| `agent-boundary.py` (ALLOW_MATRIX / READ_DENY_MATRIX / HARNESS_INFRA_PATTERNS) | **DISCARD (dcNess 한정)** | proposal §11.4 — "가드 자체가 신규 프로젝트엔 미적용". 본 저장소가 다른 사용자 프로젝트의 가드가 되려면 *plugin 배포* 후 사용자 프로젝트에서 활성화. 현재 dcNess 자체 작업 시엔 미적용 |
| `commit-gate.py` (Gate 1/4/5) | **DISCARD (dcNess 한정)** | 위 동일. 본 저장소는 git pre-commit + Claude Code PreToolUse hook (이미 도입) 으로 충분 |
| `plugin-write-guard.py` (plugin 디렉토리 보호) | **PRESERVE (전역)** | 전역 hook (~/.claude). dcNess 자체는 영향 안 줌. RWHarness 와 공존 시 동시 활성. 본 저장소가 *복사* 할 필요 없음 |
| `harness-session-start.py` (session bootstrap) | **DISCARD (dcNess 한정)** | RWHarness 활성 화이트리스트 검사 — dcNess 자체엔 무관 |
| `skill-stop-protect.py` (skill stop 차단) | **PRESERVE (전역)** | 전역 hook. 동일 |
| `harness_common.py` (hook utility) | **DISCARD (dcNess 한정)** | RWHarness hook 들의 공통 utility. dcNess hook 미도입이라 불필요 |
| `session_state.py` (live.json SSOT) | **DISCARD (dcNess 한정)** | 위 동일 |
| 기타 review/router/drift hook | **DISCARD (dcNess 한정)** | 위 동일 |

> **요약**: dcNess 는 *자체 hook 없음*. RWHarness 의 hook 은 *사용자 프로젝트* 보호용으로, dcNess 가 plugin 으로 배포돼 다른 프로젝트에 활성화될 때 의미가 있음. 본 저장소 `hooks/` 디렉토리는 만들지 않는다 (proposal §11.4 정합).

### 2.3 `agents/` (agent prompt + 모드 sub-doc)

| 모듈 | 결정 | 사유 |
|---|---|---|
| `validator.md` + `validator/*.md` (5 모드) | **REFACTOR (Phase 1) ✅** | `DCN-CHG-20260429-13` — prose writing guide 형식. 결론 + 이유만 가이드, 형식 강제 0 (proposal §3) |
| `architect.md` + `architect/*.md` (7 모드) | **REFACTOR (Phase 2)** | 동일 prose writing guide 적용 |
| `engineer.md` | **REFACTOR (Phase 2)** | 동일 |
| `designer.md` + `designer/*.md` (4 모드) | **REFACTOR (Phase 2)** | 동일 |
| `design-critic.md` | **REFACTOR (Phase 2)** | 동일 |
| `qa.md` | **REFACTOR (Phase 2)** | 동일 |
| `ux-architect.md` | **REFACTOR (Phase 2)** | 동일 |
| `product-planner.md` | **REFACTOR (Phase 2)** | 동일 |
| `plan-reviewer.md` | **REFACTOR (Phase 2)** | 동일 |
| `pr-reviewer.md` | **REFACTOR (Phase 2)** | 동일 |
| `security-reviewer.md` | **REFACTOR (Phase 2)** | 동일 |
| `test-engineer.md` | **REFACTOR (Phase 2)** | 동일 |
| `preamble.md` (자동 주입 헤더) | **DISCARD** | 점진 공개로 대체 (proposal §5 Phase 1.3 / Phase 2). dcNess 가 plugin 으로 배포될 때도 동일 |

> **dcNess 메인 작업 모드 vs Plugin 배포 모드**:
> - **메인 작업 모드 (본 저장소 내부)**: agent prompt 가 *자료* 일 뿐 의무 호출 없음. 메인 Claude 가 `Task` 도구로 호출 시에만 활성화.
> - **Plugin 배포 모드 (사용자 프로젝트에서 활성화)**: agent prompt 가 *실 호출 대상*. prose 자유 emit + 메타 LLM 해석 (형식 강제 X).
>
> 두 모드 다 같은 agent docs 형식 사용 → 변환은 한 번만.

### 2.4 `agent-config/` (프로젝트별 agent 컨텍스트)

| 모듈 | 결정 | 사유 |
|---|---|---|
| `agent-config/*.md` (project context) | **DISCARD** | proposal §5 Phase 1: "별 layer 폐기, agents/*.md 통합". dcNess 에 도입 안 함 |

### 2.5 `scripts/` (build/test/governance)

| 모듈 | 결정 | 사유 |
|---|---|---|
| RWHarness `setup-harness.sh` / `setup-agents.sh` | **DISCARD (dcNess 한정)** | RWHarness 부트스트랩 — dcNess 는 이미 거버넌스 부트스트랩 완료 (`DCN-CHG-20260429-01`) |
| RWHarness 기타 운영 script | **검토** | cherry-pick 후보. 필요 시 별도 Task |

### 2.6 `orchestration/` (changelog + rationale)

| 모듈 | 결정 | 사유 |
|---|---|---|
| `orchestration/changelog.md` 형식 + Task-ID 패턴 | **PRESERVE → 이미 흡수** | dcNess 의 `docs/process/document_update_record.md` + `change_rationale_history.md` 가 동일 역할. Task-ID 형식 (`DCN-CHG-YYYYMMDD-NN`) 도 RWHarness `HARNESS-CHG-*` 패턴 정합 |
| Document-Exception 토큰 룰 | **PRESERVE → 이미 흡수** | governance §2.4 |

### 2.7 `.claude-plugin/` (plugin manifest)

| 모듈 | 결정 | 사유 |
|---|---|---|
| `plugin.json` + `marketplace.json` 형식 | **PRESERVE → 이미 흡수** | dcNess 는 자체 manifest (`name=dcness`) 작성 (`DCN-CHG-20260429-04`). RWHarness 와 plugin name 충돌 0 |

---

## 3. 신규 net-new (RWHarness 에 없음)

| 모듈 | 상태 | 위치 |
|---|---|---|
| `harness/state_io.py` (status JSON schema) | **DISCARDED** | `DCN-CHG-20260429-03` 도입 → `DCN-CHG-20260429-13` 폐기 (proposal 갱신: 형식 강제 = 사다리) |
| `tests/test_state_io.py` (32 케이스) | **DISCARDED** | 위 동일 |
| `tests/test_validator_schemas.py` (9 round-trip) | **DISCARDED** | 위 동일 |
| `harness/signal_io.py` (prose I/O + interpret_signal + DI swap) | **DONE** | `DCN-CHG-20260429-13` |
| `tests/test_signal_io.py` (29 케이스) | **DONE** | 위 동일 |
| `agents/validator*.md` prose writing guide | **DONE** | 위 동일 |
| `.github/workflows/document-sync.yml` (CI 게이트) | **DONE** | `DCN-CHG-20260429-08` |
| `.github/workflows/python-tests.yml` | **DONE** | `DCN-CHG-20260429-09` |
| `.github/workflows/plugin-manifest.yml` | **DONE** | `DCN-CHG-20260429-10` |
| 메타 LLM (haiku) interpreter 통합 | **DISCARDED** | `DCN-CHG-20260430-04` — heuristic-only 정착, LLM fallback 폐기 (도그푸딩 호환 + Anthropic 의존 0 + 메인 Claude 자체 LLM 이라 별도 judge 불필요). `harness/llm_interpreter.py` 삭제. |

---

## 4. 보류 / 미정 (decision pending)

다음 항목은 *후속 Task* 에서 결정:

- **dcNess 가 메인 Claude 의 `Task` 도구로 agent 호출 시 prose 강제 여부** — 현 모드(메인 직접 작업) 에선 의무 아님. plugin 배포 후엔 heuristic-only 로 결론 enum 추출 + 메인 Claude 가 ambiguous 시 cascade.
- **`harness/core.py` 의 `RunLogger` / `kill_check` 도입 여부** — 도그푸딩 측정 또는 무한루프 차단 필요 시 cherry-pick.
- **`harness/helpers.py` 의 utility 함수 cherry-pick** — 사용 시점에 필요한 함수만 가져옴.

---

## 5. 분류 변경 절차

분류 결정이 잘못된 것으로 판명 시:

1. 별도 Task-ID 발급 (`DCN-CHG-YYYYMMDD-NN`)
2. 본 표의 해당 row 갱신
3. `change_rationale_history.md` 에 변경 사유·근거·후속 기록
4. 영향 받는 모듈 동반 작업

> 예: validator.md 변환을 시작했는데 RWHarness 의 mode sub-doc 구조가 dcNess 정체성과 맞지 않다고 판명 → REFACTOR → DISCARD + 신규 작성.

---

## 6. 참조

- `docs/status-json-mutate-pattern.md` §11.2 — framework 출처
- `docs/status-json-mutate-pattern.md` §11.4 — 도입할 것 / 도입 안 할 것 / 안전망
- `docs/status-json-mutate-pattern.md` §12 — RWHarness → 신규 Plugin 전환 절차
- `docs/process/governance.md` — Task-ID + Document Sync 룰
- `~/project/RWHarness` — 분류 대상 코드베이스

---

## 7. RWH 사다리 카탈로그 + dcness 한계 (2026-04-30)

> **출처**: 2026-04-30 RWH 에이전트 진단 + dcness 응답. self-check 메커니즘은 [`process/branch-surface-tracking.md`](process/branch-surface-tracking.md) 참조.

### 7.1 RWH 가 누적 patch 한 사다리 3종

RWH 깃 로그 (3일 / 82 commit / [1.1]~[46.1]) 분석:

#### 사다리 #1 — 형식 (alias) 사다리

- **패턴**: 형식 강제 → LLM 변형 발생 → alias 추가 흡수 → 새 변형 → ...
- **RWH 사례**: `MARKER_ALIASES ×12`, `parse_marker alias map`, bare LGTM alias, plan-reviewer 마커 alias 보강.
- **dcness 차단**: `prose-only + 메타 LLM 의미 해석` 발상으로 발생 자리 제거. alias #13 부재가 정조준 타격 증거.
- **후속 hole 가능성**: **자연 부재** — dcness 가 형식 강제 도입 안 하는 한 발생 안 함.

#### 사다리 #2 — state hole 사다리

- **패턴**: 분기 추가 → 분기 안 상태 보존 의무 자리 누락 → 통과 시 상태 손실 → 사후 발견 → patch → 다음 분기 추가 시 재발.
- **RWH 사례**:
  - plan_loop checkpoint hole: PASS → ux-architect FAIL 분기에서 `(A) early exit` / `(B) full save` 둘 다 안 거침 → metadata 부재 → planner 재실행. patch 사다리: `[41.1]` `[43.1]` `[44.1]` 3 단.
  - worktree plan 파일 hole: `[14.2]` 진입 시 untracked 복사 → `[26]` 재사용 케이스 또 누락. patch 의 patch.
  - autocheck no_changes 오판 (`[34.1]`): test-only commit 분류 누락 → orphan commit 양산.
- **dcness 회피 (해결 아님)**: plan_loop / impl_loop / review_agent / impl_router 폐기 (§2.1). 분기 0 → hole 0 = 동어반복. 공학 해결 X, 운영적 절제 ⚪.
- **후속 hole 가능성**: **현재 시작 안 함, 미래 위험 인정**. by-pid 레지스트리가 첫 분기 케이스 — sweep / orphan patch 0회. dcness 가 RWH 가 다루던 복잡도 (멀티세션 + 도그푸딩 sync + 마켓플레이스 + plugin 활성화 + worktree 격리) 를 *동일 비중* 흡수하면 분기 수 RWH 수렴 → 동일 사다리 시작.

#### 사다리 #2.5 — 외부 환경 사다리 (신규 분류)

- **패턴**: 외부 시스템 (CC plugin install / marketplace 컨벤션 / OS) 미공식 동작 → 우리 폴백 / wrapper 깨짐 → patch → 외부 시스템 다른 미공식 동작 만남 → patch 의 patch.
- **RWH 사례**: PLUGIN_ROOT self-detect (file 기반 폴백) — 일부.
- **dcness 사례 (이미 진입)**:
  - DCN-CHG-41 (PYTHONPATH wrapper, slash command bash 환경 PYTHONPATH 미설정 발견)
  - DCN-CHG-42 (cache glob fallback, local marketplace add 시 `marketplaces/` 미생성 발견).
  - 3 commit / 2 단 patch.
- **layer 구분 (RWH 진단 정정 인용)**: 사다리 #2 와 형식 같지만 *layer 다름* — #2 는 dcness 자체 코드 안 분기, #2.5 는 외부 시스템과의 인터페이스. 형식 강제 정조준 타격 (#1) 도, 분기 폐기 (#2 회피) 도 둘 다 #2.5 에 무력.
- **후속 hole 가능성**: **양쪽 공통 부담**, dcness 가 더 유리하지도 불리하지도 않음.

### 7.2 dcness 의 한계 명시

RWH 에이전트의 한 줄 (인용):

> ▎ State hole 은 발상 전환으로 안 사라짐. 분기가 있는 한 자리는 있음. dcness 의 답 = 분기 자체를 줄임. 분기를 줄일 수 있는 동안만 유효한 답.

dcness 의 베팅 (2026-04-30 시점):
1. **사다리 #1 차단 = 확정** — prose-only 발상이 영구 해결.
2. **사다리 #2 회피 = 작은 표면적 유지로만 유효** — 분기 늘면 동일 사다리 진입. *측정 지속 필요*.
3. **사다리 #2.5 = 공통 부담** — 양쪽 외부 시스템 미공식 동작에 노출.

### 7.3 sticky 룰 — dcness 의 self-discipline

governance 영구 자리에 박는다:

1. **분기 늘리지 않기 = 1차 룰**. 신규 분기 / 진입경로 추가 PR 은 `process/branch-surface-tracking.md` §2 self-check 의무.
2. **사다리 임계 신호 모니터링**: 동일 모듈 hole patch 30일 3회 = warning, 5회 = critical. critical 시 spec 발상 전환 협의.
3. **layer 구분 보수적**: 사다리 #2 vs #2.5 회색지대 시 #2 분류 (더 엄격).

### 7.4 inverse fallacy 회피 — outside view 부재 양쪽 동일

RWH 에이전트 정정 인용:

> ▎ 곡선은 양쪽 다 못 그림. 측정만이 답. ... 측정 데이터가 쌓이면 그땐 진짜 곡선이 보일 거.

따라서:
- "RWH 임계 도달 / 더 이상 진화 못 함" 단정 = inverse fallacy. 양쪽 미래 곡선 측정 없이 추정 못 함.
- "dcness 가 사다리 #2 자유" 도 동일 단정 못 함. *현 시점 미진입* 만 사실.
- **측정 데이터 누적이 1차** — `branch-surface-tracking.md` 가 그 회로.
