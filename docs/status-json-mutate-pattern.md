# Status JSON Mutate Pattern — Marker Enforcement 발상 전환

> **Status**: PROPOSAL_DRAFT (brainstorm)
> **Origin**: 2026-04-29 jha0313/harness_framework 비교 분석 + W0 `--json-schema` PoC
> **Related**: HARNESS-CHG-20260428-09 (alias map, 폐기 후보), CHG-14 [14.1] (alias 변형 12개 추가, 정반대 방향), W0 PoC 결과
> **적용**: 신규 프로젝트 (lightharness 등) 에서 메인 Claude 직접 작업. RWHarness 자체엔 적용 안 함. §11 참조.

---

## 1. Context

### 진앙 문제
2026-04-28 jajang 도그푸딩 12 PR 중 marker fragility 카테고리 3 PR (#5, #8, #9). 매 LLM 변형 emit 마다 `MARKER_ALIASES` 사다리 확장. 가장 최근 CHG-14 [14.1] (PR #17) 이 12개 변형을 추가하며 *텍스트 파싱 사다리 강화 방향*으로 진행 중.

### 발상 경합
- **W0 검증** (`--json-schema`): API 가 schema 만족까지 자동 retry. 출력 *형식* 결정론. 단점: 위반 시 retry 비용 폭증 ($0.15→$0.29, num_turns 7→26).
- **jha0313 비교**: agent 가 status JSON 파일을 *명시 mutate*. orchestrator 는 그 파일만 read. 출력 형식이 아니라 *agent 의 mutate 행동* 을 결정론으로.

### 정체성 정렬
RWHarness 코어 (메모리 기반):
- 검증자 격리 (validator subprocess 분리)
- conditional workflow branch (FAIL → SPEC_GAP → 재검증)
- multi-turn recovery (escalate_history, force-retry)
- 책임 분리 (agent-boundary ALLOW_MATRIX)

본 proposal 은 *코어 손실 0*. 변경 영역 = **마커 enforcement 메커니즘 한정**.

---

## 2. Goal

> "agent 의 자유 텍스트를 신뢰하지 않는다. agent 에게 외부 상태 파일 mutate 책임 부여. orchestrator 는 그 파일만 read."

### 폐기 대상
- `harness/core.py:551-604` `MARKER_ALIASES` (54 LOC, 12+ alias)
- `harness/core.py:607-680` `parse_marker` (110 LOC, 1차/2차/3차 폴백 사다리)
- `harness/core.py:520+` `diagnose_marker_miss` (UNKNOWN 진단)
- `parse_marker` 호출 14 위치 (`impl_loop.py` 7, `core.py` 6, `impl_router.py` 2, `plan_loop.py` 3)
- `---MARKER:X---` 텍스트 컨벤션 (agents/*.md 의 @OUTPUT 부분 재정의)
- handoff prose (`generate_handoff` `core.py:2040`, `write_handoff` `core.py:2150`)

### 신규 도입
- `harness/state_io.py` (가칭): `write_status(agent, run_id, payload)` / `read_status(agent, run_id)` 단일 책임 모듈 (~80 LOC)
- agents/*.md 의 @OUTPUT 섹션 재정의: "결과를 `.claude/harness-state/<run>/<agent>-<mode>.json` 에 Write 도구로 작성"
- W0 schema 와 결합: `--json-schema` 도 동시 적용 → 두 결정론 백업

---

## 2.5 Anti-Patterns — 이전 함정 회피 원칙 (불변)

> **이 proposal 의 모든 Phase 가 다음 원칙 위반 시 즉시 중단 + 재설계**.

### 원칙 1: 룰이 룰을 부르는 reactive cycle 차단
- jajang 도그푸딩 12 PR cycle = "마커 변형 발견 → alias 추가 → 또 변형 → 또 alias" 반복. 본 proposal 이 이 cycle 자체를 폐기하는 것.
- **신규 룰 추가 전 기존 룰 *제거* 가능성부터 검토**. 추가 → 제거 비대칭이 부채를 만든다.

### 원칙 2: 강제 vs 권고 분리
- **강제 (deny/block)**: catastrophic-prevention 만. plugin-write-guard, agent-boundary 의 인프라 차단, src/ scope 위반 등 *돌이킬 수 없는 사고* 만.
- **권고 (warn/log)**: 그 외 모두. 컨텍스트 비대, 비용 폭증, alias hit, schema 변형 등 *측정 가능한 신호* 는 stderr 경고 + 데이터 누적만.
- 권고 → 강제 전환은 **30일 측정 데이터 + 명시적 결정 PR** 필수. 자동 승격 금지.

### 원칙 3: agent 자율성 최대화
- agent docs 의 schema `required` 키 최소화. *결정에 영향* 주는 키만 required, *진단/감사용* 은 optional.
- agent 가 *자유롭게 채울 수 있는 영역* (`non_obvious_patterns`, `next_actions[].rationale` 등) 은 schema 에서 freeform string array 로.
- "agent 가 빠뜨렸다 → required 추가" 패턴 = 함정. 빠뜨린 이유 분석 후 *prompt 명료화* 가 우선.

### 원칙 4: 흐름 강제는 최소한만
- impl_loop 의 시퀀스 강제 (validator → engineer → pr-reviewer) = 최소 흐름. 보존.
- 단, 흐름 *내부* 의 행동 룰 (e.g. "validator 는 반드시 fail_items 에 라인 번호 박아라") 은 권고. 위반 시 prose 폴백 가능.

### 원칙 5: 신규 hook 추가 전 측정
- "사고 발생 → hook 추가" 가 아니라 "사고 발생 → 패턴 카탈로그 → 30일 빈도 측정 → hook 정당화 후 추가".
- hook 추가 시 *기존 hook 중복 제거 가능 여부* 동시 검토.

### 원칙 위반 측정
각 Phase acceptance 에 다음 추가:
- [ ] 신규 required schema 키 0 (있으면 제거 정당화)
- [ ] 신규 강제 (deny) hook 0 (있으면 30일 데이터 + 결정 PR)
- [ ] 룰 순감소 추세 (Phase 별 LOC + hook 수 모니터링)

---

## 3. Mechanism

### 현재 흐름
```
agent_call("validator", prompt, out_file)
  → claude CLI subprocess
  → validator: prose 리포트 + ---MARKER:PASS--- emit
  → harness 가 stdout 캡처 → out_file.write_text(stdout)   # harness 가 쓴다
  → parse_marker(out_file, "PASS|FAIL|SPEC_MISSING")        # 정규식 파싱
     1차 ---MARKER:X--- → 2차 \bX\b → 3차 MARKER_ALIASES
  → state_dir.flag_touch(Flag.PLAN_VALIDATION_PASSED)        # boolean flag
```

### 적용 후 흐름
```
agent_call("validator", prompt + STATE_PROMPT, run_id)
  STATE_PROMPT = """
  결과를 .claude/harness-state/<run_id>/validator-<mode>.json 에 Write 도구로 작성하라.
  형식: {"status": "PASS|FAIL|SPEC_MISSING", "fail_items": [...], "save_path"?: "..."}
  미작성 시 워크플로우 즉시 중단.
  """
  → claude CLI subprocess + --json-schema (백업)
  → validator: 자유롭게 prose 후 마지막에 Write 도구로 status JSON mutate
  → harness: read_status("validator", run_id) → json.loads
  → status = result["status"]   # 파싱 0
  → 파일 없으면 즉시 error (재시도는 retry 정책에서)
```

### Prose 의 운명
**사라지지 않음**. agent 의 prose 리포트는 *진단/감사* 용으로 stdout/out_file 그대로 보존. 단 *결정 원천에서 빠짐*. validator 의 "save_path 에 진단 리포트 저장" 같은 요구는 status JSON 안에 path 필드로 명시.

---

## 4. 충돌 지점 — 상세 분석

### 4.1 disallowedTools 매트릭스 (`harness/core.py:1024-1043`)

**현재 ReadOnly agent 들이 Write 차단**:
```python
"validator":         "Agent,Bash,Write,Edit,NotebookEdit",
"pr-reviewer":       "Agent,Bash,Write,Edit,NotebookEdit",
"design-critic":     "Agent,Bash,Write,Edit,NotebookEdit",
"security-reviewer": "Agent,Bash,Write,Edit,NotebookEdit",
"plan-reviewer":     "Agent,Bash,Write,Edit,NotebookEdit",
"qa":                "Agent,Bash,Write,Edit,NotebookEdit",
```

**충돌**: status JSON mutate 는 `Write` 도구 필요. 6 agent 다 차단됨.

**해결**: `Write` 를 disallowedTools 에서 제거. 대신 hook (agent-boundary) 의 ALLOW_MATRIX 로 path 화이트리스트 강제.

```python
# 적용 후
"validator":         "Agent,Bash,Edit,NotebookEdit",
# (Write 빠짐, hook 이 path 검사)
```

**검증된 사실** (W0 PoC 부속): `--permission-mode bypassPermissions` 모드에서는 `--allowedTools` path-scope 가 의미 없고 `--disallowedTools` 만 작동. **CLI native path-scope 는 RWHarness 의 bypassPermissions 패턴과 충돌** — hook 이 유일한 해.

### 4.2 agent-boundary.py ALLOW_MATRIX (`hooks/agent-boundary.py:47-90`)

**현재 ReadOnly agent 들이 빈 list (모든 Write deny)**:
```python
"validator":         [],
"design-critic":     [],
"pr-reviewer":       [],
"qa":                [],
"security-reviewer": [],
```

**적용 후 — status JSON 경로만 화이트리스트**:
```python
"validator": [
    r'(^|/)\.claude/harness-state/[^/]+/validator-.+\.json$',
],
"pr-reviewer": [
    r'(^|/)\.claude/harness-state/[^/]+/pr-reviewer-.+\.json$',
],
"design-critic": [
    r'(^|/)\.claude/harness-state/[^/]+/design-critic-.+\.json$',
],
"qa": [
    r'(^|/)\.claude/harness-state/[^/]+/qa-.+\.json$',
],
"security-reviewer": [
    r'(^|/)\.claude/harness-state/[^/]+/security-reviewer-.+\.json$',
],
"plan-reviewer": [
    r'(^|/)\.claude/harness-state/[^/]+/plan-reviewer-.+\.json$',
],
```

**부수 효과 (긍정)**: agent A 가 agent B 의 status 파일 *덮어쓸 수 없음*. **결정론 + 보안이 단일 매트릭스로 통합**. 현재 분리되어 있음 (parse_marker 는 결정론, agent-boundary 는 보안).

**catastrophic 가드는 무영향**:
- `HARNESS_INFRA_PATTERNS` (hooks/, harness/, .claude-plugin/ 차단) — agent 가 인프라 mutate 시도해도 여전 차단
- `READ_DENY_MATRIX` (plan-reviewer 가 src/ 못 읽음 등) — Write 영역과 무관

### 4.3 `_AGENT_DISALLOWED` 의 Write-Allowed agent 들

**현재 Write 허용 agent**: `engineer`, `architect`, `designer`, `ux-architect`, `test-engineer`, `product-planner`. 이들은 status JSON 도 자기 ALLOW_MATRIX 안에 추가만 하면 됨 — 별도 disallowedTools 변경 0.

```python
# agent-boundary.py:47 ALLOW_MATRIX 에 한 줄씩 추가
"engineer": [
    r'(^|/)src/', ...,
    r'(^|/)\.claude/harness-state/[^/]+/engineer-.+\.json$',  # 신규
],
"architect": [
    r'(^|/)docs/', ...,
    r'(^|/)\.claude/harness-state/[^/]+/architect-.+\.json$',
],
# 이하 동일
```

### 4.4 핸드오프 (`generate_handoff` core.py:2040, `write_handoff` core.py:2150)

**현재**: validator → engineer 핸드오프가 prose 6KB+ 텍스트.
```python
val_content = Path(val_out).read_text()
_val_handoff = generate_handoff("validator", "engineer", val_content, impl_file, 0, str(issue_num))
write_handoff(state_dir, prefix, 0, "validator", "engineer", _val_handoff)
```

**적용 후**: validator 가 mutate 한 status JSON 안에 `next_actions[]` 필드 박음. engineer 가 그 파일 직접 read.

```python
# validator 의 status JSON
{
  "status": "FAIL",
  "fail_items": ["impl 6.2 의 retry 횟수 명세 누락", "..."],
  "next_actions": [
    {"target": "engineer", "action": "fix_spec_gap", "ref": "docs/impl/14.md#L42"},
    ...
  ],
  "spec_refs": ["docs/impl/14.md"]
}

# engineer 의 prompt
"이전 단계 status: .claude/harness-state/<run>/validator-PLAN_VALIDATION.json 을 읽고 next_actions[] 처리하라."
```

**generate_handoff / write_handoff 폐기**. 핸드오프 = *공유 상태 파일*.

### 4.5 Flag 시스템 (`harness/core.py:175-210` `class Flag`)

**현재**:
```python
class Flag(str, Enum):
    PLAN_VALIDATION_PASSED = "plan_validation_passed"
    SECURITY_REVIEW_PASSED = "security_review_passed"
    BUGFIX_VALIDATION_PASSED = "bugfix_validation_passed"
    ...
```
별도 boolean flag 파일들이 `.claude/harness-state/` 에 touch/rm 됨.

**적용 후 두 옵션**:

#### 옵션 A: Flag 시스템 보존 — status JSON read 후 derive
```python
# core.py:2389
status = read_status("validator", run_id)["status"]
if status == "PLAN_VALIDATION_PASS":
    state_dir.flag_touch(Flag.PLAN_VALIDATION_PASSED)
```
Flag 는 *summary state*. status JSON 은 *atomic record*. 두 layer 보존.

#### 옵션 B: Flag 폐기 — status JSON 합본으로 대체
```python
# 단일 .claude/harness-state/<run>/workflow-state.json
{
  "validator-PLAN_VALIDATION": {"status": "PASS", "ts": "..."},
  "security-reviewer": {"status": "SECURE", "ts": "..."},
  ...
}
```
Flag.PLAN_VALIDATION_PASSED 같은 구분 사라짐. workflow-state.json 한 파일에서 전체 워크플로우 단계 조회.

**권장**: A 옵션 (Flag 보존). recovery 로직이 Flag 기반 (`force-retry`, `escalate_history`) — 변경 폭 최소화. Phase D 에서 B 검토.

### 4.6 parse_marker 14 호출지

| 파일 | 라인 | 호출 패턴 | 변경 |
|---|---|---|---|
| impl_loop.py | 451 | `parse_marker(arch_out, "SPEC_GAP_RESOLVED\|...")` | architect status JSON read |
| impl_loop.py | 651 | `parse_marker(pr_out, "LGTM\|CHANGES_REQUESTED")` | pr-reviewer status JSON read |
| impl_loop.py | 986 | `parse_marker(te_tdd_out, "TESTS_WRITTEN")` | test-engineer status JSON read |
| impl_loop.py | 1174 | `parse_marker(arch_out, "SPEC_GAP_RESOLVED\|...")` | (위와 동일) |
| impl_loop.py | 1339 | `parse_marker(val_out, "PASS\|FAIL\|SPEC_MISSING")` | validator(CODE) status JSON |
| impl_loop.py | 1440 | `parse_marker(pr_out, "LGTM\|CHANGES_REQUESTED")` | pr-reviewer (위와 동일) |
| impl_loop.py | 1575 | `parse_marker(sec_out, "SECURE\|VULNERABILITIES_FOUND")` | security-reviewer status JSON |
| impl_router.py | 90 | `parse_marker(...)` | (모드 분기) |
| impl_router.py | 403 | `parse_marker(...)` | architect 모드 |
| core.py | 2337 | `parse_marker(val_out, "PLAN_VALIDATION_*")` | validator(PLAN) |
| core.py | 2390 | `parse_marker(val_out2, ...)` | validator rework |
| core.py | 2427 | `parse_marker(val_out, "DESIGN_REVIEW_*")` | validator(DESIGN) |
| core.py | 2463 | `parse_marker(val_out2, ...)` | validator rework |
| core.py | 2500 | `parse_marker(val_out, "UX_REVIEW_*")` | validator(UX) |
| core.py | 2537 | `parse_marker(val_out2, ...)` | validator rework |
| plan_loop.py | 133 | `parse_marker(pp_out, "PRODUCT_PLAN_*")` | product-planner status JSON |
| plan_loop.py | 196 | `parse_marker(pr_out, "PLAN_REVIEW_*")` | plan-reviewer status JSON |
| plan_loop.py | 320 | `parse_marker(uxa_out, "UX_FLOW_*")` | ux-architect status JSON |

총 18 호출지 (앞서 14는 잘못된 카운트 — 정확히 18). 각 약 5 LOC 변경 = ~90 LOC.

### 4.7 agents/*.md 의 @OUTPUT 정의 (33 정의)

**현재**: `@OUTPUT: { "marker": "PASS / FAIL", "fail_items?": "..." }` 텍스트 컨벤션.

**적용 후**:
```
@OUTPUT_FILE: .claude/harness-state/<run>/validator-CODE_VALIDATION.json
@OUTPUT_SCHEMA: { "status": "PASS"|"FAIL"|"SPEC_MISSING", "fail_items": [...], "save_path"?: "docs/validation/..." }
@OUTPUT_RULE: 마지막 단계에서 Write 도구로 위 파일 작성. 미작성 시 워크플로우 즉시 종료.
```

33 @OUTPUT 정의 모두 위 형식 변환. validator (5 모드), architect (7 모드), designer (4 모드), 등.

### 4.8 spec / architecture 문서

**`docs/harness-spec.md` §3 I-2** (마커 강제 invariant):
> 변경 전: "에이전트 마커 emit → harness parse_marker 로 결정론"
> 변경 후: "에이전트 status JSON mutate → harness 가 그 파일만 read. 미mutate=워크플로우 종료."

**`docs/harness-architecture.md` §5** (메커니즘 섹션):
- parse_marker 사다리 → state_io.read_status() 단일 함수
- handoff prose → status JSON next_actions
- W0 schema 와의 결합 명시

**PR title 토큰**: `[invariant-shift]` (CHG-13 시리즈와 동일 패턴)

### 4.9 최근 CHG-14 [14.1] 와의 정합성 충돌

**문제**: PR #17 (어제 머지) 가 `MARKER_ALIASES` 12 변형 추가. 본 proposal 이 그 사다리를 *전체 폐기*. 즉 PR #17 가치가 본 proposal 머지 시 **0**.

**해석 1 (sunk-cost)**: PR #17 은 임시 우회책으로 명시됨 ("agent docs canonical 룰 강화 권장" 경고 포함). 폐기 자연스러움.

**해석 2 (스테이징 정합)**: 본 proposal Phase 1 (validator) 적용 후 PR #17 가 *여전히 작동* 해야 함 — 다른 agent 들은 alias 사다리 의존. Phase 3 (Legacy Sweep) 시점에만 PR #17 와 함께 폐기.

**권장**: 해석 2. Phase 별 alias 사다리 부분 제거 (해당 agent 만), Phase 3 끝나야 MARKER_ALIASES dict 자체 삭제.

---

## 5. Phase 분할 (Compressed Migration — 4 기둥 정합)

> **압축 원칙**: 마이그레이션 layer 가 어차피 폐기될 거면 *마이그레이션 자체가 낭비*. agent 단위로 신규 패턴 + legacy 폐기를 *동시에* 진행. ENV 게이트가 회귀 안전망.

### Phase 1 — Foundation Migration: validator 단일 agent (sub-phase 4 분할, 3일)

> **리뷰 #1 반영**: Phase 1 한 덩어리 진입 시 회귀 원인 분리 불가능. 4 sub-phase 분할 + 각 ENV 게이트 별도. 2일 → 3일이지만 회귀 분리 가치 큼.

**Sub-phase 분할**:

| sub | 범위 | ENV 게이트 |
|---|---|---|
| **1.1 Mechanism** | parse_marker → read_status (validator 7 호출지) + state_io.py + ALLOW_MATRIX/disallowedTools | `HARNESS_STATUS_JSON_VALIDATOR_MECHANISM=1` |
| **1.2 Handoff** | validator → engineer status JSON next_actions[] (generate_handoff 우회) | `HARNESS_STATUS_JSON_VALIDATOR_HANDOFF=1` |
| **1.3 Preamble** | validator 한정 점진 공개 (preamble.md 자동 주입 우회, hot context only) | `HARNESS_STATUS_JSON_VALIDATOR_PREAMBLE=1` |
| **1.4 Checkpoint** | plan_loop checkpoint hash 대상 prose → status JSON (validator 영역) | `HARNESS_STATUS_JSON_VALIDATOR_CHECKPOINT=1` |

각 sub-phase 별도 PR. 1.1 통과 + 1 cycle 도그푸딩 후 1.2 진입. 회귀 발생 시 어느 sub 가 원인인지 ENV 게이트 토글로 분리 가능.

**범위**: validator 5 모드 + validator → engineer handoff 1쌍 — 단일 agent 로 *전체 발상* 검증

**변경**:
- `harness/state_io.py` 신규 (~80 LOC, write_status / read_status / clear_run_state, R8 normalize 포함)
- `agents/validator.md` + 5 sub-doc:
  - @OUTPUT_FILE / @OUTPUT_SCHEMA / @OUTPUT_RULE 형식
  - 점진 공개: validator 호출 시 *전체 preamble dump 대신* hot context (현재 모드별 검증 대상 docs 만) 주입
  - **5질문 템플릿 흡수 (optional)** — schema 에 `non_obvious_patterns: string[]` (optional) 추가. agent 가 검증 중 발견한 *비명백한 패턴* 자율 기록. 비어있어도 schema 통과. 원칙 3 정합 (자율성).
    ```json
    {
      "status": "PASS|FAIL|SPEC_MISSING",
      "fail_items": [...],
      "non_obvious_patterns": [   // optional
        "LEGACY_PROCESSING enum 절대 추가 금지 — repo sync 미친다",
        "..."
      ]
    }
    ```
- `agent-config/validator.md` 가 있으면 → `agents/validator.md` 로 통합 (별 layer 폐기)
- `harness/core.py:1027` validator disallowedTools 에서 Write 제거
- `hooks/agent-boundary.py:85` validator ALLOW_MATRIX 에 status path 추가 (3-layer defense: state_io self-validate + PreToolUse + PostToolUse)
- `core.py` 6 호출지 (2337, 2390, 2427, 2463, 2500, 2537) + `impl_loop.py` 1 호출지 (1339) parse_marker → read_status
- **handoff 동시 변환**: validator → engineer 핸드오프를 prose 대신 status JSON 의 `next_actions[]` 로. `generate_handoff` / `write_handoff` 호출은 validator 한정 우회
- `harness/plan_loop.py:265` checkpoint hash 대상을 prose → status JSON 자체 hash 로 (validator 영역만)

**ENV 게이트**: `HARNESS_STATUS_JSON_VALIDATOR=1` 일 때만 신규 path. off 시 기존 parse_marker + prose handoff (회귀 안전망).

**Pre-flight 데이터 측정 (R4 대응)**:
- Phase 1 진입 *전*에 1 cycle 도그푸딩 으로 `MARKER_ALIASES alias hit` stderr 빈도 카탈로그
- 0건 = status JSON 정당화. > 0 = 어느 변형이 hit 인지 schema 설계 반영

**Acceptance**:
- validator 호출 7곳 모두 status JSON mutate
- validator preamble 토큰 측정 (Phase 1 전후 비교, 목표 30% 절감)
- jajang 도그푸딩 1 cycle marker fragility 0건 (validator 한정)
- read_status FileNotFound + prose 폴백 hit 횟수 측정 → R2 비용 폭증 검증

---

### Phase 2 — Multi-Agent Rollout: 12 agent 확장 + handoff 전체 (1.5주)

**범위**: validator 외 12 agent (architect 7 모드, engineer, designer 4 모드, design-critic, qa, ux-architect, product-planner, plan-reviewer, pr-reviewer, security-reviewer, test-engineer)

**복잡도 분포 (R5 재산정)**:
- 단순 tier 11 (각 30분: 변환 + handoff schema) = 5.5시간
- 중간 tier 12 (각 1시간: schema 설계 + 변환 + 검증) = 12시간
- 복잡 tier 8 (architect 7 모드, designer 4 모드, ux-architect 3 모드, security-reviewer vulnerabilities, design-critic variants — 각 2시간) = 16시간
- handoff schema (agent 쌍별, 약 8쌍 × 30분) = 4시간
- **합계 ~37시간 (5일)** + 회귀 검증 도그푸딩 1 cycle (별도)

**변경**:
- 11 호출지 (parse_marker → read_status): impl_loop 6, plan_loop 3, impl_router 2
- 33 @OUTPUT 정의 신규 형식 (validator 5 제외하면 28)
- 모든 agent disallowedTools / ALLOW_MATRIX 갱신 (Write 허용 + path 화이트리스트)
- handoff 전체 schema 화 (`generate_handoff` / `write_handoff` 호출 0)
- preamble 점진 공개 모든 agent 적용 — `agents/preamble.md` 자동 주입 폐기, agent별 prompt 에 필요 사항 명시
- `agent-config/*.md` 잔존분 → `agents/*.md` 통합 후 디렉토리 삭제
- plan_loop checkpoint hash 대상 전체 status JSON 이전

**ENV 게이트 per agent**: `HARNESS_STATUS_JSON_<AGENT>=1`. 단순 → 중간 → 복잡 순 staged.

**Acceptance**:
- 18 parse_marker 호출지 모두 read_status (validator 7 + 11 = 18)
- generate_handoff / write_handoff 호출 0
- preamble.md 자동 주입 코드 0
- agent-config/ 디렉토리 0 (통합 완료)
- token cost 측정: cache hit 97.3% → 98%+ (preamble 폐기 효과)
- jajang 도그푸딩 1 cycle 무사고

---

### Phase 3 — Legacy Sweep + GitHub 외부화 (3일)

**범위**: 4 기둥 정신 정합 마무리 — legacy 코드 일괄 폐기 + commit-gate 일부 GitHub 외부화

**변경**:

#### 3.1 Legacy 코드 삭제
- `harness/core.py:551-680` `MARKER_ALIASES`, `parse_marker`, `diagnose_marker_miss` 삭제 (~180 LOC)
- `harness/core.py:2040-2200` `generate_handoff` / `write_handoff` 삭제 (~150 LOC)
- `agents/*.md` 의 `---MARKER:X---` 컨벤션 잔재 정리
- `agents/preamble.md` 폐기 (점진 공개 후 미사용)
- ENV 게이트 (`HARNESS_STATUS_JSON_*`) 모두 제거 — 항상 활성

#### 3.2 Flag → workflow-state.json 합본 (옵션 B, R6 대응)
- `harness/core.py:175-210` `class Flag` enum 7 항목 → 단일 `workflow-state.json` 안의 키
- 호출지 약 35곳 변경 (`flag_touch` → `update_workflow_state`)
- force-retry / escalate_history / merge_cooldown recovery 로직은 보존 — 단 state 읽기 위치만 변경

#### 3.3 GitHub 외부화 (4 기둥 #2 정신 — CI 가 강제)
- `commit-gate.py` Gate 1 (gh issue/tracker mutate 차단) → `.github/workflows/tracker-mutate-guard.yml` regex
- `commit-gate.py` Gate 4 (doc-sync) → `.github/workflows/doc-sync.yml` (기존 `scripts/check_doc_sync.py` 활용)
- `commit-gate.py` Gate 5 (LGTM flag) → branch protection 의 *required reviewers* + PR review approval
- Task-ID `HARNESS-CHG-YYYYMMDD-NN` 형식 검증 → `.github/workflows/task-id-format.yml`
- `Document-Exception:` 토큰 검증 → 동일 workflow

#### 3.4 PR #17 (CHG-14.1, alias map) 가치 정정
- `orchestration/changelog.md` 의 CHG-14.1 항목에 "Phase 3 에서 폐기" 명시 추가
- `orchestration/rationale.md` 정정

**Acceptance**:
- `grep parse_marker` → 0건
- `grep generate_handoff` → 0건
- `agents/preamble.md` 미존재
- `class Flag` 미존재
- `commit-gate.py` 코드 ~200 LOC 순감소
- `.github/workflows/` 신규 3 workflow

---

### Phase 4 — Validation: 4 기둥 fitness 측정 (도그푸딩 1 cycle, ~3~5일)

**범위**: 변경 작업 0. 4 기둥 정합 검증 + 측정.

**측정 항목**:

| 4 기둥 | 측정 | 목표 |
|---|---|---|
| 기둥 1 (컨텍스트) | layer 갯수 (CLAUDE.md + agents/*.md + agent-config + preamble + ...) | 5 → 2 |
| 기둥 1 (컨텍스트) | 평균 agent_call 토큰 비용 | 30%+ 절감 |
| 기둥 2 (CI/CD 게이트) | hook 갯수 | 7 → 3 (agent-boundary, plugin-write-guard, skill-stop-protect) |
| 기둥 2 (CI/CD 게이트) | GitHub workflow 갯수 | +3 (tracker, doc-sync, task-id) |
| 기둥 3 (도구 경계) | ALLOW_MATRIX 정합성 (회귀 테스트) | 100% pass |
| 기둥 4 (피드백 루프) | jajang 도그푸딩 marker fragility | 0건 |
| 기둥 4 (피드백 루프) | poor_cache_util 패턴 (improve-token-efficiency) | $507 → $200 미만 |
| 전체 | LOC 순감소 | 5000 → 2500~3000 |
| 전체 | parse_marker 호출지 | 18 → 0 |

**도그푸딩 시나리오**:
- jajang 1 cycle 정상 워크플로우
- jajang scope strict 사고 (모노레포 path 추가) 의도적 발생 → 4 기둥 정합 새 패턴이 어떻게 처리하는지 측정
- token-efficiency 분석 1회 (Phase 1 전후 비교)

**Phase 4 결과 따른 분기**:
- 측정 항목 모두 통과 → Phase 5 진입 또는 proposal 폐기 결정 (changelog 에 기록)
- 일부 항목 회귀 → 회귀 PR 별도 진행. proposal 잔존 항목 명시

---

### Phase 5 — Passive Optimization Hooks (warning-first, 선택적, 2일)

> **착수 전 결정 게이트**: Phase 4 측정 결과 + 30일 측정 데이터 후 명시 결정. 조기 진입 금지. (원칙 5 정합)

**범위**: 세미나 "Mode B Passive Optimization" 정신. 메모리 룰 (`feedback_session_cost_hygiene`) 의 *자동화 버전* — 단 **차단 (deny) 이 아니라 권고 (warn)** 으로 시작.

**원칙 정합**:
- 모든 hook **warning-first**. stderr 경고 + 카운터 누적만. 차단 0.
- 30일 데이터 + 명시 결정 PR 후에만 일부 hook 차단 모드 검토 (원칙 2 정합).
- agent/사용자 자율성 보존 — hook 이 *판단* 하지 않고 *측정* 만.

**3 Hook 신설**:

#### 5.1 PreToolUse Read 큰 파일 감지 (warn)
- 트리거: Read 도구 입력 파일 size > 50k chars (~12.5k tokens)
- 동작: stderr 경고 + `.claude/harness-state/.metrics/large-reads.jsonl` 기록
- 메시지: "Large file Read detected (50k+). Consider sub-agent for exploration to protect main context."
- 차단 0. agent 가 무시 가능.

#### 5.2 PostToolUse agent_call 컨텍스트 사이즈 감지 (warn)
- 트리거: agent_call 종료 후 누적 input_tokens > 200k
- 동작: stderr 경고 + `.claude/harness-state/.metrics/context-bloat.jsonl` 기록
- 메시지: "Context bloat detected (200k+). Consider /compact or new session for next task."
- 차단 0.

#### 5.3 SessionStart 오래된 state 청소 권고 (warn)
- 트리거: SessionStart 시 `.claude/harness-state/<run>` 중 7일 이상 mtime
- 동작: stderr 경고 (목록 출력) + 자동 청소 X
- 메시지: "Old run states detected (7d+). Run `harness clean --older-than 7d` to remove."
- 차단 0. 사용자 명시 명령으로만 청소.

**ENV 게이트**: `HARNESS_PASSIVE_HOOKS=1` 일 때만 활성. 기본 off (opt-in).

**Acceptance**:
- [ ] 3 hook 모두 warning-only. deny/block 0.
- [ ] 4 기둥 framework 정합 (CI/CD 게이트 정신 + 자율성 보존)
- [ ] `.claude/harness-state/.metrics/` 디렉토리 + 3 jsonl 로그
- [ ] 30일 측정 데이터 누적 후 차단 모드 전환 결정 PR 별도 (Phase 5 자체엔 미포함)
- [ ] 신규 deny 0 (원칙 2)

**원칙 위반 회피 명시**:
- ❌ "사용자가 무시한다 → 차단 모드로" 식 자동 승격 금지. 메모리 룰은 *Active 모드* 로 충분.
- ❌ hook 이 자동 청소/자동 compact 수행 금지 (원칙 3 자율성 위반).

---

## 6. Acceptance Criteria (Phase 별)

### Phase 1 (Foundation — validator)
- [ ] `harness/state_io.py` 모듈 + R8 normalize (MissingStatus exception) + 테스트 100%
- [ ] validator disallowedTools 에서 Write 제거 + ALLOW_MATRIX status path 추가 (3-layer defense)
- [ ] validator 7 호출지 (core.py 6 + impl_loop.py 1) parse_marker → read_status
- [ ] validator → engineer handoff 1쌍이 status JSON next_actions[] 로
- [ ] preamble 점진 공개 (validator 한정) 적용, 토큰 30% 절감 측정
- [ ] checkpoint hash 대상 status JSON 자체로 (validator 영역)
- [ ] Pre-flight: alias hit 빈도 카탈로그 (R4 PDCA 데이터)
- [ ] ENV 게이트 `HARNESS_STATUS_JSON_VALIDATOR=1` off 시 회귀 0

### Phase 2 (Multi-Agent Rollout)
- [ ] 18 parse_marker 호출지 모두 read_status (validator 7 + 11)
- [ ] generate_handoff / write_handoff 호출 0
- [ ] 33 @OUTPUT 정의 모두 신규 형식 (validator 5 + 28)
- [ ] preamble.md 자동 주입 코드 0
- [ ] agent-config/ 디렉토리 0 (통합 완료)
- [ ] cache hit ratio 97.3% → 98%+ (preamble 폐기 효과)
- [ ] jajang 도그푸딩 1 cycle 무사고

### Phase 3 (Legacy Sweep + GitHub 외부화)
- [ ] `MARKER_ALIASES` / `parse_marker` / `diagnose_marker_miss` 코드 삭제
- [ ] `generate_handoff` / `write_handoff` 코드 삭제
- [ ] `class Flag` enum 폐기 → `workflow-state.json` 합본 (옵션 B)
- [ ] `commit-gate.py` Gate 1/4/5 → `.github/workflows/*` 3 workflow 신설
- [ ] CHG-14.1 (alias map) 폐기 정정 (changelog/rationale)
- [ ] ENV 게이트 (`HARNESS_STATUS_JSON_*`) 모두 제거
- [ ] commit-gate.py 코드 ~200 LOC 순감소

### Phase 4 (Validation — 4 기둥 fitness)
- [ ] 컨텍스트 layer 5 → 2
- [ ] hook 갯수 7 → 3
- [ ] LOC 순감소 5000 → 2500~3000
- [ ] parse_marker 호출지 18 → 0
- [ ] poor_cache_util 패턴 비용 $507 → $200 미만
- [ ] catastrophic 가드 무손실 (HARNESS_INFRA_PATTERNS, READ_DENY_MATRIX, plugin-write-guard, agent-boundary ALLOW_MATRIX, skill-stop-protect)
- [ ] docs/harness-spec.md §3 I-2 + harness-architecture.md §5 갱신
- [ ] PR title `[invariant-shift] HARNESS-CHG-YYYYMMDD-NN status json mutate phase {1,2,3}`

### Phase 5 (Passive Hooks — opt-in, warning-first)
- [ ] 3 hook 신설 (large-reads / context-bloat / old-state) 모두 warning-only
- [ ] `.claude/harness-state/.metrics/*.jsonl` 3 로그 파일
- [ ] ENV 게이트 `HARNESS_PASSIVE_HOOKS=1` 기본 off (opt-in)
- [ ] 신규 deny/block 0 (원칙 2)
- [ ] 30일 측정 데이터 누적 시작 (차단 모드 전환은 별도 결정 PR)

### 원칙 위반 측정 (모든 Phase 공통)
- [ ] 신규 required schema 키 0 (있으면 제거 정당화 PR)
- [ ] 신규 강제 (deny) hook 0 (원칙 2 정합)
- [ ] 룰 순감소 추세 (Phase 별 LOC + hook 수 모니터링) — 증가 시 정당화 PR
- [ ] agent freeform 영역 보존 (`non_obvious_patterns` 등 optional 필드 유지)

---

## 7. Out of Scope

- **검증자 인스턴스 격리** — subprocess 격리 그대로. 본 proposal 무관.
- **Conditional workflow branch** (FAIL → SPEC_GAP → 재검증) — impl_loop.py 시퀀스 코드 보존.
- **Multi-turn recovery state** (escalate_history, force-retry, merge_cooldown) — 그대로.
- **catastrophic hook 가드** (plugin-write-guard, HARNESS_INFRA_PATTERNS, READ_DENY_MATRIX) — 그대로.
- **GitHub-level audit** (changelog, rationale, Issue tracking) — 그대로.
- **agent_call subprocess 자체** — claude CLI subprocess 격리 보존.
- **W0 `--json-schema` 적용** — 본 proposal 의 *백업 layer* 로 결합. 단독 채택 별도.
- **사용자 프로젝트용 deny-patterns.yaml 시스템** — 세미나 "회사 패턴 Deny List" 정신. RWHarness 가 init 시 템플릿 제공 + agent-boundary 처럼 사용자 프로젝트 비즈니스 패턴 차단. **별도 epic** (RWHarness 자체와 무관 — 사용자 프로젝트 가치 확장). 원칙 1 정합 (RWHarness 코어 부풀리기 회피).
- **AI-readiness-cartography 스킬 채택** — jha0313 다른 스킬. 어제 본. 별도 작업 (스킬 import 30분).

---

## 8. Risks

### R1. ReadOnly 6 agent 의 Write 차단 해제 — 방어선 단계 후퇴
- **시나리오**: validator/pr-reviewer/design-critic/security-reviewer/plan-reviewer/qa 가 현재 disallowedTools 의 `Write` 로 *물리 차단*. 신규엔 Write 허용 + hook regex 로 path 강제 → "도구 차단" → "정규식 매칭" 한 단계 후퇴.
- **단일 장애점**: agent-boundary.py 의 ALLOW_MATRIX 정규식 오류 한 글자가 ReadOnly 보장 붕괴.
- **대응 (3-layer defense)**:
  1. state_io.py 가 path 생성 시 동일 regex 로 self-validate 후 Write
  2. agent-boundary.py PreToolUse 가 regex 매칭으로 차단
  3. **PostToolUse Write hook 추가** — Write 직후 path 가 화이트리스트 안인지 사후 검증, 위반 시 fail loud (state 파일 자체엔 영향 없으나 다음 turn 의 진단 데이터 확보)
- **수용**: hook 단일 장애점은 *완전 제거 불가능*. 3-layer 로 *완화*만. 회귀 테스트로 regex 변형 케이스 (oversight) 카탈로그.

### R2. LLM Write 누락 → retry 비용 폭증 + deadlock
- **시나리오**: validator agent 가 prose 만 emit 하고 status JSON Write 안 함 → read_status FileNotFound → retry → 실패 반복.
- **W0 측정 데이터**: schema 위반 강제 시 num_turns 7 → 26, cost $0.15 → $0.29 (~2x). status JSON 누락도 동일 패턴 — schema 백업과 *같은 약점 공유* (LLM 형식 따르기 실패가 원인).
- **대응**:
  1. agent prompt 의 STATE_PROMPT 매우 명시적 (마지막 액션이 Write 임을 단언)
  2. `--json-schema` 동시 적용 (이중 결정론) — 단 백업 layer 도 같은 약점
  3. **비용 cap**: `agent_call` 의 `--max-budget-usd 2.00` 그대로 활용. 위반 시 immediate fail
  4. **prose 마지막 메시지 폴백 1차 한정**: read_status FileNotFound 시 *retry 직전* prose 끝에서 status 추론 (`---MARKER:X---` 잔재 형식 잡으면 normalize). 이 폴백은 1 cycle 도그푸딩 후 hit 0이면 폐기. (alias 사다리 ↔ 신규 패턴 사이 가교)
- **측정**: Phase A 후 read_status FileNotFound 횟수 + prose 폴백 hit 횟수 + 비용 델타.

### R3. plugin-write-guard 정합성
- **검증 결과**:
  - 차단 경로 = `~/.claude/plugins/{cache,marketplaces,data}/**` (글로벌)
  - 신규 status JSON 경로 = 프로젝트 로컬 `./.claude/harness-state/<run>/<agent>-*.json`
  - **사용자 프로젝트 = 안전** (별개 경로, 차단 안 됨)
- **인프라 프로젝트 케이스**: RWHarness 자체가 `~/.claude/plugins/cache/realworld-harness/...` 안에 있을 때 (`is_infra_project()` True) — status JSON 도 plugin 디렉토리 안 → **plugin-write-guard 가 차단**
- **대응**:
  - 사용자 프로젝트: 변경 없음
  - 인프라 프로젝트: status JSON 위치를 `~/.claude/harness-state-infra/` (홈 직속) 으로 분기. `is_infra_project()` 분기 룰 (메모리/CLAUDE.md 인프라 분기 룰) 과 정합

### R4. CHG-14 [14.1] (alias map) 도그푸딩 0 cycle — A→D 점프
- **사실**: CHG-09.1 (alias 도입 PR #9) → CHG-14.1 (alias 12 변형 확장 PR #17, 어제 머지) → 본 proposal "alias 사다리 폐기" 직진 = PDCA 가 아니라 A 의 추측에서 D 로 점프
- **대응**:
  - Phase A 자체를 **alias 병존 단계** 로 정의. status JSON 신규 path + alias 폴백 동시 활성. ENV 게이트 (`HARNESS_STATUS_JSON_VALIDATOR=1`) 로 신규 우선, 실패 시 alias 폴백
  - **measurement gate**: Phase A 진입 *전*에 1 cycle 도그푸딩 으로 `MARKER_ALIASES alias hit` stderr 로그 빈도 측정. 빈도 0 이면 status JSON 정당화. 빈도 > 0 이면 어느 변형이 hit 인지 카탈로그 후 schema 설계 반영
  - PDCA 룰 박기: "신규 메커니즘 채택 전 기존 메커니즘의 hit 데이터 1 cycle 측정 강제"

### R5. Schema 설계 비용 — 단순 변환 시간만 추정한 누락
- **재산정**:
  - 단순 tier 14 × 5분 (변환만) = 70분
  - 중간 tier 12 × 15분 (변환 + 검토) = 180분
  - 복잡 tier 7 × 30분 (schema 설계 + 변환 + 테스트) = 210분
  - **schema design 별도**: ux-architect 다중 라인 (3 모드) + security-reviewer (vulnerabilities array) + designer (array of objects 4 모드) = 8 schema × 1시간 = 8시간
  - **합계 ~16시간 (2일)** — 기존 추정 3시간의 **5배**
- **위험**: 잘못 설계된 schema (e.g. enum 빠뜨림, optional 잘못) → LLM 변형 emit → "schema 강제 retry" 또는 "schema 확장" 욕구 → 사다리 부활
- **대응**:
  - 복잡 tier 8 schema 는 신규 프로젝트 메인 Claude 가 직접 설계 (escape hatch — schema 결정 막힐 때만 architect 명시 호출)
  - 각 schema 작성 시 RWHarness 호출 1 sample 로 검증 후 확정
  - schema 변경 시 ENV 게이트 별도 (`HARNESS_STATUS_JSON_<AGENT>_V<N>`) — 변경 자체가 staged

### R6. 회복 로직 부분 적용 (Flag 잔존)
- **사실**: Phase 1~2 까지는 옵션 A (Flag 보존 + status JSON 후 derive) = 중복 layer 잔존
- **대응**: **Phase 3.2 에서 옵션 B (workflow-state.json 합본) 정식 채택**. 별도 Phase 추가 없음 (리뷰 #2 단일화).
  - `Flag` enum 7 항목 × 호출지 평균 5곳 = 약 35 호출지 변경
  - force-retry / escalate_history / merge_cooldown 정책 자체는 보존, state 읽기 위치만 변경
  - Phase 3.2 진입 조건: Phase 1~2 안정 + 1 cycle 도그푸딩 무사고

### R7. Checkpoint 시스템 정합성 (CHG ref 정정)
- **CHG-41 / 43+44 ref 오류**: changelog 최신 = HARNESS-CHG-20260428-14.5. CHG-41 / 43+44 존재 안 함.
- **단 우려 자체는 유효**: `harness/plan_loop.py:51-89` 에 `load_plan_checkpoint` / `save_plan_checkpoint` + prose hash 게이트 (`_current_prd_hash`, `_current_ux_hash`) **실재**. plan_loop.py:265, 351, 496 등에서 사용.
- **status JSON pivot 시 충돌**: 현재 hash 대상이 prose 출력 (`pp_out_file`, `uxa_out_file` 등). 신규엔 prose 가 *진단용* 으로 전락 — hash 대상 미명확 시 checkpoint 무효화 룰 깨짐.
- **대응**:
  - hash 대상을 **status JSON 자체 hash** 로 변경 (`hashlib.sha256(read_status_raw(...))`). prose hash 폐기.
  - checkpoint key 도 status JSON path 기반으로 정렬
  - Phase 1.4 (Checkpoint) 시 plan_loop.py 의 product-planner / plan-reviewer / ux-architect 코드 호출 위치 (3 호출지) 동시 변경
  - **acceptance**: status JSON 적용 후 checkpoint hit/miss ratio 가 변경 전 ±5% 안

### R8. JSON malformed — 단일 실패모드 약속 깨짐
- **다수 실패모드**:
  - (a) FileNotFound (Write 누락)
  - (b) JSONDecodeError (Write 도중 crash, 부분 작성)
  - (c) schema violation (status enum 외 값, required 키 누락)
  - (d) 빈 파일 (Write 직후 sync 실패)
  - (e) race condition (multi-step 시 중간 상태 read)
- **대응 — state_io.py 의 read_status 가 모든 실패를 단일 모드로 normalize**:
  ```python
  class MissingStatus(Exception):
      reason: Literal["not_found", "malformed_json", "schema_violation", "empty", "race"]
      detail: str

  def read_status(agent, run_id) -> dict:
      path = state_path(agent, run_id)
      if not path.exists():
          raise MissingStatus("not_found", str(path))
      raw = path.read_text()
      if not raw.strip():
          raise MissingStatus("empty", str(path))
      try:
          data = json.loads(raw)
      except JSONDecodeError as e:
          raise MissingStatus("malformed_json", f"{path}: {e}")
      if "status" not in data:
          raise MissingStatus("schema_violation", f"{path}: missing 'status'")
      # ... enum 검증, race 휴리스틱 등
      return data
  ```
- **caller 측**: try/except MissingStatus 로 단일 catch. reason 별 retry 정책 분기 (e.g. `empty`/`race` 는 100ms 후 1회 재read, 나머지는 즉시 fail)
- **acceptance**: read_status 의 모든 실패가 MissingStatus 로 catch. 다른 exception 누수 0.

### R9. GitHub 외부화 피드백 지연 trade-off (리뷰 #6 신규)
- **사실**: Phase 3.3 가 commit-gate Gate 1/4/5 → GitHub Actions 외부화. *push 전 즉시 차단* → *push 후 PR CI 실패* 로 피드백 지점 이동.
- **사용자 cost**: PR 생성 후 CI 실패 알림 받고 fix → push → 재 CI 사이클. local hook 대비 느림 (~수분).
- **trade-off 정합**:
  - 4 기둥 #2 정신 (CI 가 강제) + 원칙 2 (catastrophic 만 강제) = GitHub native 가 옳다
  - 단 사용자 즉시 피드백 손실은 사실
- **완화**:
  - local pre-commit hook 으로 *동일 룰 best-effort 검증* 보존 (단 차단 아닌 warning). 사용자가 미리 알 수 있게.
  - GitHub workflow 의 fail-fast 모드 (regex 위반 즉시 fail). PR 분 단위 피드백.
- **acceptance**: pre-commit warning 으로 push 전 90% catch 측정. 나머지 10% 는 PR CI 가 차단.

### R10. non_obvious_patterns 다운스트림 부재 (리뷰 #3 신규)
- **사실**: Phase 1 schema 의 `non_obvious_patterns` (optional) 가 누가/언제 read 하는지 미명세. agent 가 기록만 하고 dead weight 위험.
- **다운스트림 명시 (Phase 1.1 안에 흡수)**:
  - **(a) `.claude/harness-state/.metrics/non-obvious-patterns.jsonl` 카탈로그**: read_status 시 patterns 자동 추출 → 시간순 누적 로그
  - **(b) 월 1회 메인 리뷰 (수동)**: jsonl 로그 → agent docs canonical 강화 input. 반복 패턴 발견 시 `agents/<agent>.md` 의 명시 룰로 승격 PR
  - **(c) 미사용 시 자동 폐기**: 30일 무사용 (jsonl 로그 hit 0 + 승격 PR 0) 시 schema 에서 필드 자체 삭제 (원칙 1 정합 — 룰이 룰을 부르는 cycle 차단)
- **acceptance**: 카탈로그 jsonl 자동 누적. 월 1회 리뷰 절차 docs/proposals 또는 orchestration 에 명시. 30일 dead weight 검증 일정 박힘.

### R11. cache hit 측정의 control 부재 (리뷰 #4 신규)
- **사실**: Phase 1 의 `cache hit 97.3% → 98%+` 측정이 다른 변경 (status JSON Write 추가, schema 응답 변형) 과 분리 불가능. 통계 노이즈에 묻힐 가능성.
- **대응**:
  - **Phase 1 직전 1 cycle 도그푸딩 = baseline** 측정. improve-token-efficiency 결과 보존
  - **Phase 1 직후 1 cycle = treatment** 측정
  - **차이 ±2pp 이내면 "preamble 효과 미검증"** 으로 명시. cache hit 개선이 다른 요인일 수 있음 인정
  - 명확한 검증을 원하면 **Phase 1.3 (Preamble) 만 단독 토글** A/B 테스트: 1.3 off / 1.3 on 의 cache hit 비교
- **acceptance**: baseline + treatment 측정 데이터 보존. ±2pp 이내일 때 결론 "미검증" 명시.

### R12. Phase 5 ↔ Active 메모리 룰 인터페이스 (리뷰 #5 신규)
- **사실**: Active 모드 (`feedback_session_cost_hygiene` 메모리 룰, 사람 의식적 /compact) + Passive opt-in (Phase 5 hook) 동시 활성 시 메시지 중복 가능.
- **인터페이스 룰**:
  - Passive hook 의 stderr 메시지에 `[passive-hint]` prefix
  - 사용자가 Active 모드 *명시 인지* (메모리 룰 적용 중) 시 Passive `HARNESS_PASSIVE_HOOKS=0` 으로 끄기 권고
  - 또는 Passive hook 이 *threshold* 만 다르게 (Active 메모리 룰: 200k → Passive: 250k) — Active 가 미리 잡으면 Passive 안 발동
- **acceptance**: Phase 5 PR 에 인터페이스 룰 명시. 메모리 룰 (`feedback_session_cost_hygiene`) 에도 cross-link 추가.

---

## 9. Inputs (구현자 먼저 읽을 자료)

| 파일 | 왜 |
|---|---|
| `docs/harness-spec.md` 전체 | invariant 헌법 |
| `harness/core.py:551-680` (MARKER_ALIASES + parse_marker) | 폐기 대상 메커니즘 |
| `harness/core.py:1024-1043` (`_AGENT_DISALLOWED`) | Write 차단 매트릭스 |
| `harness/core.py:2040, 2150` (generate_handoff, write_handoff) | handoff prose 생성 |
| `harness/core.py:175-210` (`class Flag`) | flag 시스템 |
| `hooks/agent-boundary.py:37-113` (HARNESS_INFRA_PATTERNS, ALLOW_MATRIX, READ_DENY_MATRIX) | path 가드 |
| `agents/validator.md` + `agents/validator/*.md` (5 모드 sub-doc) | @OUTPUT 변환 1차 대상 |
| W0 PoC 결과 (대화 로그) | --json-schema 동작 검증 |
| jha0313/harness_framework `scripts/execute.py` | 발상 원천 |
| `orchestration/changelog.md` HARNESS-CHG-20260428-09 (alias map) + CHG-14 [14.1] | 폐기될 reactive 패치들 |

---

## 10. 적용 모드

본 proposal 은 **신규 프로젝트 (lightharness 등) 에서 메인 Claude 직접 작업** 모드로 진행. RWHarness 가드 미적용 환경 + CHG 시스템만 도입. architect/validator/engineer 위임 강제 없음 (§11.4 정합).

RWHarness 자체에는 적용 안 함 — 본 proposal 은 신규 프로젝트의 development input 역할.

---

## 11. Fork-and-Refactor Development Guide (다른 프로젝트 에이전트 입력)

> **본 proposal 은 RWHarness 자체에 직접 적용하지 않는다**. 신규 프로젝트 (가칭: `lightharness`) 를 새로 파고, RWHarness 코드를 *복사하면서 리팩터링* 하는 방식. 이 섹션은 신규 프로젝트의 첫 architect/engineer 가 읽을 자료.

### 11.1 신규 프로젝트 정체성

- **이름 후보**: `lightharness`, `microharness`, `rwh-lite`, `harness-v2` (사용자 결정 필요)
- **정체성** (RWHarness 코어 보존 + 본 proposal 정합):
  > "Claude 의 disobedience 를 외부 process 로 결정론화하는 *최소 레이어*. 4 기둥 (CLAUDE.md / CI 게이트 / 도구 경계 / 피드백 루프) 정합 + 함정 회피 원칙 5개 (§2.5) 불변"
- **vs RWHarness 차이**:
  - 결정론 메커니즘: parse_marker → status JSON mutate
  - 컨텍스트: 5 layer → 2 layer (Compass not Encyclopedia)
  - 게이트: hook 7 → 3 (catastrophic 만)
  - 외부화: commit-gate Gate 1/4/5 → GitHub Actions
  - LOC: 5000 → ~2500 목표

### 11.2 신규 architect 의 모듈 분류 framework

신규 프로젝트 진입 시 메인 Claude 가 RWHarness 를 read 후 *각 모듈을 자율 분류*. 본 proposal 은 결정 표 박지 않음 (§2.5 원칙 3 정합). framework 만:

각 모듈 3 질문:
1. **Catastrophic-prevention 인가?** — jajang 도그푸딩 12 PR 의 *돌이킬 수 없는 사고* 를 막는가? → 보존
2. **발상 변경으로 자연 폐기되는가?** — status JSON mutate 적용 시 의미 잃는가? → 폐기 후보
3. **단순화 가능한가?** — 룰 누적 패턴인가? → 리팩터링 후보

분류 결과는 신규 프로젝트의 `docs/migration-decisions.md` 에 기록 (모듈별 결정 + 근거).

### 11.3 RWHarness Read 권한 부여 메커니즘

신규 저장소에서 RWHarness 를 read 하는 방법 (검증된 옵션):

- **`--add-dir`**: `claude --add-dir /Users/dc.kim/project/RWHarness` 또는 `.claude/settings.json` 영구 등록
- **Bash 직접 path**: prompt 에 절대 path 명시, agent 가 Read 도구로 접근

가드는 RWHarness 화이트리스트 밖이라 차단 0 — 둘 다 안전.

### 11.4 도입할 것 / 도입 안 할 것 / 안전망

#### 도입할 것
- `orchestration/changelog.md` (HARNESS-CHG-YYYYMMDD-NN, 1부터 재시작)
- `orchestration/rationale.md` (4섹션: Context / Decision / Alternatives / Consequences)
- PR title `[invariant-shift] HARNESS-CHG-* …`
- Task-ID 형식 검증 (gh action regex 1줄)
- Document-Exception 룰 (긴급 fix escape hatch)

#### 도입 안 할 것
- architect / validator / engineer 위임 사이클 (가드 미적용 환경에서 ceremony 만 남음)
- agent-boundary / commit-gate hook (가드 자체가 신규 프로젝트엔 미적용)
- impl_loop subprocess 시퀀스 강제 (메인 직접 작업)

#### 안전망 (검증자 격리 손실 보완)
- **Sub-phase 마다 smoke test 강제**: 코드 review 아닌 *실제 RWHarness 호출 1~2회 동작 검증*
- **매 sub-phase squash merge 후 `improve-token-efficiency` 측정**: cache hit / poor_cache_util 회귀 시 즉시 rollback
- **Escape hatch**: schema 설계 결정 막힐 때 / conditional branch 정합성 의문일 때 architect 명시 호출 (강제 아닌 옵션)

---

## 12. RWHarness → 신규 Plugin 전환 절차

> **신규 plugin 1차 완성 (Phase 1~4 통과) 후 RWHarness 대체 테스트**.

### 12.1 사전 검증 (현재 시스템 상태)

확인된 사실:
- RWHarness 설치 위치: `~/.claude/plugins/cache/realworld-harness/realworld-harness/0.1.0-alpha/`
- 활성 프로젝트 화이트리스트: `~/.claude/harness-projects.json` (현재 4 프로젝트: `~/.claude`, `jajang`, `memoryBattle`, `/private/tmp/rw-quickstart`)
- 플러그인 매니저: `claude plugin {install|uninstall|disable|enable|list|marketplace}`
- 마켓플레이스 이름 / 플러그인 이름 형식: `<plugin>@<marketplace>` (예: `realworld-harness@realworld-harness`)

### 12.2 신규 Plugin 빌드 (Phase 1~4 후)

신규 프로젝트 (`lightharness`) 디렉토리에서:

```bash
# 1. .claude-plugin/marketplace.json + plugin.json 작성 완료 검증
cat lightharness/.claude-plugin/plugin.json   # name: "lightharness", version: "0.1.0-alpha"
cat lightharness/.claude-plugin/marketplace.json

# 2. 로컬 marketplace 검증
claude plugin validate lightharness/.claude-plugin
```

### 12.3 단계적 전환 (RWHarness 보존 + 비교)

**원칙**: RWHarness 즉시 제거 금지. 1~2 cycle 도그푸딩으로 동등성 검증 후 제거.

#### 12.3.1 신규 plugin 마켓플레이스 등록 (로컬)

```bash
# 로컬 경로 marketplace 추가
claude plugin marketplace add /Users/dc.kim/project/lightharness/.claude-plugin

# 또는 GitHub 마켓플레이스
claude plugin marketplace add github:alruminum/lightharness
```

#### 12.3.2 신규 plugin 설치 (RWHarness 와 공존 가능 검증)

```bash
claude plugin install lightharness@lightharness
claude plugin list   # realworld-harness + lightharness 둘 다 enabled 확인
```

**충돌 우려**: 두 plugin 이 같은 hook 이름 / agent 이름 사용 시 충돌. 신규 plugin 의 모든 hook/agent 가 `lightharness-` prefix 또는 다른 디렉토리 사용 권장. 또는 신규 plugin 설치 시 RWHarness 자동 disable.

```bash
# 충돌 회피: RWHarness 일시 disable
claude plugin disable realworld-harness@realworld-harness

# 신규 plugin 만 활성
claude plugin list
```

#### 12.3.3 활성 프로젝트 분기

```bash
# harness-projects.json 백업
cp ~/.claude/harness-projects.json ~/.claude/harness-projects.json.bak

# 1 프로젝트 (jajang) 만 신규 plugin 으로 도그푸딩
# → 신규 plugin 이 같은 harness-projects.json 형식 사용 시 자동 적용
# → 형식 다르면 신규 plugin 의 자체 화이트리스트 파일 사용

# 1 cycle 도그푸딩 후 결과 비교 (improve-token-efficiency)
python3 ~/.claude/skills/improve-token-efficiency/scripts/analyze_sessions.py \
  --sessions-dir ~/.claude/projects/-Users-dc-kim-project-jajang
```

#### 12.3.4 통과 시 RWHarness 완전 제거

```bash
# 1. 활성 프로젝트 모두 신규 plugin 으로
claude plugin disable realworld-harness@realworld-harness
claude plugin enable lightharness@lightharness

# 2. 도그푸딩 1~2 cycle 추가 검증

# 3. RWHarness 완전 uninstall
claude plugin uninstall realworld-harness@realworld-harness

# 4. 잔존 파일 정리 (uninstall 후 자동 제거 안 되는 경우)
ls ~/.claude/plugins/cache/realworld-harness   # 이거 남아있으면 수동 삭제
rm -rf ~/.claude/plugins/cache/realworld-harness
rm -rf ~/.claude/plugins/marketplaces/realworld-harness

# 5. 마켓플레이스 제거 (선택)
claude plugin marketplace list
claude plugin marketplace remove realworld-harness
```

#### 12.3.5 즉시 롤백 시나리오 (실패 시)

신규 plugin 도그푸딩 중 catastrophic fail 발견:

```bash
# 1. 신규 plugin 즉시 disable
claude plugin disable lightharness@lightharness

# 2. RWHarness 재활성
claude plugin enable realworld-harness@realworld-harness

# 3. 활성 프로젝트 복구
cp ~/.claude/harness-projects.json.bak ~/.claude/harness-projects.json

# 4. 신규 plugin 의 사고 분석 → 신규 프로젝트 PR 로 fix → 재 도그푸딩
```

### 12.4 보존 데이터

신규 plugin 으로 전환해도 보존:
- `~/.claude/harness-projects.json` — 활성 프로젝트 화이트리스트 (신규 plugin 도 같은 형식 사용 권장)
- `~/.claude/projects/-Users-*/` — Claude Code 세션 jsonl 로그 (improve-token-efficiency 분석용)
- `~/.claude/projects/-Users-*/memory/` — auto memory (RWHarness 관련 메모리는 신규 plugin 에서도 참조)
- 프로젝트별 `.claude/harness-state/` — 신규 plugin 도 같은 디렉토리 사용 시 history 보존

### 12.5 Acceptance — 전환 완료 기준

- [ ] 1 프로젝트 (jajang) 1 cycle 도그푸딩 무사고
- [ ] 추가 1 프로젝트 (memoryBattle) 1 cycle 도그푸딩 무사고
- [ ] cache hit / poor_cache_util 측정값 RWHarness baseline 대비 동등 또는 개선
- [ ] marker fragility 0건
- [ ] catastrophic 가드 작동 검증 (의도적 src/ 외 수정 시도 → 차단 확인)
- [ ] 롤백 절차 검증 (12.3.5 시나리오 1회 dry-run)
- [ ] RWHarness 완전 uninstall 후 7일 무사고

### 12.6 작업 권한 매트릭스

- 신규 프로젝트 빌드 = 메인 Claude 직접 작업 (가드 미적용, §11.4 정합)
- RWHarness 자체는 frozen — 본 proposal 적용 안 함
- 신규 plugin 설치/제거는 사용자 명시 명령 시에만 수행 (catastrophic 가능성)
