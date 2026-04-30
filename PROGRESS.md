# PROGRESS

## 현재 상태

- **✂️ loop-procedure.md split + 300줄 cap 룰 신설** (`DCN-CHG-20260430-30`):
  - 사용자 지시 — "loop-procedure.md 쪼개자 가급적 300라인 넘기지 말랬잖아 행동지침 md는 이것도 룰로 적어놔줘". loop-procedure.md (436줄) cap 위반.
  - **`docs/loop-catalog.md` 신규** (239줄) — 8 loop 행별 풀스펙 (allowed_enums / 분기 / sub_cycles / branch_prefix). loop-procedure.md §7.0 인덱스 + §7.1~§7.10 풀스펙 모두 이전.
  - **`docs/loop-procedure.md` 슬림** (436 → 242줄) — Step 0~8 mechanics 만 보존. §7 = catalog cross-ref + catastrophic 룰 정합 1 항목.
  - **`docs/process/dcness-guidelines.md` §0 갱신** — 2 SSOT 분담 (procedure + catalog) 명시. §0.1 신설 — **행동지침 md 300줄 cap 룰** (대상 / 대상 외 / Why / How to apply / 현재 알려진 위반).
  - **`docs/orchestration.md` §3 헤더** — loop-catalog.md cross-ref 추가.
  - **알려진 위반**: orchestration.md (540줄). split 후속 별도 Task-ID 예정.
- **🔌 helper finalize-run --auto-review + qa.md slim pilot** (`DCN-CHG-20260430-29`):
  - 4 PR migration (skill 슬림화 + procedure SSOT) 의 PR3.
  - `harness/session_state.py:_cli_finalize_run` 에 `--auto-review` flag 추가. STATUS JSON 출력 직후 in-process 로 `harness.run_review.main(["--run-id", rid, "--repo", cwd])` 호출. 메인 Claude 가 finalize-run 부르면 review 자동 piggy-back — 의도적 skip 불가.
  - 실패 케이스 (review_main 예외) 안전망 — `AUTO_REVIEW_FAIL` stderr WARN + STATUS JSON 자체는 정상 출력 + exit 0.
  - `commands/qa.md` slim pilot — 127줄 → 28줄 (78% 절감). `qa-triage` loop / Inputs / 후속 라우팅 추천만. 절차는 [`docs/loop-procedure.md`](docs/loop-procedure.md) §1~§6 + §7.5 cross-ref.
  - `tests/test_session_state.py` 3 신규 (`auto_review_chains_report` / `skip_on_failure` / `off_no_chain`) PASS. 219 ran / 217 PASS / 2 pre-existing flaky 무관.
  - PR4 후속 — 4 skill (quick / impl / impl-loop / product-plan) bulk slim.
- **📐 loop-procedure.md §7 매트릭스 행별 풀스펙 보강** (`DCN-CHG-20260430-28`):
  - PR1 (DCN-30-27) self-test gap 반영. §7.0 한눈 인덱스 + §7.1~§7.8 행별 풀스펙 sub-section. 각 행 = `branch_prefix` decision rule / `Step 4.5 적용` / Step 별 `allowed_enums` 표 / 분기 표 / sub_cycles. 252줄 → 436줄.
  - feature-build-loop 분기 (PRODUCT_PLAN_UPDATED skip / UX_REFINE_READY / CLARITY_INSUFFICIENT 등) 명시.
  - impl-ui-design-loop design-critic 별도 step 분리 + DESIGN_LOOP_ESCALATE / VARIANTS_ALL_REJECTED 분기.
  - ux-design-stage / ux-refine-stage designer mode (THREE_WAY 권장) + 사용자 PICK / Step 2.5 사용자 승인.
  - sub_cycle agent (architect:SPEC_GAP / engineer:POLISH-<n> / engineer:IMPL-RETRY-<n> / designer:SCREEN-ROUND-<n>) allowed_enums 명시.
- **📑 loop-procedure.md SSOT 신설 + cross-ref** (`DCN-CHG-20260430-27`):
  - skill 5종 Step 0~7 *실행 절차* 중복 (100~215줄/skill) 풀어내는 4 PR migration 의 1단계.
  - `docs/loop-procedure.md` (252줄) — 8 loop 공통 실행 절차 SSOT (Step 0 worktree+begin-run / Step 1 TaskCreate / Step 2~N agent 호출 / Step 4.5 stories sync / Step 7 finalize-run+clean+commit-PR / Step 8 review).
  - 8 loop name 확정: `feature-build-loop` / `impl-batch-loop` / `impl-ui-design-loop` / `quick-bugfix-loop` / `qa-triage` / `ux-design-stage` / `ux-refine-stage` / `direct-impl-loop`.
  - `docs/process/dcness-guidelines.md` §0 cross-ref + 의무 read 명시. `docs/orchestration.md` §3 헤더 8 loop name 매핑.
- **📜 dcness-guidelines.md SSOT + SessionStart 훅 inject** (`DCN-CHG-20260430-26`):
  - 사용자 지적 — quick.md (light path 전용) 에 범용 룰 다 박혀 책임 혼재. + 미래 추가 룰 (Epic/Story 분할, 커스텀 루프) SSOT 필요.
  - `docs/process/dcness-guidelines.md` (신규) — 11 섹션 (가시성 / Step 기록 / **/run-review 의무 (신규)** / **결과 출력 룰 (신규)** / yolo / AMBIGUOUS / worktree / TBD 분할 기준 / TBD 커스텀 루프 / 권한 요청 / Karpathy 참조).
  - `hooks/session-start.sh` — 활성 프로젝트 게이트 통과 후 guidelines.md 내용을 system-reminder 로 inject (RWHarness review-inject 패턴 정합). CC 매 세션 자동 인지 + plugin 비활성 시 발화 X.
  - `commands/quick.md` — 380줄 → 215줄 슬림화. 범용 룰 cross-ref 만.
  - 미래 룰 추가 = 본 SSOT 1 파일에만 append.
- **🛡️ Step 기록 안전망 — drift/count WARN + skill SSOT 강화** (`DCN-CHG-20260430-25`):
  - jajang DCN-30-23 사후 분석 — engineer 자체 PR 만든 후 메인이 end-step skip → .steps.jsonl 누락 사단.
  - helper 측: `_cli_end_step` drift detector (current_step ≠ args.agent → stderr WARN) + `finalize-run --expected-steps N` row count 검증.
  - `commands/quick.md` SSOT: `## Step 기록 룰` 절 신규 — Agent ↔ begin/end-step 1:1 의무 + POLISH 네이밍 컨벤션 + 안티패턴 4건 + helper 안전망 cross-ref.
  - `commands/impl.md` Step 7 — `--expected-steps 5` 박음.
  - 신규 4 테스트. 자동 보정 X (안전) — WARN 으로 메인 사후 인지.
- **🕐 /run-review 단계별 표에 local time 시각 컬럼** (`DCN-CHG-20260430-24`):
  - 사용자 디버그 시 UTC `04:xx` 가 헷갈려 보고. `.steps.jsonl` 은 UTC ISO 저장 (시스템 표준), render 측만 `astimezone()` 변환해서 KST 표시.
- **🩹 /run-review 매칭 fix + skill prompt 의 prose-file 격리** (`DCN-CHG-20260430-23`):
  - jajang 실측 (run-657d86fc, 9 step) 발견 2 결함 동시 fix.
  - **(1) 매칭 cascade 결함**: step 0 invocation 부재 시 후속 step 모두 어긋남 (9 중 2 매칭). timestamp-proximity 기반 매칭 (inv.ts < step.ts AND step.ts - inv.ts ≤ 600s, closest before) 으로 해결 → 9 중 8 매칭 (step 0 정당 미매칭).
  - **(2) prose-file 세션 격리 X**: skill prompt 가 `/tmp/dcness-*.md` 고정 path 사용 → 멀티세션 race / stale prose 잔여로 helper 가 옛 enum 추출. `dcness-helper run-dir` subcommand 신규 + skill prompt 4개 (`quick` / `product-plan` / `impl` / `qa`) 가 `<run_dir>/.prose-staging/<step>.md` 사용. multisession 자동 격리.
  - 신규 5 테스트 (AssignInvocationsTests timestamp / missing-first / unmatched-after-step + run-dir CLI). 209/211 PASS (2 pre-existing flaky 무관).
- **🌀 /run-review Phase 2 — THINKING_LOOP 검출 + per-Agent metrics** (`DCN-CHG-20260430-20`):
  - 사용자 jajang 실측 사례 (product-planner 6분 elapsed + ↓624 tokens stall) 자동 검출.
  - CC session JSONL `toolUseResult.usage.output_tokens` + `totalDurationMs` per-Agent 매칭 (순서 + agent name).
  - `EXPECTED_AGENT_BUDGETS` 12 agent 표 (elapsed_s + min_output_tokens).
  - THINKING_LOOP — duration > budget × 1.5 + output < budget × 0.3 (또는 5분 + 1k 절대 한도).
  - StepRecord 필드 4 추가 (duration_ms / output_tokens / total_tokens / cost_usd / matched_invocation).
  - 단계별 표 컬럼 5 추가 (duration / out_tok / total_tok / cost / matched).
  - 신규 8 테스트 (NormalizeAgentTypeTests / AssignInvocationsTests / ThinkingLoopDetectionTests). 23/23 PASS.
- **🔍 /run-review skill — 메타-하네스 self-improvement Phase 1** (`DCN-CHG-20260430-19`):
  - RWHarness `harness-review.py` 의 dcness 변환. dcness conveyor run 사후 분석.
  - `harness/run_review.py` (~370 LOC) — `.steps.jsonl` + per-agent prose 파싱 → 잘한 점 5 패턴 + 잘못한 점 8 패턴 detection + run-level cost (CC session JSONL 합산).
  - 잘한 점: `ENUM_CLEAN` / `PROSE_ECHO_OK` (DCN-30-15) / `DDD_PHASE_A` (DCN-30-16) / `DEPENDENCY_CAUSAL` / `EXTERNAL_VERIFIED_PRESENT` (DCN-30-18).
  - 잘못한 점: `RETRY_SAME_FAIL` / `ECHO_VIOLATION` / `PLACEHOLDER_LEAK` / `MUST_FIX_GHOST` / `SPEC_GAP_LOOP` / `INFRA_READ` / `READONLY_BASH` / `EXTERNAL_VERIFIED_MISSING`. 오늘 박은 룰 자동 회귀 검출.
  - `commands/run-review.md` skill prompt — character-for-character 출력 룰 (RW 패턴 정합).
  - 신규 15 테스트 PASS. dcness skill 9 개.
  - Phase 2 후속: per-Agent cost 매칭 (`toolUseResult.totalCost`), finalize-run 자동 트리거, 30일 누적 분석.
- **🪄 MODULE_PLAN_READY 마커 → state-aware skip** (`DCN-CHG-20260430-13`):
  - 사용자 통찰 — RWHarness plan_loop 의 원래 의도 (산출물 있으면 통과 / 없으면 다시 호출) 복원.
  - `agents/architect/task-decompose.md` — 각 batch 산출 시 ## 생성/수정 파일 / ## 인터페이스 / ## 의사코드 / ## 결정 근거 + `MODULE_PLAN_READY` 마커 박는 컨벤션.
  - `commands/impl.md` Step 2.0 — batch 파일 마커 grep → SKIP_MODULE_PLAN 시 batch 파일을 architect-MODULE_PLAN.md 자리에 cp + test-engineer 직진. catastrophic §2.3.3 정합.
  - 분기 추가 = 1 (grep 1줄). branch-surface-tracking warning 임계 미달.
  - 옵션 D — 컨벤션 + 메인 자율. dcness 철학 정합.
- **🧷 /impl-loop inner sub-task 의무 + `b<i>.<agent>` prefix 컨벤션** (`DCN-CHG-20260430-12`):
  - 사용자 smoke 발견 — 메인이 inner 5 sub-task TaskCreate inline skip → outer 5 batch entry 만 보임.
  - `commands/impl-loop.md` Step 2 에 ⚠️ "skip 금지" 경고 + `b<i>.<agent>` prefix 컨벤션 박음.
  - `commands/impl.md` Step 1 도 같은 강도 강조.
  - 사용자 가시성 기대 형식 (◼ b1.architect: MODULE_PLAN 등) 그대로 default 화.
- **👀 가시성 보강 — 결론 섹션 우선 + 메인 text echo** (`DCN-CHG-20260430-11`):
  - `_extract_prose_summary` 가 `## 결론` / `## Summary` / `## 변경 요약` 섹션 우선 추출. cap 12줄/1200char.
  - 5 skill (qa / quick / product-plan / impl / impl-loop) 에 "가시성 룰" 신규 — 매 Agent 후 메인 text reply 로 prose 핵심 5~12줄 echo (CC collapsed 회피).
  - 사용자 manual smoke 피드백 (ctrl+o 의존) 에 두 채널 동시 보강. 신규 5 테스트. 185/185 PASS.
  - PR split (#51 PROGRESS fragment + #52 본체) — commit 분할 사고. 두 PR 합쳐 -11 완성.
- **💰 /efficiency skill — jha0313/skills_repo 흡수** (`DCN-CHG-20260430-08`):
  - `harness/efficiency/` 패키지 (4 script fork from `improve-token-efficiency`) + `scripts/dcness-efficiency` wrapper + `commands/efficiency.md` skill prompt.
  - dcness fix 2건: encode_repo_path 의 `.` → `-` (CC 실 인코딩 룰 정합), price_for prefix 매칭 (dated suffix / variant tag 흡수).
  - 4 지표 점수화 (Cache utilization 40% + Output density 20% + Read redundancy 20% + Tool economy 20%) + Pareto + 6 절감 휴리스틱.
  - 신규 10 테스트 (`test_efficiency.py`). 181/181 PASS.
  - dcness skill 8 개: /init-dcness /qa /quick /product-plan /impl /impl-loop /smart-compact /efficiency.
- **🔁 /impl + /impl-loop skill 신규** (`DCN-CHG-20260430-06`):
  - `/impl` — per-batch 정식 impl 루프 (architect MODULE_PLAN → test-engineer → engineer IMPL → validator CODE_VALIDATION → pr-reviewer + clean 자동 commit/PR + yolo + worktree).
  - `/impl-loop` — multi-batch sequential auto chain (각 batch 마다 /impl 호출 + clean 자동 진행 + caveat 멈춤).
  - /product-plan TASK_DECOMPOSE 산출 batch list 의 후속 진입점. 5 sub-task per batch 가시화 — 사용자 manual smoke 지적 정합.
  - dcNess plugin skill 7개 됨: /qa /quick /product-plan /smart-compact /init-dcness /impl /impl-loop.
- **🔍 DESIGN_VALIDATION step 추가** (`DCN-CHG-20260430-05`):
  - orchestration §3.1 mermaid + §2.3.5 catastrophic 룰 + §4.9 결정표 갱신.
  - /product-plan Step 6.5 신규 (validator DESIGN_VALIDATION) + cycle 한도 2.
  - hooks.py §2.3.5 검사 (architect TASK_DECOMPOSE + SYSTEM_DESIGN.md 존재 시 DESIGN_REVIEW_PASS 필수).
  - 신규 5 테스트 (`CatastrophicDesignValidationTests`). 171/171 PASS.
  - 사용자 manual smoke 발견 — validator/design-validation.md agent 정의는 있는데 orchestration 시퀀스에서 호출 자리 빠져있던 갭 메움.
- **🧹 heuristic-only 정착 + dead code 제거** (`DCN-CHG-20260430-04`):
  - `harness/llm_interpreter.py` + `tests/test_llm_interpreter.py` 삭제 (dead code, 호출 경로 0).
  - `interpret_with_fallback` 의 `llm_interpreter=` 인자 제거 — heuristic-only.
  - `signal_io.py` docstring 정정 ("프로덕션 = haiku" → "프로덕션 = heuristic-only").
  - `docs/status-json-mutate-pattern.md` §0 정착 박스 추가 (heuristic-only 4 이유 + 트렌드 위치).
  - 트렌드 위치 재정의: RWH [2024 regex] → proposal 원안 [2025 메타 LLM] → **dcness 정착 [2025+ heuristic-only + 메인 cascade]** → [2026 structured output].
  - anthropic SDK 의존 0, 도그푸딩 API_KEY 불필요.
  - 166/166 PASS (이전 184 - 18 = LLM 관련 테스트 삭제).
- **🤖 Helper-side automation foundation** (`DCN-CHG-20260430-02`):
  - `dcness-helper end-step` 이 enum 추출 후 prose 첫 5~8줄 stderr 자동 출력 — CC collapsed 회피, 모든 skill 가시성 자동 ↑.
  - `dcness-helper finalize-run` 신규 — `.steps.jsonl` append-only 로그 집계 → JSON status (has_ambiguous / has_must_fix / step enum 매트릭스). skill 이 clean 판정용으로 소비.
  - `dcness-helper auto-resolve` 신규 — yolo 모드 폴백 매트릭스. UX_FLOW_ESCALATE → UX_FLOW_PATCHED 등 권장 액션 JSON.
  - `/quick` Step 7 = 7a clean 자동 commit/PR (graceful degrade) + 7b caveat 확인. worktree squash 흡수 자동 검사 (`git diff main..wt-branch -- :^.claude` 빈 줄이면 discard_changes=true).
  - yolo keyword (yolo / auto / 끝까지 / 막힘 없이 / 다 알아서) — `/quick` `/product-plan` 둘 다 적용. catastrophic 훅 (§2.3) 은 hard safety 보존.
  - 신규 9 테스트 (`HelperAutomationTests`). 184/184 PASS.
  - PR2 후속: validator DESIGN_VALIDATION 추가 + `/impl` `/impl-loop` skill.
- **🔧 Skill bash PYTHONPATH wrapper** (`DCN-CHG-20260429-41`):
  - `scripts/dcness-helper` 신규 — BASH_SOURCE 기반 자기위치 추출 → PYTHONPATH 자동 설정. CLAUDE_PLUGIN_ROOT 의존 0.
  - 4 skill (`qa` / `quick` / `product-plan` / `init-dcness`) 의 helper 호출 일괄 wrapper 경유로 변경.
  - Manual smoke (`/qa`) 첫 helper 호출 ModuleNotFoundError 해결.
- **🚪 Plugin 활성화 게이트 + cross-project PYTHONPATH** (`DCN-CHG-20260429-40`):
  - `harness/session_state.py` — `is_project_active` / `enable_project` / `disable_project` + 4 CLI subcommand. plugin-scoped whitelist (`~/.claude/plugins/data/dcness-dcness/projects.json`) — CC `data/` 컨벤션 정합 + 글로벌 `~/.claude/` 오염 0.
  - hook 양쪽 (`hooks/session-start.sh` `hooks/catastrophic-gate.sh`) — PYTHONPATH=$CLAUDE_PLUGIN_ROOT prepend + `is-active` 게이트 (inactive 프로젝트 즉시 exit 0). hook 자체는 모든 프로젝트에서 호출되지만 dcness 미활성 프로젝트는 import 비용도 0.
  - `commands/init-dcness.md` 신규 — `/init-dcness` skill (현재 cwd 활성화 + 안내).
  - 신규 10 테스트 (`ProjectActivationTests`). 175/175 PASS.
  - manual smoke 사용자 발견에서 출발 — dcness install 후 hook 미발화 + cross-project ModuleNotFoundError. 두 문제 동반 해결.
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
