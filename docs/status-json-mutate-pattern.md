# Prose-Only Pattern — 형식 강제 폐기 + heuristic enum 추출

> **Status**: PROPOSAL_DRAFT (brainstorm) → **HEURISTIC-ONLY 정착** (DCN-CHG-20260430-04)
> **Origin**: 2026-04-29 jha0313/harness_framework 비교 + W0 PoC + 형식 강제 함정 자각
> **적용**: 신규 프로젝트 (dcNess 등) 에서 메인 Claude 직접 작업. RWHarness 자체엔 적용 안 함. §11 참조.
> **이전 이름**: status-json-mutate-pattern. 신규 진단 (status JSON 도 형식 강제의 한 형태) 후 *prose-only* 로 정정.

> ### ✅ 2026-04-30 정착 결정 — heuristic-only
>
> 본 proposal 의 *원래 비전* 은 "메타 LLM (haiku) 해석" 이었으나, dcNess 도그푸딩 결과 **메타 LLM 호출도 폐기** (DCN-CHG-20260430-04). 이유:
>
> 1. **API 키 의존 회피** — dcNess 자체가 plugin 으로 사용자 환경 도그푸딩. ANTHROPIC_API_KEY 강제 의존 = 진입 장벽.
> 2. **메인 Claude = LLM** — 이미 메인이 LLM 이라 별도 judge 호출 = 2-LLM 패턴. 비용 + latency + 또 다른 사다리 (LLM 결과 검증) 진입 위험.
> 3. **트렌드 위치** — RWH (regex parser, [2024]) → 본 proposal 원안 (메타 LLM, [2025]) → **heuristic-only + 메인 cascade ([2025+])** → structured tool output ([2026 미래]). 한 정거장 더 가벼운 위치.
> 4. **휴리스틱 충분성 측정** — agent prose 가 prose 마지막 영역에 enum 단어 명시하면 단어경계 매칭이 정확. 30일 도그푸딩 데이터에서 heuristic_hit ≥ 80% 확인 시 정당.
>
> **현재 인프라** = `harness/interpret_strategy.py` (heuristic-only) + `harness/signal_io.interpret_signal` (휴리스틱 default + DI swap option). `harness/llm_interpreter.py` 폐기 (삭제). 메인 Claude 가 `MissingSignal` (ambiguous propagate) 받으면 cascade (재호출 / 사용자 위임 / yolo auto-resolve) 결정.
>
> 본 §의 "메타 LLM" / "haiku" 표현은 *원안 (historical)* — 실 동작은 heuristic-only. 미래 schema 강제 도입 시 본 결정 재검토.

---

## 1. Context

### 진앙 — 형식 강제는 사다리를 부른다

```
Layer 1: parse_marker text 매칭 (실패) →
Layer 2: MARKER_ALIASES 12 변형 (alias 사다리) →
Layer 3: status JSON schema 강제 (jha0313 패턴) →
Layer 4: schema 위반 발견 → 더 정교한 schema → 사다리 부활
```

JSON 으로 형식만 바꿔도 같은 함정. 매 LLM 변형 emit 마다 형식 사다리 확장 = jajang 도그푸딩 12 PR cycle 의 본질.

같은 함정의 다른 얼굴 — Flag 시스템:
```
agent 가 flag_touch() 빠뜨림 → 다음 단계 진행 안 됨 →
"왜 안 되지?" 진단 → flag 강제 룰 추가 → 또 빠뜨림 → ...
```

진짜 답은 *형식 / flag / schema 모두 폐기*. agent 자유 emit + 메타 LLM 해석.

---

## 2. Goal

> "agent 는 prose 자유롭게 emit. harness 는 prose 의 *의미* 를 메타 LLM 으로 해석. 형식 강제 0, flag 0, schema 0."

### 폐기 대상

| 영역 | 코드 위치 | LOC |
|---|---|---|
| `MARKER_ALIASES` 12 변형 dict | `harness/core.py:551-604` | 54 |
| `parse_marker` 1차/2차/3차 폴백 | `harness/core.py:607-680` | 110 |
| `diagnose_marker_miss` UNKNOWN 진단 | `harness/core.py:520+` | ~30 |
| `parse_marker` 18 호출지 | impl_loop / core / impl_router / plan_loop | ~90 |
| `---MARKER:X---` 컨벤션 | `agents/*.md` 의 @OUTPUT 33 정의 | — |
| `generate_handoff` / `write_handoff` prose 강제 형식 | `harness/core.py:2040, 2150` | ~150 |
| `class Flag` enum 7 항목 | `harness/core.py:175-210` | ~40 |
| `flag_touch` / `flag_exists` / `flag_rm` 호출 | ~35 위치 | ~70 |
| `agents/preamble.md` 자동 주입 | `harness/core.py:990+` | — |
| `agent-config/*.md` 별 layer | — | — |

총 폐기 LOC: **~550**

### 신규 도입

| 영역 | 위치 | LOC |
|---|---|---|
| `harness/signal_io.py` — prose 저장 + 메타 LLM 해석 | 신규 | ~50 |
| `agents/<agent>.md` 작성 지침 — 형식 X, *결론+이유 명확* 만 가이드 | 변경 | — |

순감소: **~500 LOC**

---

## 2.5 Anti-Patterns — 함정 회피 원칙 (불변)

> **🔴 대 원칙**:
> **harness 가 강제하는 것은 단 2가지 — (1) 작업 순서, (2) 접근 영역. 그 외 모두 agent 자율.**
> - 작업 순서 = 시퀀스 (validator → engineer → pr-reviewer 등) + retry 정책
> - 접근 영역 = file path 경계 (agent-boundary ALLOW/READ_DENY) + 외부 시스템 mutation 차단 (push, gh issue, plugin 디렉토리)
> - **출력 형식 / handoff 형식 / preamble 구조 / marker / status JSON / Flag / 모든 형식적 강제 = agent 자율. harness 가 강제하지 않는다.**

### 원칙 1: 룰이 룰을 부르는 reactive cycle 차단
- 신규 룰 추가 전 *기존 룰 제거* 가능성 우선 검토
- 추가 → 제거 비대칭이 부채

### 원칙 2: 강제 vs 권고 분리
- **강제 (deny/block)**: catastrophic 만 (plugin-write-guard, agent-boundary 인프라 차단, src/ 외 mutation)
- **권고 (warn/log)**: 그 외. 형식 위반, 비용 폭증, 모호한 prose 등은 *측정 + 경고 + 사용자 개입*
- 권고 → 강제 자동 승격 금지 (30일 데이터 + 결정 PR 필수)

### 원칙 3: agent 자율성 최대화
- agent prompt 의 강제 형식 0
- *prose 작성 가이드* (결론 + 이유 명확히) 만 — 형식이 아니라 의미
- agent 가 빠뜨림 = prompt 명료화 우선 (룰 추가 X)

### 원칙 4: 흐름 강제는 catastrophic 시퀀스만
- impl_loop 시퀀스 (validator → engineer → pr-reviewer) = 보존
- 시퀀스 *내부* 행동 = agent 자율

### 원칙 5: 신규 hook 추가 전 30일 측정
- "사고 발생 → hook" 이 아니라 "사고 발생 → 30일 빈도 → 정당화 후 hook"

---

## 3. Mechanism

### 신규 흐름

```
agent_call("validator", prompt + WRITING_GUIDE, issue_num)
  WRITING_GUIDE = "결론과 이유를 명확히 prose 로 작성. 형식 자유."
  → claude CLI subprocess
  → validator: prose 자유 emit (markdown / 평문 / 표)
  → harness 가 stdout 캡처 → .claude/harness-state/<issue_num>/<agent>-<mode>.md 저장
  → harness 가 메타 LLM (haiku) 1 호출:
     "다음 prose 의 결론은 PASS/FAIL/SPEC_MISSING 중 무엇? 한 단어."
  → 메타 LLM 답 = enum 1개. 파싱 trivial.
  → 시퀀스 진행 또는 retry/escalate
```

### 진실의 원천

- **issue_num** (또는 `LOCAL-N`): 워크플로우 식별자
- **prose 디렉토리** (`.claude/harness-state/<issue_num>/`): 모든 agent 의 prose 파일
- **메타 LLM 해석**: 매 단계 진행 시 prose 읽고 결론 + 다음 행동 판단

flag 0, schema 0, marker 0. agent 가 빠뜨릴 *형식 자체가 없음*.

### Handoff

다음 agent prompt 에 `.claude/harness-state/<issue>/` 디렉토리 명시. 다음 agent 가 이전 prose 자유 read. 별도 handoff payload 형식 없음.

### 작성 지침 예 (validator/code-validation.md)

```markdown
## 출력 작성 지침

검증 결과를 prose 로 작성. **형식 자유** (markdown / 평문 / 표).

다음 두 가지 **반드시 명확히**:

1. **결론** — 의미가 명확:
   - 통과 / 정상 / PASS — 코드가 계획과 일치
   - 실패 / FAIL — 불일치 항목 발견
   - 스펙 부족 / SPEC_MISSING — 계획 부재/모호

2. **이유** — 결론의 근거:
   - 파일 path + 라인 번호
   - 구체적 사실 (추측 금지)

harness 가 prose 의 *의미* 를 LLM 으로 해석.
```

### 비용

- 메타 LLM = haiku 1회 ~$0.001 (50 토큰 in + 5 토큰 out)
- agent 호출당 +1 메타 호출
- 13 agent × 평균 5 호출/cycle = 65 메타 호출 = **$0.065/cycle**
- agent 자체 비용 $0.07~$0.29 대비 미미 (~1%)

---

## 4. 충돌 분석

### 4.1 disallowedTools / ALLOW_MATRIX
- **무관**. agent 가 stdout emit, harness 가 캡처. agent 가 Write 도구 안 씀.
- 기존 ReadOnly agent (validator/pr-reviewer 등) disallowedTools 그대로 — Write 차단 보존
- ALLOW_MATRIX 도 기존 그대로 — 신규 path 추가 0

### 4.2 parse_marker 18 호출지
- 모두 `interpret_signal(issue_num, agent, expected_enum)` 으로 변환
- expected_enum = caller 가 정의 (예: `["PASS", "FAIL", "SPEC_MISSING"]`)
- 코드 변경 평균 ~5 LOC × 18 호출지 = ~90 LOC

### 4.3 generate_handoff / write_handoff
- 폐기. 다음 agent prompt 에 prose 디렉토리 path 만 명시.
- 코드 삭제 ~150 LOC

### 4.4 Flag 시스템
- `class Flag` enum + `flag_touch` / `flag_exists` / `flag_rm` 모두 폐기
- recovery state (force-retry, escalate_history, merge_cooldown) 는 *별도 메커니즘* 으로 보존:
  - `.claude/harness-state/<issue>/.attempts.json` 같은 단순 카운터 (메타 LLM 무관, retry 정책의 결정론 영역)
  - 또는 prose 파일 자체 mtime / 갯수로 attempt 추정
- 35 호출지 모두 변경 또는 삭제

### 4.5 agents/*.md (33 @OUTPUT 정의)
- @OUTPUT_SCHEMA / @OUTPUT_FILE / @OUTPUT_RULE 모두 삭제
- 대신 *작성 지침* 한 섹션 추가 (결론 + 이유 가이드)
- agent 자율 prose

### 4.6 preamble.md 자동 주입
- 폐기. agent prompt 별 *필요 사항만* 명시.
- `agent-config/*.md` 별 layer 도 통합

### 4.7 spec / architecture
- `docs/harness-spec.md` §3 I-2: 마커 강제 → "agent prose 자유 emit + 메타 LLM 해석"
- `docs/harness-architecture.md` §5: signal_io.py 메커니즘 명시
- PR title `[invariant-shift]`

### 4.8 CHG-14.1 (alias map) 정합성
- alias map = parse_marker 의 일부. parse_marker 폐기 시 자동 폐기.
- changelog 정정 (CHG-14.1 가치 폐기 명시)

---

## 5. Phase 분할 — 단순화

> 형식 + flag 폐기로 sub-phase 분할 의미 줄어듦. 기능별 묶음으로 단순화.

### Phase 1 — Foundation: signal_io + validator 1 모드 (1.5일)

**범위**: 가장 단순 case 로 발상 검증
- `harness/signal_io.py` 신규 (write_prose / interpret_signal / MissingSignal exception)
- `agents/validator/code-validation.md` writing guide 적용 (한 모드만)
- `harness/impl_loop.py:1339` parse_marker → interpret_signal (validator CODE_VALIDATION 1곳)
- ENV 게이트 `HARNESS_PROSE_VALIDATOR_CODE=1`

**Pre-flight (R4 PDCA)**:
- 진입 *전* 1 cycle 도그푸딩 baseline 측정 (alias hit 빈도, cache hit, poor_cache_util)

**Acceptance**:
- validator CODE_VALIDATION 호출 1곳이 prose + 메타 LLM 해석으로 통과
- ENV off 시 회귀 0
- 메타 LLM 비용 측정 (cycle 당 +$0.001 미만 예상)

### Phase 2 — Multi-Agent + Handoff + Flag 폐기 (1주)

**범위**: 13 agent 전체 확장 + handoff prose 직접 read + Flag 시스템 일괄 폐기
- 18 parse_marker 호출지 모두 interpret_signal
- 33 @OUTPUT 정의 → 작성 지침 변경
- generate_handoff / write_handoff 코드 삭제
- preamble.md 자동 주입 폐기, agent prompt 별 필요 사항만 명시
- agent-config/*.md → agents/*.md 통합 (디렉토리 삭제)
- Flag 시스템 폐기 (35 호출지 변경/삭제, recovery 는 .attempts.json 으로 분리)
- ENV 게이트 per agent (`HARNESS_PROSE_<AGENT>=1`) — 단순 → 복잡 순

**Acceptance**:
- parse_marker / generate_handoff / class Flag / preamble.md 모두 코드 0
- jajang 도그푸딩 1 cycle 무사고
- cache hit 97.3% → 98%+ (preamble 폐기 효과 — R11 control 측정)

### Phase 3 — GitHub 외부화 + Sweep (3일)

**범위**: 4 기둥 #2 정신 (CI 가 강제) + legacy 일괄 sweep
- `commit-gate.py` Gate 1 (gh issue/tracker mutate) → `.github/workflows/tracker-mutate-guard.yml`
- Gate 4 (doc-sync) → workflow
- Gate 5 (LGTM flag) → branch protection required reviewers
- Task-ID 형식 검증 → workflow regex
- ENV 게이트 (`HARNESS_PROSE_*`) 모두 제거
- changelog/rationale 정정 (CHG-14.1 폐기 명시)

### Phase 4 — Validation: 4 기둥 fitness 측정 (도그푸딩 1 cycle)

**측정 항목**:

| 4 기둥 | 측정 | 목표 |
|---|---|---|
| 컨텍스트 layer | CLAUDE.md + agents/*.md + ... | 5 → 2 |
| hook 갯수 | | 7 → 3 |
| LOC 순감소 | | 5000 → 2500~3000 |
| 형식 강제 호출지 | parse_marker / flag_touch / write_handoff | 0 |
| poor_cache_util 비용 | improve-token-efficiency | $507 → $200 미만 |
| jajang marker fragility | | 0건 |
| 메타 LLM 비용 | cycle 당 합 | < $0.10 |
| catastrophic 가드 | HARNESS_INFRA_PATTERNS / READ_DENY / plugin-write-guard | 무손실 |

---

## 6. Acceptance Criteria

### Phase 1
- [ ] `harness/signal_io.py` (write_prose / interpret_signal / MissingSignal) + 테스트
- [ ] validator CODE_VALIDATION 1 호출지 prose 흐름
- [ ] Pre-flight baseline 측정 데이터 보존
- [ ] ENV off 회귀 0

### Phase 2
- [ ] parse_marker 호출 0
- [ ] generate_handoff / write_handoff 코드 0
- [ ] class Flag 폐기 (recovery 는 .attempts.json)
- [ ] preamble.md 자동 주입 0
- [ ] agent-config/ 디렉토리 0
- [ ] cache hit ±2pp baseline 비교 (R11 control)

### Phase 3 — dcNess 적용 결과 (PHASE_3_DONE)
- [x] commit-gate.py Gate 1/4/5 코드 0 — *dcNess 자연 만족* (migration-decisions §2.2 — commit-gate.py DISCARD, 처음부터 미도입)
- [x] `.github/workflows/*` 3+ 신설 — `document-sync.yml` (`DCN-CHG-20260429-08`) + `python-tests.yml` (`-09`) + `plugin-manifest.yml` (`-10`) + `task-id-validation.yml` (`-20`) **= 4 워크플로 + branch protection (`-21`)**
- [x] ENV 게이트 (`HARNESS_PROSE_*`) 모두 제거 — *dcNess 자연 만족* (도입 0)
- [x] CHG-14.1 폐기 정정 — *RWHarness 영역* (dcNess 외, 본 acceptance 비대상)
- [x] **dcNess 한정 추가 acceptance**:
  - [x] Task-ID 형식 검증 게이트 (`DCN-CHG-20260429-20`)
  - [x] LGTM 게이트 외부화 = branch protection required reviewers (`-21`)
  - [x] 메타 LLM (haiku) interpreter 통합 = `harness/llm_interpreter.py` (`-22`) → **DISCARDED** (`DCN-CHG-20260430-04` heuristic-only 정착)
  - [x] heuristic-first + LLM-fallback 합성 + telemetry 분석기 (`-23`)
  - [x] plugin 배포 dry-run 가이드 = `docs/process/plugin-dryrun-guide.md` (`-24`)

### Phase 4
- [ ] 위 §5 Phase 4 측정 항목 모두 통과
- [ ] catastrophic 가드 무손실 (의도적 src/ 외 수정 → 차단 검증)

### 원칙 위반 측정 (모든 Phase 공통)
- [ ] 신규 강제 형식 0 (schema, required 키, flag 등)
- [ ] 신규 deny hook 0
- [ ] 룰 순감소 추세 (LOC + hook + flag 모니터링)

---

## 7. Out of Scope

- **검증자 인스턴스 격리** (subprocess) — 보존
- **Conditional workflow branch** (FAIL → SPEC_GAP → 재검증) — 보존
- **Recovery state** (force-retry, escalate_history, merge_cooldown) — 메커니즘 변경 (.attempts.json), 정책 보존
- **catastrophic hook 가드** (plugin-write-guard, HARNESS_INFRA_PATTERNS, READ_DENY_MATRIX, agent-boundary ALLOW_MATRIX) — 보존
- **GitHub-level audit** (changelog, rationale, Issue tracking) — 보존
- **agent_call subprocess 격리** — 보존
- **사용자 프로젝트용 deny-patterns.yaml** — 별도 epic
- **AI-readiness-cartography 스킬 채택** — 별도 작업

---

## 8. Risks

### R1. 메타 LLM 해석 모호성
- **시나리오**: agent prose 가 결론 명확히 안 적음 → 메타 LLM 답 모호 ("PASS or FAIL ambiguous")
- **대응**:
  - 1차: agent prompt 의 writing guide 명료화
  - 2차: 메타 LLM 답이 모호하면 사용자에게 prompt ("이 결과가 PASS 인가요?")
  - 3차: prose 분석 카탈로그 → 반복 패턴 발견 시 writing guide 추가 정정 (룰 X, 가이드 강화)
- **acceptance**: 모호 케이스 카탈로그 (`.metrics/ambiguous-prose.jsonl`) 누적. cycle 당 hit 5건 미만 목표.

### R2. prose 길이 폭증 → 메타 LLM 비용/지연
- **시나리오**: agent 가 너무 긴 prose emit → 메타 LLM input 토큰 증가
- **대응**:
  - writing guide 에 "결론은 첫 단락에 명시" 권고
  - 메타 LLM prompt 가 prose 의 *마지막 500 토큰* 만 전달 (결론은 보통 마지막)
  - 위반 시 (마지막 500 토큰에 결론 없음) writing guide 정정
- **acceptance**: 메타 LLM 평균 input < 500 토큰 측정.

### R3. Flag 폐기로 recovery state 손실 우려
- **시나리오**: force-retry / escalate_history 가 Flag 기반 — Flag 폐기 시 정책 깨짐
- **대응**:
  - Flag 의 *boolean* 부분만 `.claude/harness-state/<issue>/.attempts.json` 카운터로 대체
  - `{"plan_validation": 1, "code_validation": 2, ...}` 단순 dict
  - force-retry 시 카운터 청소 (PR #11 패턴 정합)
- **acceptance**: recovery 시나리오 회귀 테스트 통과 (force-retry, escalate, cooldown 각각).

### R4. CHG-14.1 (alias map) 폐기 직진 — A→D 점프 (PDCA 미준수)
- **사실**: alias map 도그푸딩 0 cycle 후 폐기 결정. 데이터 없는 결정.
- **대응**:
  - Phase 1 진입 *전* 1 cycle 도그푸딩 baseline 측정 (alias hit stderr 로그 빈도)
  - 0건 = 폐기 정당화. > 0 = 어느 변형이 hit 인지 카탈로그 후 writing guide 반영

### R5. cache hit 측정 control 부재
- **사실**: Phase 2 의 `cache hit 97.3% → 98%+` 측정이 다른 변경 (preamble 폐기, prose 흐름) 과 분리 불가능
- **대응**:
  - Phase 1 직전 baseline 측정 보존
  - Phase 2 후 treatment 측정
  - 차이 ±2pp 이내 = "preamble 폐기 효과 미검증" 명시

### R6. GitHub 외부화 피드백 지연
- **사실**: Phase 3 가 commit-gate Gate 1/4/5 → GitHub Actions. push 전 즉시 차단 → push 후 PR CI 실패 로 피드백 지점 이동.
- **대응**:
  - local pre-commit warning 으로 동일 룰 best-effort 검증 (차단 X, 알림만)
  - workflow fail-fast (regex 위반 즉시 fail, PR 분 단위 피드백)

### R7. checkpoint 시스템 정합성
- **사실**: `harness/plan_loop.py:51-89` `load_plan_checkpoint` + prose hash 게이트 (`_current_prd_hash` 등) 실재. 신규 흐름에서도 prose 가 진실의 원천.
- **대응**:
  - hash 대상은 *prose 파일 자체* (이미 그러함). 변경 0.
  - 단 hash 안정성 검증 — agent 가 prose 같은 의미 다른 표현 emit 시 hash 변동 → checkpoint miss 위험. 측정 필요.

### R8. 메타 LLM rate limit / 비용 폭증 (성공 시)
- **사실**: cycle 당 65 호출은 미미하지만 도그푸딩 누적 시 일/주 단위 비용 측정 필요
- **대응**:
  - 메타 LLM 호출 카탈로그 (`.metrics/meta-llm-calls.jsonl`) 누적
  - 주간 비용 리포트 (improve-token-efficiency 와 결합)
  - 폭증 시 메타 LLM 호출 빈도 조정 (e.g. 같은 prose 결과 캐싱)

---

## 9. Inputs (구현자 먼저 읽을 자료)

| 파일 | 왜 |
|---|---|
| `docs/harness-spec.md` | invariant 헌법 |
| `harness/core.py:551-680` (parse_marker + MARKER_ALIASES) | 폐기 대상 |
| `harness/core.py:175-210` (class Flag) | 폐기 대상 |
| `harness/core.py:2040, 2150` (generate_handoff, write_handoff) | 폐기 대상 |
| `harness/core.py:990+` (preamble 자동 주입) | 폐기 대상 |
| `agents/validator/code-validation.md` | writing guide 1차 적용 대상 |
| `hooks/agent-boundary.py` | 보존 (catastrophic) |
| W0 PoC 결과 + jha0313 비교 (대화 로그) | 발상 진화 컨텍스트 |
| `orchestration/changelog.md` HARNESS-CHG-20260428-09 / -14.1 | 폐기될 reactive 패치들 |

---

## 10. 적용 모드

본 proposal 은 **신규 프로젝트 (lightharness 등) 에서 메인 Claude 직접 작업** 모드. RWHarness 가드 미적용 + CHG 시스템만 도입. architect/validator/engineer 위임 강제 없음.

RWHarness 자체엔 적용 안 함 — 본 proposal 은 신규 프로젝트의 development input.

---

## 11. Fork-and-Refactor Development Guide (다른 프로젝트 에이전트 입력)

### 11.1 신규 프로젝트 정체성

- **이름 후보**: `lightharness`, `dcNess` 등 (사용자 결정)
- **정체성**:
  > "Claude 의 disobedience 를 외부 process 로 결정론화하는 *최소 레이어*. 강제는 (1) 작업 순서, (2) 접근 영역만. 형식 / flag / schema 0. agent prose 자유 + 메타 LLM 해석."
- **vs RWHarness**:
  - 결정론 메커니즘: parse_marker / Flag → prose + 메타 LLM
  - 컨텍스트: 5 layer → 2 layer
  - hook: 7 → 3 (catastrophic 만)
  - GitHub 외부화 (commit-gate Gate 1/4/5)
  - LOC: 5000 → ~2500

### 11.2 신규 architect 의 모듈 분류 framework

신규 프로젝트 진입 시 메인 Claude 가 RWHarness 를 read 후 *각 모듈을 자율 분류*. 본 proposal 은 결정 표 박지 않음 (§2.5 원칙 3 정합).

각 모듈 3 질문:
1. **Catastrophic-prevention 인가?** — jajang 도그푸딩 12 PR 의 *돌이킬 수 없는 사고* 를 막는가? → 보존
2. **형식 강제로 자연 폐기되는가?** — prose + 메타 LLM 적용 시 의미 잃는가? → 폐기 후보
3. **단순화 가능한가?** — 룰 누적 패턴인가? → 리팩터링 후보

분류 결과는 `docs/migration-decisions.md` 에 기록.

### 11.3 RWHarness Read 권한 부여 메커니즘

- **`--add-dir`**: `claude --add-dir /Users/dc.kim/project/RWHarness` 또는 `.claude/settings.json` 영구 등록
- **Bash 직접 path**: prompt 에 절대 path 명시

가드는 RWHarness 화이트리스트 밖이라 차단 0.

### 11.4 도입할 것 / 도입 안 할 것 / 안전망

> **대 원칙 정합** (§2.5): 작업 순서 + 접근 영역만 제어.
> **본 §11.4 의 *적용 SSOT*** = [`docs/orchestration.md`](orchestration.md) (`DCN-CHG-20260429-25`).

#### 도입할 것
- **작업 순서 강제**: 시퀀스 (validator → engineer → pr-reviewer) + retry 정책 (사용자 프로젝트 적용 시) → `docs/orchestration.md` §2/§4/§5
- **접근 영역 강제**: agent-boundary ALLOW/READ_DENY + plugin-write-guard (사용자 프로젝트 적용 시) → `docs/orchestration.md` §7
- **추적**: orchestration/{changelog, rationale}.md (HARNESS-CHG-* 1부터, 4섹션) + PR `[invariant-shift]` 토큰 + Task-ID gh action 검증 + Document-Exception escape hatch

#### 도입 안 할 것
- **출력 형식 강제** (marker / status JSON / @OUTPUT_SCHEMA 일체)
- **handoff 형식** (next_actions[] 같은 구조 강제)
- **Flag 시스템** (boolean flag 파일)
- **preamble 자동 주입**
- **schema / alias map / parse_marker 사다리**
- **architect/validator/engineer 위임 사이클** (신규 plugin 빌드 중)
- **commit-gate hook Gate 1/4/5** → GitHub Actions

#### 안전망
- **Sub-phase 마다 smoke test**: 실제 RWHarness 호출 1~2회 동작 검증
- **매 sub-phase squash merge 후 `improve-token-efficiency` 측정**: 회귀 시 즉시 rollback
- **메타 LLM 비용 모니터링**: cycle 당 합 측정
- **Escape hatch**: 결정 막힐 때 architect 명시 호출 (옵션)

### 11.5 RWHarness 와의 동기화 룰 (drift 방지)

- 신규 프로젝트 PR 마다 RWHarness 의 *최근 commit* 확인. catastrophic fix 발견 시 cherry-pick.
- `orchestration/changelog.md` 에 cherry-pick 출처 명시.
- Phase 4 통과 후 RWHarness frozen — drift 신경 안 써도 됨.

---

## 12. RWHarness → 신규 Plugin 전환 절차

### 12.1 사전 검증 (현재 시스템 상태)

- RWHarness 설치: `~/.claude/plugins/cache/realworld-harness/realworld-harness/0.1.0-alpha/`
- 활성 화이트리스트: `~/.claude/harness-projects.json` (현재 4 프로젝트)
- 플러그인 매니저: `claude plugin {install|uninstall|disable|enable|list|marketplace}`
- 플러그인 명 형식: `<plugin>@<marketplace>`

### 12.2 신규 Plugin 빌드 (Phase 1~4 후)

```bash
cat lightharness/.claude-plugin/plugin.json   # name + version
claude plugin validate lightharness/.claude-plugin
```

### 12.3 단계적 전환 (RWHarness 보존 + 비교)

#### 12.3.1 신규 marketplace 등록
```bash
claude plugin marketplace add /path/to/lightharness/.claude-plugin
# 또는: claude plugin marketplace add github:alruminum/lightharness
```

#### 12.3.2 신규 plugin 설치 + 충돌 회피
```bash
claude plugin install lightharness@lightharness
claude plugin disable realworld-harness@realworld-harness  # 충돌 회피
claude plugin list
```

#### 12.3.3 활성 프로젝트 분기
```bash
cp ~/.claude/harness-projects.json ~/.claude/harness-projects.json.bak
# 1 프로젝트 (jajang) 만 신규 plugin 으로 도그푸딩
python3 ~/.claude/skills/improve-token-efficiency/scripts/analyze_sessions.py \
  --sessions-dir ~/.claude/projects/-Users-dc-kim-project-jajang
```

#### 12.3.4 통과 시 RWHarness 완전 제거
```bash
claude plugin disable realworld-harness@realworld-harness
claude plugin enable lightharness@lightharness
# 1~2 cycle 도그푸딩 추가 검증
claude plugin uninstall realworld-harness@realworld-harness
rm -rf ~/.claude/plugins/cache/realworld-harness
rm -rf ~/.claude/plugins/marketplaces/realworld-harness
claude plugin marketplace remove realworld-harness
```

#### 12.3.5 즉시 롤백 시나리오
```bash
claude plugin disable lightharness@lightharness
claude plugin enable realworld-harness@realworld-harness
cp ~/.claude/harness-projects.json.bak ~/.claude/harness-projects.json
```

### 12.4 보존 데이터

- `~/.claude/harness-projects.json` — 화이트리스트
- `~/.claude/projects/-Users-*/` — 세션 jsonl
- `~/.claude/projects/-Users-*/memory/` — auto memory
- 프로젝트별 `.claude/harness-state/` — 신규 plugin 도 같은 디렉토리 사용 권장

### 12.5 Acceptance — 전환 완료 기준

- [ ] 1 프로젝트 1 cycle 도그푸딩 무사고
- [ ] 추가 1 프로젝트 1 cycle 도그푸딩 무사고
- [ ] cache hit / poor_cache_util RWHarness baseline 대비 동등 또는 개선
- [ ] 형식 강제 사고 (marker fragility) 0건
- [ ] catastrophic 가드 작동 검증 (의도적 src/ 외 수정 → 차단)
- [ ] 메타 LLM 비용 cycle 당 < $0.10
- [ ] 롤백 절차 1회 dry-run 검증
- [ ] RWHarness 완전 uninstall 후 7일 무사고

### 12.6 작업 권한 매트릭스

- 신규 프로젝트 빌드 = 메인 Claude 직접 (가드 미적용)
- RWHarness 자체는 frozen
- plugin install/uninstall = 사용자 명시 명령 시에만
