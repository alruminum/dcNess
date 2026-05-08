# Handoff Matrix — Agent Routing 가이드 / Retry / Escalate / 권한

> **Status**: ACTIVE
> **Scope**: dcness 컨베이어의 *agent 측 강제 영역* SSOT — agent 결론 prose 를 보고 메인 Claude 가 다음 단계 결정할 때 참조하는 자연어 routing 가이드 / retry 한도 / escalate 카탈로그 / 접근 권한.
> **Cross-ref**: 시퀀스 spec + 8 loop 행별 풀스펙 = [`orchestration.md`](orchestration.md) §2~§4. 절차 mechanics = [`loop-procedure.md`](loop-procedure.md).

---

## 1. Agent 결론 → 다음 agent 결정 가이드 (자연어)

> agent 13 종 (validator / architect 는 mode 펼침). agent 가 자기 prose 에 결론 + 권장 다음 단계를 자유롭게 박는다. 메인 Claude 는 그 prose 와 본 가이드를 비교해 다음 호출을 결정한다. 본 가이드는 형식 강제가 아니라 *판단 보조*. 가능한 결론 표현은 agent 별로 다양 — 의미만 맞으면 OK ([`dcness-rules.md`](dcness-rules.md) §1 원칙 2 자율 정합).

> **이슈 #280 정착 후 작동 모델**:
> - agent 는 prose 마지막 단락에 *어떤 결과로 끝났는지 + 메인이 누구를 부르는 게 적절한지* 자기 언어로 명시.
> - 메인은 prose + 본 §1 가이드만으로 routing 결정. enum 형식 검증 없음.
> - prose 가 모호하거나 결론을 추출 못 하면 메인이 사용자에게 위임 (cascade — `harness/routing_telemetry.py:record_cascade`).

### 1.1 product-planner

PRD 작성 / 변경 / 동기화 hub. 일반적으로 다음 4 결과 중 하나로 종료:

- **PRD 신규 또는 변경안 준비 완료** → plan-reviewer 호출 (변경분만이면 review 도 변경분 한정).
- **사용자 입력이 모호해 추가 질문 필요** → 사용자에게 역질문하고 응답 대기 (자동 진행 금지).
- **변경된 PRD 가 UX 영향** → ux-architect 로 변경 반영.
- **issue tracker 동기화 완료** → 후속 단계 없음.

### 1.2 plan-reviewer

PRD 심사. 두 가지 결과:

- **PRD 승인** → 다음 단계는 ux-architect (UX_FLOW).
- **PRD 변경 요청** → product-planner 재진입.

### 1.3 ux-architect

UX Flow 정의 / 변경 / refine. 다음 4 결과:

- **UX Flow 신규 완성 / 변경분 patch 완료** → validator UX_VALIDATION.
- **UI refine 완료 (기존 디자인 다듬기)** → 사용자 승인 후 designer SCREEN.
- **Flow 정의 불가 (PRD 모순 등)** → escalate (사용자 위임).

### 1.4 architect (6 mode hub)

mode 별 처리 흐름:

- **SYSTEM_DESIGN / TECH_EPIC** — 시스템 설계 산출 (`## impl 목차` 표 포함). 완료 시 validator DESIGN_VALIDATION.
- **MODULE_PLAN** — impl 파일 detail 작성. 다음 단계는 컨텍스트:
  - feature-build-loop 안 = impl 목차 다음 행 있으면 MODULE_PLAN 재호출, 마지막 행이면 loop 종료 → impl-task-loop 진입.
  - impl-task-loop fallback = test-engineer.
  - SPEC GAP 발견 시 architect SPEC_GAP, 기술 제약 충돌 시 escalate.
- **SPEC_GAP** — gap 해소 시 engineer 재진입. PRD 변경 필요면 product-planner. 기술 제약 충돌이면 escalate.
- **LIGHT_PLAN** — 가벼운 plan 완료 시 engineer (simple).
- **DOCS_SYNC** — 문서 정합 동기화 완료 시 후속 없음. SPEC GAP 발견 시 architect SPEC_GAP, 기술 제약 충돌 시 escalate.

> Note: 옛 TASK_DECOMPOSE mode 폐기 (issue #247). 가치 4 자리 (Story → impl 매핑 / NN-slug 명명 / 의존 순서 / outline) 는 SYSTEM_DESIGN 의 `## impl 목차` 표로 흡수. impl 파일 본문 detail 은 MODULE_PLAN × N 가 채움.

### 1.5 engineer

구현 hub. 결과 종류:

- **구현 완료 (기능 검증 가능)** → validator CODE_VALIDATION.
- **부분 구현 (분량 초과로 split 필요)** → engineer 재호출 (split 한도 3, 새 context window — DCN-30-34).
- **SPEC GAP 발견 (스펙 모호 / 부족)** → architect SPEC_GAP (attempt < 2). 한도 초과면 escalate.
- **테스트 실패 (재구현 필요)** → engineer 재시도 (attempt < 3). 한도 초과면 escalate.
- **POLISH 단계 마무리** → pr-reviewer 재호출.
- **escalate** (구현 불가 / 한도 초과) → 사용자 위임.

### 1.6 test-engineer

테스트 코드 선작성 (TDD). 결과:

- **테스트 준비 완료** → engineer (attempt 0 진입).
- **스펙 부족해 테스트 작성 불가** → architect SPEC_GAP.

### 1.7 designer

UI variant 생성. 결과:

- **variant 준비 완료** → THREE_WAY 면 design-critic, ONE_WAY 면 사용자 PICK.
- **variant 생성 불가** → escalate (사용자 위임).

### 1.8 design-critic

variant 심사. 결과:

- **1+ variant 승인** → 사용자 PICK → 다음 단계 (test 또는 impl).
- **모두 reject** → designer 재진입 (round < 3).
- **3 round 누적 reject** → ux-architect UX_REFINE.

### 1.9 validator (4 mode)

검증 전담. mode 별:

- **CODE_VALIDATION** — PASS 시 pr-reviewer. FAIL 시 engineer 재시도 (attempt < 3). 스펙 부족 시 architect SPEC_GAP.
- **DESIGN_VALIDATION** — 승인 시 architect MODULE_PLAN × N (impl 목차 첫 행부터 순차). FAIL 시 architect SYSTEM_DESIGN 재진입 (cycle 한도 2). escalate 시 사용자 위임.
- **UX_VALIDATION** — PASS 시 architect SYSTEM_DESIGN. FAIL 시 ux-architect 재진입.
- **BUGFIX_VALIDATION** — PASS 시 pr-reviewer. FAIL 시 engineer 재시도.

> Note: 옛 PLAN_VALIDATION mode 폐기 (issue #247). 컨베이어 동작은 `orchestration.md §4.3 task_list` 기준이고, 그 task_list 에 PLAN_VALIDATION step 이 *원래부터* 빠져있어서 (drift) 사실상 default-skip 중이었음. spec / 동작 정합 회복.

### 1.10 pr-reviewer

merge 직전 코드 품질 심사:

- **LGTM** → CI PASS 후 메인이 즉시 regular merge.
- **변경 요청** → engineer POLISH 재호출.

### 1.11 qa

이슈 분류 hub. 5 결과:

- **기능 버그** → architect LIGHT_PLAN.
- **간단 cleanup** → engineer 직접 (light).
- **디자인 이슈** → designer 또는 ux-architect (REFINE).
- **알려진 이슈** → 후속 없음.
- **분류 불가 (escalate)** → 사용자 위임.

### 1.12 security-reviewer

보안 감사. 두 결과:

- **취약점 없음** → 후속 없음 (검증 완료).
- **취약점 발견** → engineer 수정 요청.

---

## 2. Retry 한도

> RWHarness `harness-architecture.md` §4.3 핵심 상수 + impl_loop 정책 정합. dcNess 는 boolean Flag 대신 `.claude/harness-state/<run_id>/.attempts.json` 카운터로 표현.

| 항목 | 한도 | 초과 시 |
|---|---|---|
| engineer attempt (TESTS_FAIL → 재시도) | 3 | `IMPLEMENTATION_ESCALATE` |
| engineer split (IMPL_PARTIAL → 재호출, DCN-30-34) | 3 | `IMPLEMENTATION_ESCALATE` (작업 분해 부족 — architect SYSTEM_DESIGN 재진입 권고 / impl 목차 분할 재검토) |
| engineer SPEC_GAP_FOUND → architect.spec-gap → engineer 재진입 | 2 | `IMPLEMENTATION_ESCALATE` |
| validator FAIL → 직전 agent 재진입 | (validator 종속) | 직전 agent 의 retry 한도에 흡수 |
| design THREE_WAY VARIANTS_ALL_REJECTED 라운드 | 3 | `UX_REDESIGN_SHORTLIST` (ux-architect REFINE) |
| pr-reviewer CHANGES_REQUESTED → POLISH 라운드 | 2 | 사용자 escalate |
| product-planner CLARITY_INSUFFICIENT 라운드 | 무제한 (사용자 응답 대기) | (해당 없음) |
| ESCALATE 누적 (동일 fail_type) | 2 | architect SPEC_GAP 자동 호출 |

`.attempts.json` 형식 (예시):
```json
{
  "code_validation": 2,
  "spec_gap": 1,
  "design_round": 0
}
```

force-retry 시 카운터 리셋 (RWHarness PR #11 패턴 정합).

---

## 3. Escalate 조건 카탈로그

다음 결론 enum 수신 시 **메인 Claude / driver 가 즉시 사용자 보고 후 대기** ([`dcness-rules.md`](dcness-rules.md) §1 §2 원칙 2 정합 — 자동 복구 금지):

| Enum | 출처 agent | 의미 |
|---|---|---|
| `IMPLEMENTATION_ESCALATE` | engineer | 재시도 한도 초과 또는 구현 불가 |
| `UX_FLOW_ESCALATE` | ux-architect | UX Flow 정의 불가 (PRD 모순 등) |
| `DESIGN_LOOP_ESCALATE` | designer | variant 생성 불가 또는 critic 3 round 후 |
| `SCOPE_ESCALATE` | qa | 이슈 범위가 분류 enum 5개 모두 해당 안 됨 |
| `PRODUCT_PLANNER_ESCALATION_NEEDED` | architect.spec-gap | PRD 변경 필요 |
| `TECH_CONSTRAINT_CONFLICT` | architect.spec-gap / docs-sync | 기술 제약 충돌 |
| `UX_REDESIGN_SHORTLIST` | design-critic | 3 round 누적 reject |
| `CLARITY_INSUFFICIENT` | product-planner | 사용자 입력 모호 (역질문 필요) |

자동 재시도 / 우회 금지. 사용자 명시 결정 후만 진행.

---

## 4. 접근 권한 매트릭스

> RWHarness `harness-architecture.md` §3 의 dcNess 변환. dcness 의 두 번째 강제 영역 = "접근 영역" ([`dcness-rules.md`](dcness-rules.md) §1 §1 정합).

### 4.1 호출 권한 (HARNESS_ONLY_AGENTS)

`HARNESS_ONLY_AGENTS = ("engineer",)` — 메인 Claude 가 Agent 도구로 직접 호출 차단. 코드 driver (impl_driver) 경유 필수.

| Agent | Mode | 직접 호출 허용 | 비고 |
|---|---|---|---|
| architect | SYSTEM_DESIGN, TECH_EPIC, LIGHT_PLAN, DOCS_SYNC | ✅ | 메인 직접 |
| architect | MODULE_PLAN, SPEC_GAP | ❌ | impl_driver / plan_driver 경유 (feature-build-loop §4.2 Step 7 의 MODULE_PLAN × N 도 컨베이어 경유) |
| validator | DESIGN_VALIDATION, UX_VALIDATION | ✅ | 메인 직접 |
| validator | CODE_VALIDATION, BUGFIX_VALIDATION | ❌ | 루프 경유 |
| 그 외 11 agent | — | ✅ | designer, ux-architect, qa, pr-reviewer, design-critic, security-reviewer, product-planner, test-engineer, plan-reviewer 모두 메인 직접 |
| engineer | — | ❌ | impl_driver 경유 필수 |

### 4.2 Write/Edit 허용 경로 (ALLOW_MATRIX)

| 에이전트 | 허용 경로 |
|---|---|
| engineer | `src/**` |
| architect | `docs/**`, `backlog.md`, `trd.md` |
| designer | `design-variants/**`, `docs/ui-spec*` |
| test-engineer | `src/__tests__/**`, `*.test.*`, `*.spec.*` |
| product-planner | `prd.md`, `stories.md` |
| ux-architect | `docs/ux-flow.md` |
| qa | (Issue tracker mutation 만, 파일 X) |
| validator / design-critic / pr-reviewer / security-reviewer / plan-reviewer | (없음 — 판정 전용) |

### 4.3 Read 금지 경로 (READ_DENY_MATRIX)

| 에이전트 | 금지 |
|---|---|
| product-planner | `src/`, `docs/impl/`, `trd.md` |
| designer | `src/` |
| test-engineer | `src/` (impl 외), 도메인 문서 |
| plan-reviewer | `src/`, `docs/impl/`, `trd.md` |

### 4.4 인프라 패턴 (전 에이전트 공통 차단)

> **코드 SSOT**: 실제 강제 패턴은 `harness/agent_boundary.py:DCNESS_INFRA_PATTERNS`. 본 §4.4 와 코드는 항상 동기 — 변경 시 양쪽 함께.

```python
DCNESS_INFRA_PATTERNS = [
    r'(^|/)\.claude/',
    r'(^|/)hooks/',
    r'(^|/)harness/(signal_io|interpret_strategy|hooks|session_state|agent_boundary)\.py$',
    r'(^|/)docs/plugin/orchestration\.md$',
    r'(^|/)docs/plugin/handoff-matrix\.md$',
    r'(^|/)docs/plugin/loop-procedure\.md$',
    r'(^|/)docs/plugin/dcness-rules\.md$',
    r'(^|/)scripts/(setup_branch_protection|analyze_metrics)\.mjs$',
]
```

> RWHarness 의 `HARNESS_INFRA_PATTERNS` 안 `r'orchestration-rules\.md'` 잔재는 dcness 가 정정 — 파일명은 `docs/plugin/orchestration.md` + `docs/plugin/handoff-matrix.md` (split 후 양쪽). loop-procedure / dcness-rules / hooks·session_state·agent_boundary 도 dcness 가 추가 보호.

인프라 프로젝트(`is_infra_project()` True) 에선 위 패턴 해제 (dcness 자체 작업 시 본 SSOT 들도 편집 가능해야 함).

### 4.5 인프라 프로젝트 판정

RWHarness 4 신호 OR 정합:

1. `DCNESS_INFRA=1` 환경변수
2. 마커 파일 `~/.claude/.dcness-infra` 존재
3. `CLAUDE_PLUGIN_ROOT` 환경변수 non-empty
4. `cwd.resolve() == Path("/Users/<user>/project/dcness")` (또는 화이트리스트 매칭)

> **코드 강제**: `harness/agent_boundary.py` 가 본 spec 의 SSOT 구현. `hooks/file-guard.sh` (PreToolUse Edit/Write/Read/Bash) + `hooks/post-agent-clear.sh` (PostToolUse Agent) 가 활성화. opt-out 마커 = `.no-dcness-guard` (cwd) — 사용자 임시 우회.

---

## 5. 참조

- [`orchestration.md`](orchestration.md) — 시퀀스 catalog (§2 게이트 + §3 진입 경로 + §4 8 loop 행별 풀스펙)
- [`loop-procedure.md`](loop-procedure.md) — Step 0~8 mechanics
- [`dcness-rules.md`](dcness-rules.md) §1 — Prose-Only 원칙 현행 SSOT (대 원칙 + Anti-Pattern 5원칙)
- [`../archive/status-json-mutate-pattern.md`](../archive/status-json-mutate-pattern.md) — Prose-Only 원전 proposal (역사 자료)
- `agents/*.md` — 각 agent 의 결론 prose 표현 가이드
- `harness/routing_telemetry.py` — prose-only routing 회귀 검증 telemetry (이슈 #281)
- `harness/signal_io.py` / `harness/interpret_strategy.py` — 옛 enum 추출 인프라 (이슈 #284 폐기 진행 중)
