# PROGRESS

## 현재 상태

- **🌲 Worktree 격리 옵션 C** (`DCN-CHG-20260429-39`):
  - `harness/session_state.py` `_default_base()` γ 설계 — `git rev-parse --git-common-dir` 로 main repo `.claude/harness-state/` 를 단일 source. cwd 별 캐시. 비-git 폴백 보존.
  - `commands/quick.md` / `commands/product-plan.md` Step 0a — keyword (`worktree` / `wt` / `격리` / `isolate`) 트리거 시 EnterWorktree, 종료 step 에 ExitWorktree 옵션.
  - `docs/conveyor-design.md` §13 신규 — 옵션 검토 (A/B/C/D) + γ 설계 + skill protocol + EnterWorktree 룰 정합.
  - 신규 5 테스트 (전체 165/165 PASS).
  - v2 후속: 자동 cleanup / PR merge 감지 / 옵션 D 디폴트 마이그레이션.
- **🧪 Conveyor 인프라 Step 4 — multi-session e2e smoke** (`DCN-CHG-20260429-35`):
  - `tests/test_multisession_smoke.py` 신규 (11 케이스):
    - bash 훅 파이프라인 (4) — 실 subprocess 호출 + 부수효과 검증
    - 멀티세션 격리 (3) — 두 cc_pid by-pid / live.json 격리 + 동시 Popen race 검증
    - catastrophic 룰 e2e (4) — engineer/pr-reviewer/HARNESS_ONLY 차단 + 통과 매트릭스
  - 신규 11 테스트 (전체 160/160 PASS).
  - 한계: 실 Claude Code 환경의 PPID 신뢰성 / stdin payload 형식 = 별도 manual smoke follow-up.
- **🚀 Conveyor 인프라 Step 3 — 훅 인프라** (`DCN-CHG-20260429-34`):
  - `harness/hooks.py` (~280 LOC) — Python 훅 핸들러 (SessionStart + PreToolUse Agent)
  - `hooks/session-start.sh` + `hooks/catastrophic-gate.sh` — bash 래퍼 (PPID 캡처 + python 호출)
  - `hooks/hooks.json` — plugin 활성 시 자동 등록 (RWHarness 패턴 정합)
  - HARNESS_ONLY_AGENTS (engineer / validator-PLAN/CODE/BUGFIX_VALIDATION) + §2.3 4룰 (1/3/4) 강제
  - 신규 28 테스트 (전체 149/149 PASS).
- **🚀 Conveyor 인프라 Step 2 — `session_state.py` 확장 (by-pid 레지스트리 + CLI)** (`DCN-CHG-20260429-33`):
  - by-pid 레지스트리 함수 8개 (`.by-pid/{cc_pid}` sid 매핑 + `.by-pid-current-run/{cc_pid}` rid 매핑) — 멀티세션 정합 핵심.
  - PPID chain walker (`os.getppid()` → bash → `ps` → CC main pid) — 환경변수 휘발성 우회.
  - CLI subcommand 5개 (`init-session/begin-run/end-run/begin-step/end-step`) — argparse 진입점.
  - 신규 20 테스트 (전체 121/121 PASS).
- **📐 Conveyor 디자인 v2 — `docs/conveyor-design.md` rewrite** (`DCN-CHG-20260429-32`, PR #31 머지):
  - PR #29 v1 (Python `run_conveyor`) 폐기 후 Task tool + Agent + helper + 훅 패턴 채택.
  - 12 절 모두 갱신. 멀티세션 by-pid 레지스트리 layout 명시.
  - 폐기 사유 = subagent 호출이 Python 안에서 일어나면 PreToolUse 훅 미발화 + 사용자 가시성 0 + 메인 자율도 0.
- **🚀 Conveyor 인프라 Step 1 — `harness/session_state.py` 신규** (`DCN-CHG-20260429-30`):
  - OMC `SkillActiveStateV2` (active_runs map, soft tombstone, heartbeat) + RWH `_meta` envelope + 3-tier resolution (글로벌 폴백 제외) + atomic write (O_EXCL+fsync+rename+dir fsync, 0o600) 차용.
  - 14 함수 export — session_id 검증/추출/resolution, session pointer R/W, run_id 생성, atomic_write, session_dir/run_dir/live_path, read_live/update_live, start_run/update_current_step/complete_run, cleanup_stale_runs.
  - 49 신규 테스트 (전체 101/101 PASS).
  - **컨베이어 spec** (`docs/conveyor-design.md` PR #29) 의 첫 코드 구현. 후속 Task 들 (-31 impl_driver / -32 SessionStart hook / -33 catastrophic-gate hook) 의 인프라 기반.
- **🎯 Conveyor 디자인 spec — `docs/conveyor-design.md`** (`DCN-CHG-20260429-29`, PR #29 머지):
  - 메인 클로드 = 시퀀스 결정자, 컨베이어 = 멍청한 순회기, catastrophic = PreToolUse 훅. 12 절 660 줄.
  - PR #28 (옵션 c JSON 결정자) close 후 새 spec. proposal §2.5 (prose-only) 정합.
- 거버넌스 시스템 부트스트랩 완료 (`DCN-CHG-20260429-01`, PR #1 머지)
- 프로젝트 루트 `CLAUDE.md` + 루트 정책 파일 게이트 분류 추가 (`DCN-CHG-20260429-02`)
- **Plugin 배포 인프라**: `.claude-plugin/{plugin,marketplace}.json` (`DCN-CHG-20260429-04`)
  - 이름 = `dcness`, 버전 = `0.1.0-alpha`. RWHarness 와 공존 가능 설계.
- **모듈 분류 framework 적용**: `docs/migration-decisions.md` (`DCN-CHG-20260429-05`)
- **CI 게이트 3종**: Document Sync (`-08`) / Python tests (`-09`) / Plugin manifest (`-10`)
- **README + AGENTS 보강**: `-11`, `-12`
- **🎉 Phase 2 iter 5 (FINAL) — ux-architect + product-planner prose-only** (`DCN-CHG-20260429-19`):
  - `agents/ux-architect.md` (UX_FLOW_READY / UX_FLOW_PATCHED / UX_REFINE_READY / UX_FLOW_ESCALATE) — UX_FLOW + UX_SYNC + UX_SYNC_INCREMENTAL + UX_REFINE 4 모드 inline + Anti-AI-Smell + 카테고리 클리셰 회피 + 라이트/다크 두 모드 의무 + Outline-First
  - `agents/product-planner.md` (PRODUCT_PLAN_READY / CLARITY_INSUFFICIENT / PRODUCT_PLAN_CHANGE_DIFF / PRODUCT_PLAN_UPDATED / ISSUES_SYNCED) — Phase 1 (요구사항) + Phase 2 (기능 스펙) + Phase 3 (4 옵션 스코프) + Diff-First 변경 처리 + ISSUE_SYNC
  - **Phase 2 종결**: 13 agent docs 모두 prose-only 변환 완료 (validator iter 0 + 4 read-only iter 1 + 8 architect iter 2 + 2 engineer/test-engineer iter 3 + 2 designer/critic iter 4 + 2 ux/planner iter 5)
- **🚀 Phase 2 iter 4 — designer + design-critic prose-only** (`DCN-CHG-20260429-18`):
  - `agents/designer.md` (DESIGN_READY_FOR_REVIEW / DESIGN_LOOP_ESCALATE) — 2×2 매트릭스 (SCREEN/COMPONENT × ONE_WAY/THREE_WAY) 4 모드 + Phase 0 (이슈 생성, Pencil 캔버스) + Phase 1 (variant 생성) + Phase 4 (DESIGN_HANDOFF, outline-first) + 차별화 의무 + View 전용 원칙
  - `agents/design-critic.md` (VARIANTS_APPROVED / VARIANTS_ALL_REJECTED / UX_REDESIGN_SHORTLIST) — 4 기준 (UX 명료성·미적 독창성·컨텍스트 적합성·구현 실현성) 각 10점, 총 40점, PASS 28+ 기준
- **🚀 Phase 2 iter 3 — engineer + test-engineer prose-only** (`DCN-CHG-20260429-17`):
  - `agents/engineer.md` (IMPL_DONE / SPEC_GAP_FOUND / IMPLEMENTATION_ESCALATE / TESTS_FAIL / POLISH_DONE) — Phase 1 스펙 검토 + Phase 2 구현 + 듀얼 모드 + DESIGN_HANDOFF + 재시도 한도 + 커밋 단위 룰
  - `agents/test-engineer.md` (TESTS_WRITTEN / SPEC_GAP_FOUND) — TDD attempt 0 전용, src/ 읽기 금지 (catastrophic-prevention), impl `## 생성/수정 파일` 경로만 사용
- **🚀 Phase 2 iter 2 — architect 8 docs prose-only** (`DCN-CHG-20260429-16`):
  - `agents/architect.md` (마스터, 7 모드 인덱스 + Outline-First 자기규율 + TRD 현행화 룰)
  - `agents/architect/system-design.md` (SYSTEM_DESIGN_READY)
  - `agents/architect/module-plan.md` (READY_FOR_IMPL — depth/design frontmatter, DB 영향도 분석, 듀얼 모드 가드레일)
  - `agents/architect/spec-gap.md` (SPEC_GAP_RESOLVED / PRODUCT_PLANNER_ESCALATION_NEEDED / TECH_CONSTRAINT_CONFLICT)
  - `agents/architect/task-decompose.md` (READY_FOR_IMPL — Outline-First, 듀얼 모드 가드레일)
  - `agents/architect/tech-epic.md` (SYSTEM_DESIGN_READY)
  - `agents/architect/light-plan.md` (LIGHT_PLAN_READY — bugfix / DESIGN_HANDOFF / REVIEW_FIX / DOCS_UPDATE)
  - `agents/architect/docs-sync.md` (DOCS_SYNCED / SPEC_GAP_FOUND / TECH_CONSTRAINT_CONFLICT)
  - 모두 prose writing guide. `---MARKER:X---` 텍스트 마커 + `@OUTPUT` JSON schema + preamble / agent-config 별 layer 의존 폐기.
- **🚀 Phase 2 iter 1 — 4 read-only agents prose-only** (`DCN-CHG-20260429-15`):
  - `agents/pr-reviewer.md` (LGTM / CHANGES_REQUESTED) — validator 와 역할 분리, 스코프 매트릭스, 레거시 처리
  - `agents/plan-reviewer.md` (PLAN_REVIEW_PASS / PLAN_REVIEW_CHANGES_REQUESTED) — 8 차원 (현실성·MVP·제약·UX·숨은가정·경쟁·BM·기술실현)
  - `agents/qa.md` (FUNCTIONAL_BUG / CLEANUP / DESIGN_ISSUE / KNOWN_ISSUE / SCOPE_ESCALATE) — 역질문 루프, MCP+tracker CLI 폴백
  - `agents/security-reviewer.md` (SECURE / VULNERABILITIES_FOUND) — OWASP Top 10 + WebView 특화
  - 모두 prose writing guide 형식. `---MARKER:X---` 텍스트 마커 + `@OUTPUT_*` JSON schema + preamble 자동주입 / agent-config 별 layer 의존 모두 폐기.
- **🧹 stale 참조 sweep** (`DCN-CHG-20260429-14`): CLAUDE.md test 명령어 + python-tests.yml 헤더 + marketplace.json description/tags + .gitignore 코멘트 + migration-decisions framework 표현을 prose-only 로 정정. history record 항목은 governance §2.4 스코핑 정합으로 미수정.
- **🔄 Phase 1 재정렬 — Prose-Only Pattern** (`DCN-CHG-20260429-13`):
  - **proposal 갱신**: `docs/status-json-mutate-pattern.md` 가 *Prose-Only Pattern* 으로 정정. 형식 강제 자체가 사다리를 부른다는 자각 — JSON schema 도 형식 사다리의 한 형태. harness 강제 = 작업 순서 + 접근 영역만, 그 외는 agent 자율.
  - **폐기**: `harness/state_io.py` (~290 LOC) + `tests/test_state_io.py` (32) + `tests/test_validator_schemas.py` (9). JSON schema 강제 자체가 형식 사다리 잠재.
  - **신규**: `harness/signal_io.py` (~290 LOC) — `write_prose` / `read_prose` / `interpret_signal` (휴리스틱 + DI swap) / `MissingSignal` (3 reason).
  - **테스트**: `tests/test_signal_io.py` 29 PASS — round-trip / path 화이트리스트 / 휴리스틱 (단어경계·case-insensitive·다중매칭) / DI / clear_run_state.
  - **validator agent docs 6 재작성**: `@OUTPUT_*` 형식 강제 제거 → prose writing guide. 각 모드별 결론 enum 만 명시 (PASS / FAIL / SPEC_MISSING / ESCALATE 등).
  - 메타 LLM (haiku) 통합은 `interpreter=` DI swap point 로 남김 — 후속 Task-ID.

## TODO

### Phase 1 — Foundation (prose-only) ✅
모든 acceptance 항목 완료. dcNess 메인 작업 모드(`status-json-mutate-pattern.md` §11.4) 정합으로 RWHarness `harness/core.py` 의 parse_marker 호출지 / agent-boundary hook ALLOW_MATRIX / `_AGENT_DISALLOWED` 변경은 본 저장소엔 미도입 (plugin 배포 시점 사용자 프로젝트 가드용).

### Phase 2 — 메타 LLM 통합 + 다른 12 agent docs (진행 중)

**다음 iteration 시작점**: `git log --oneline` + 본 PROGRESS 의 진행도 확인 후 다음 묶음 picker.

- [ ] Anthropic SDK 통합 — `interpret_signal` 의 메타 LLM interpreter 구현 (haiku, cycle 당 비용 측정 — proposal R8)
- [ ] ambiguous prose 카탈로그 — `MissingSignal(ambiguous)` raise 시 `.metrics/ambiguous-prose.jsonl` 누적 (proposal R1 acceptance)
- [ ] 다른 agent docs 를 prose writing guide 로 변환:
  - [x] **iter 1 완료** (DCN-CHG-20260429-15): `agents/pr-reviewer.md`, `agents/plan-reviewer.md`, `agents/qa.md`, `agents/security-reviewer.md`
  - [x] **iter 2 완료** (DCN-CHG-20260429-16): `agents/architect.md` + 7 mode sub-doc
  - [x] **iter 3 완료** (DCN-CHG-20260429-17): `agents/engineer.md` + `agents/test-engineer.md`
  - [x] **iter 4 완료** (DCN-CHG-20260429-18): `agents/designer.md` (4 모드 inline) + `agents/design-critic.md`
  - [x] **iter 5 완료** (DCN-CHG-20260429-19): `agents/ux-architect.md` + `agents/product-planner.md` — Phase 2 13 agents 종결 🎉

### Phase 3 — GitHub 외부화 + Sweep ✅ (종결, 5/5 iter)

> proposal §5 Phase 3 정합 — RWHarness `commit-gate.py` Gate 1/4/5 → GitHub Actions 외부화.
> dcNess 는 commit-gate.py 미도입(migration-decisions §2.2 DISCARD)이라 *자연 외부화* — 신규 워크플로우만 추가.
> proposal §6 의 4 acceptance 모두 PASS (자연 만족 2 + 신규 1 + 비대상 1) + dcNess 한정 추가 5 항목 모두 PASS.

- [x] **iter 1 완료** (DCN-CHG-20260429-20): Task-ID 형식 검증 워크플로 + 스크립트 — `scripts/check_task_id.mjs` + `.github/workflows/task-id-validation.yml`. 모든 비-머지 커밋이 `DCN-CHG-YYYYMMDD-NN` 토큰 정확히 1개 포함하는지 PR/push 단위로 차단. PR title 도 동시 검증. 머지 커밋 면제(squash 합본). proposal §11 4-pillar #2 (CI 최후 차단) 정합.
- [x] **iter 2 완료** (DCN-CHG-20260429-21): branch protection 적용 스크립트 + 가이드 — `scripts/setup_branch_protection.mjs` (멱등 PUT, dry-run 지원) + `docs/process/branch-protection-setup.md` (자동/수동/검증) + `governance.md` §2.8 신설. proposal §5 Phase 3 "Gate 5 (LGTM flag) → branch protection required reviewers" 외부화. RWHarness `class Flag` LGTM in-process 메커니즘은 dcNess 자연 폐기 (migration-decisions §2.2 DISCARD), GitHub branch protection 이 동일 역할 외부 강제. 4 status check (`Document Sync gate` / `unittest discover` / `validate manifest` / `Task-ID format gate`) + 1 approving review + force-push/삭제 차단 + linear history.
- [x] **iter 3 완료** (DCN-CHG-20260429-22): Anthropic SDK haiku interpreter 통합 — `harness/llm_interpreter.py` (신규, `make_haiku_interpreter()` 팩토리, mock client DI 지원, telemetry `.metrics/meta-llm-calls.jsonl`, ambiguous fallback) + `tests/test_llm_interpreter.py` (16 케이스, 실 SDK 호출 0). `harness/signal_io.py` 의 `interpret_signal(..., interpreter=)` swap point 가 프로덕션 가능 상태. proposal §3 비용 (~$0.0001/호출) + R8 telemetry 누적.
- [x] **iter 4 완료** (DCN-CHG-20260429-23): heuristic-first + LLM-fallback 합성 전략 + telemetry 분석기 — `harness/interpret_strategy.py` (신규, `interpret_with_fallback()` 합성, outcome 5종 telemetry) + `tests/test_interpret_strategy.py` (7 케이스) + `scripts/analyze_metrics.mjs` (heuristic + LLM JSONL 집계, outcome 분포 / 비용 / 모델별 / allowed enum 별 / 최근 ambiguous 샘플 5개 / Phase 4 fitness 목표 자동 판정). `tests/test_llm_interpreter.py` 의 telemetry_dir 누락 3 케이스 fix (cwd `.metrics/` 오염 회피). 52/52 PASS. proposal R1 (ambiguous 카탈로그) + R8 (cycle 당 비용 측정) + §5 Phase 4 fitness 측정 인프라 완성.
- [x] **iter 5 완료** (DCN-CHG-20260429-24): Phase 3 종결 + `docs/process/plugin-dryrun-guide.md` (신규 — proposal §12 절차 풀어쓴 운영 가이드, 11 섹션: 사전검증 → manifest → marketplace → 충돌회피 → smoke test → 1 cycle 도그푸딩 → 완전 제거/롤백 → acceptance → Phase 4 후속). `docs/status-json-mutate-pattern.md` §6 Phase 3 acceptance 4 항목 모두 PASS 표시 (자연 만족 2 + 신규 워크플로 1 + RWHarness 외 1) + dcNess 한정 5 항목 추가 PASS.
- [x] **사후 보강** (DCN-CHG-20260429-25): **오케스트레이션 SSOT** — `docs/orchestration.md` 신규 작성. RWHarness `harness-spec.md` §4.2 (게이트 시퀀스) + §4.3 (진입 경로) + `harness-architecture.md` §3 (호출 권한 + Write/Read 가드 + INFRA_PATTERNS) 통합. 11 섹션 (정체성·적용모드·게이트시퀀스 mermaid·진입경로 mini graph 6개·결론 enum 결정표·retry 한도·escalate 카탈로그·핸드오프 매트릭스·catastrophic vs 자율·코드 driver 보류 옵션 a/b/c·proposal 인용). 형식 강제 어휘 (`---MARKER---` / `_handoffs/` / `class Flag`) 모두 dcNess prose + signal_io 표현으로 변환. proposal §2.5 원칙 4 + §11.4 직접 인용. Phase 1~3 작업 (agents/*.md / signal_io / 거버넌스) 의 *시퀀스 정의 spec* 부재를 보강 — 사용자 지적 정합. 옵션 (c) Orchestration Agent + 동적 시퀀스 (parameter-driven, 메타 LLM 동적 갱신, catastrophic backbone 강제) 신규 발상으로 §9 에 박음.
- [x] **사후 보강** (DCN-CHG-20260429-26): **agents/*.md 형식 어휘 일괄 폐기** — 외부 review 지적 반영. `@MODE:X:Y` 헤더 메타 / `@PARAMS:` JSON 블록 / `@CONCLUSION_ENUM:` 라인 / `@OUTPUT JSON schema` 본문 메모를 24 파일 모두에서 자연어로 변환. 177 → 0 hit. 헤더 메타 블록 → "**모드** / **결론** / **호출자가 prompt 로 전달하는 정보**" 자연어 3 라인. 표 안 `@MODE:` 접두사 → mode 이름만 남김. "폐기된 컨벤션 (참고)" 본문은 *원리 보존* + 형식 어휘 제거 (proposal §2.5 정합 명시). 형식 사다리 부활 risk 차단.
- [x] **사후 보강** (DCN-CHG-20260429-27): **agents/*.md 자율성 강화 일괄 정리** — proposal §2.5 정신 (작업 순서 + 접근 영역만 강제, 그 외 agent 자율) 정합으로 24 파일 압축. **4350 → 1683 줄 (61% 감소)**, 모든 파일 ≤ 150 줄. 변환 6 원칙: (A) frontmatter = 자기인식 → "🔴 정체성" 강박 섹션 + "절대 출력 금지 패턴" list 폐기 → 1 줄 메타. (B) 원칙 1 줄 + 자율 판단. (C) Phase/Step 강박 → "수행 흐름 (자율 조정 가능)" 1 단락. (D) 산출물 마크다운 템플릿 → "정보 의무 (형식 자유)" 권고만. (E) 결론 enum 예시 반복 → 헤더 1 회. (F) 다중 체크리스트 → catastrophic 1~2 + 권고 prose. 페르소나 1~2 줄 압축. Anti-AI-Smell 가치 메타는 1 단락 압축. 폐기된 컨벤션 섹션 제거 (orchestration.md / status-doc 참조로 대체). 모든 파일 끝에 cross-link 1 단락. 코드 변경 0, 회귀 0.

### Phase 3 acceptance 매핑 표

| proposal §6 Phase 3 항목 | dcNess 결과 | 근거 |
|---|---|---|
| commit-gate.py Gate 1/4/5 코드 0 | ✅ 자연 만족 | migration-decisions §2.2 — commit-gate.py DISCARD |
| `.github/workflows/*` 3+ 신설 | ✅ **4 워크플로** | document-sync(`-08`) + python-tests(`-09`) + plugin-manifest(`-10`) + task-id-validation(`-20`) + branch protection 룰(`-21`) |
| ENV 게이트 (`HARNESS_PROSE_*`) 모두 제거 | ✅ 자연 만족 | dcNess 도입 0 |
| CHG-14.1 폐기 정정 | ✅ 비대상 | RWHarness 영역 |
| (dcNess 추가) Task-ID 형식 검증 | ✅ | `DCN-CHG-20260429-20` |
| (dcNess 추가) LGTM 외부화 | ✅ | `-21` (branch protection) |
| (dcNess 추가) haiku interpreter | ✅ | `-22` |
| (dcNess 추가) heuristic-fallback + analyzer | ✅ | `-23` |
| (dcNess 추가) plugin dry-run 가이드 | ✅ | `-24` |

### Phase 4 — 4 기둥 fitness 측정 (다음)

> proposal §5 Phase 4 진입 전제: Phase 1~3 모두 PASS (✅ 본 PR 머지 후 충족).

- [ ] 컨텍스트 layer 5 → 2 측정 (CLAUDE.md + agents/*.md + AGENTS.md + ...)
- [ ] hook 갯수 7 → 3 (catastrophic 만) — dcNess 자연 만족 (hooks/ 디렉토리 0)
- [ ] LOC 순감소 5000 → 2500~3000 (RWHarness baseline 비교)
- [ ] 형식 강제 호출지 0 (parse_marker / flag_touch / write_handoff) — dcNess 자연 만족
- [ ] poor_cache_util 비용 $507 → $200 미만 (improve-token-efficiency 측정)
- [ ] 메타 LLM cycle 당 < $0.10 (analyzer fitness PASS — 본 Phase 3 인프라 완성)
- [ ] catastrophic 가드 무손실 (의도적 src/ 외 수정 → 차단 검증)
- [ ] **plugin 배포 dry-run** (`docs/process/plugin-dryrun-guide.md` §1~§9 절차 실행)

### 인프라 / CI 보강
- [ ] branch protection 룰 추가 (사용자 수동, GitHub Settings)
- [ ] CLAUDE.md §6 환경변수 — 도입 시 갱신

## Blockers
- 없음
