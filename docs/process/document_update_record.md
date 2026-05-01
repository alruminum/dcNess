# Document Update Record (WHAT log)

> 본 파일은 dcNess 프로젝트 모든 변경 작업의 **WHAT** (무엇을 바꿨나) 로그.
> 규칙 정의: [`governance.md`](governance.md) §2.3 / §2.6 (재기술 금지).

## 형식

```
### {Task-ID}
- **Date**: YYYY-MM-DD
- **Change-Type**: spec | agent | harness | hooks | ci | test | docs-only (복수 가능)
- **Files Changed**:
  - path/to/file.md
  - path/to/code.ts
- **Summary**: 한 줄 요약
- **Document-Exception** (있을 때만): 예외 사유
```

---

## Records

### DCN-CHG-20260502-04
- **Date**: 2026-05-02
- **Change-Type**: agent | docs-only
- **Files Changed**:
  - `commands/impl.md`
  - `commands/impl-loop.md`
  - `commands/product-plan.md`
  - `commands/qa.md`
  - `commands/run-review.md`
  - `agents/architect/task-decompose.md`
  - `agents/architect/module-plan.md`
  - `agents/architect/spec-gap.md`
  - `agents/engineer.md`
  - `agents/validator/design-validation.md`
  - `docs/loop-catalog.md`
  - `docs/loop-procedure.md`
  - `docs/orchestration.md`
  - `docs/process/dcness-guidelines.md`
  - `docs/process/manual-smoke-guide.md`
  - `docs/process/document_update_record.md`
  - `docs/process/change_rationale_history.md`
  - `README.md`
- **Summary**: "batch" 용어 전면 제거 — impl 단위를 "task"로 통일 (Epic→Story→Task 계층 정합), 루프명 `impl-batch-loop` → `impl-task-loop`
- **Note**: governance 파일은 PR #104(선행 커밋)에서 갱신됨. Document-Exception: 실제 파일 치환 커밋 — governance 동반 파일은 선행 커밋에서 완료.

### DCN-CHG-20260502-03
- **Date**: 2026-05-02
- **Change-Type**: hooks
- **Files Changed**:
  - `hooks/session-start.sh`
  - `docs/process/document_update_record.md`
  - `docs/process/change_rationale_history.md`
  - `PROGRESS.md`
- **Summary**: session-start inject 절대 경로 버그 수정 — Read 도구는 절대 경로만 허용, CLAUDE_PROJECT_DIR로 동적 절대 경로 구성.

### DCN-CHG-20260502-02
- **Date**: 2026-05-02
- **Change-Type**: harness + docs-only
- **Files Changed**:
  - `harness/loop_insights.py` (신규)
  - `harness/session_state.py` (begin-step 주입 + finalize-run --accumulate)
  - `docs/loop-procedure.md` (§3.1 강제 문구)
  - `tests/test_loop_insights.py` (신규)
  - `docs/process/document_update_record.md` (본 항목)
  - `docs/process/change_rationale_history.md`
  - `PROGRESS.md`
- **Summary**: loop-insights 누적·주입 — 루프 종료 시 redo-log + WASTE/GOOD → agent별 .claude/loop-insights/<agent>.md 누적, begin-step 에서 stdout 주입.

### DCN-CHG-20260502-01
- **Date**: 2026-05-02
- **Change-Type**: hooks
- **Files Changed**:
  - `hooks/session-start.sh`
  - `docs/process/document_update_record.md`
  - `docs/process/change_rationale_history.md`
  - `PROGRESS.md`
- **Summary**: session-start inject BLOCKING 게이트 강화 — 단순 지시 → 출력 금지 조건 + 검증 토큰 + 예외 없음 명시 3원칙.

### DCN-CHG-20260501-18
- **Date**: 2026-05-01
- **Change-Type**: hooks + docs-only
- **Files Changed**:
  - `hooks/session-start.sh`
  - `docs/process/dcness-guidelines.md`
  - `docs/process/document_update_record.md`
  - `docs/process/change_rationale_history.md`
- **Summary**: lazy-load v2 — inject의 lazy 섹션 파일경로 제거, dcness-guidelines.md §0 링크 비활성화. 경로 나열 자체가 read 트리거였음.

### DCN-CHG-20260501-17
- **Date**: 2026-05-01
- **Change-Type**: hooks + docs-only
- **Files Changed**:
  - `hooks/session-start.sh`
  - `docs/process/dcness-guidelines.md`
  - `commands/impl.md`
  - `commands/quick.md`
  - `commands/product-plan.md`
  - `commands/impl-loop.md`
  - `commands/qa.md`
  - `docs/process/document_update_record.md`
  - `docs/process/change_rationale_history.md`
  - `PROGRESS.md`
- **Summary**: session-start inject lazy-load 최적화 — 5 docs 즉시 read → dcness-guidelines.md 만 즉시, 나머지 4개 skill 진입 시 lazy. 감시자 Hat dcness-guidelines.md §13으로 이전.

### DCN-CHG-20260501-16
- **Date**: 2026-05-01
- **Change-Type**: docs-only
- **Files Changed**:
  - `docs/loop-procedure.md`
  - `docs/process/document_update_record.md`
- **Summary**: loop-procedure §3.1~§3.2 — prose auto-staging 반영, 메인 Write 지시 제거

### DCN-CHG-20260501-15
- **Date**: 2026-05-01
- **Change-Type**: harness, test
- **Files Changed**:
  - `harness/hooks.py`
  - `harness/session_state.py`
  - `tests/test_hooks.py`
  - `tests/test_session_state.py`
  - `docs/process/document_update_record.md`
  - `docs/process/change_rationale_history.md`
  - `PROGRESS.md`
- **Summary**: PostToolUse hook prose auto-staging — tool_response.text → run_dir 자동 저장, end-step --prose-file optional

### DCN-CHG-20260501-14
- **Date**: 2026-05-01
- **Change-Type**: harness, test
- **Files Changed**:
  - `harness/signal_io.py`
  - `harness/session_state.py`
  - `harness/run_review.py`
  - `tests/test_run_review.py`
  - `tests/test_session_state.py`
- **Summary**: prose_file 필드로 `.steps.jsonl` ↔ prose 직접 연결 — `_resolve_prose_path()` 삭제

### DCN-CHG-20260501-13
- **Date**: 2026-05-01
- **Change-Type**: harness, hooks, test
- **Files Changed**:
  - `harness/agent_trace.py` (`histogram` + `last_agent_id` helper 추가)
  - `harness/sub_eval.py` (신규 — anomaly 룰 + auto decision)
  - `harness/hooks.py` (`handle_posttooluse_agent` 확장 — histogram inject + auto redo_log)
  - `hooks/post-agent-clear.sh` (stdout JSON 통과 — 코멘트 갱신)
  - `tests/test_sub_eval.py` (신규 — 10 case)
  - `tests/test_agent_trace.py` (HistogramTests + LastAgentIdTests — 6 case)
  - `tests/test_hooks.py` (PostToolUseAgentHistogramTests — 5 case)
  - `docs/process/document_update_record.md` (본 항목)
  - `docs/process/change_rationale_history.md`
  - `PROGRESS.md`
- **Summary**: PR-3 — surface 개선 (jajang 메인 자기 진단 반영). 권고 어휘 한계 인지 → push 형태로 전환. PostToolUse Agent hook 가 sub 종료 후 (1) `agent-trace` 집계 → tool histogram 계산 → `additionalContext` 로 메인 다음 turn 의 Agent tool result 옆에 시스템 reminder 자동 inject (2) anomaly 룰 (tool_uses<2 / 같은 tool 5+회 / Write 약속+Write 0건 = prose-only) 검출 → ⚠️ 강조 메시지 + REDO 권고 (3) `redo_log` 1줄 자동 append (auto:true 마커). 메인은 자연스럽게 보고 + 필요 시 별도 1줄로 결정 덮어쓰기. 룰 추가 X, surface 풍부화 ✅. 회귀 0 — 324 → 345 tests OK.

### DCN-CHG-20260501-12
- **Date**: 2026-05-01
- **Change-Type**: hooks, agent
- **Files Changed**:
  - `hooks/session-start.sh` (additionalContext 에 "감시자 Hat" 섹션 추가 — 권고 어휘, 형식 강제 X)
  - `commands/audit-redo.md` (신규 skill — redo-log + agent-trace 결합 분석, Layer 1/2 후보 제안)
  - `docs/process/document_update_record.md` (본 항목)
  - `docs/process/change_rationale_history.md`
  - `PROGRESS.md`
- **Summary**: PR-2 — PR-1 인프라 위에 운영 layer 얹기. SessionStart 메시지에 "builder + 감시자 hat 우선 / sub completion 결과 깐깐 평가 / redo-log 1줄 append 권고 / 루프 재구성 자유" 안내. `/audit-redo` skill 신규 — `(sub, mode)` 별 redo 분포 + REDO 사유 클러스터 + trace 공통 패턴 → Layer 1 (현 프로젝트 1차 prompt 첨가) + Layer 2 (`agents/*.md` 영구 patch) 후보 제안. 룰 추가 X, prompt 풍부화 ✅.

### DCN-CHG-20260501-11
- **Date**: 2026-05-01
- **Change-Type**: harness, hooks, test
- **Files Changed**:
  - `harness/redo_log.py` (신규 — sub cycle 평가 audit log append/read/tail)
  - `harness/agent_trace.py` (신규 — sub 행동 trace append/read/tail)
  - `harness/hooks.py` (`handle_pretooluse_file_op` boundary 통과 시 trace pre append + `handle_posttooluse_file_op` 신규 + CLI subcommand 추가)
  - `hooks/post-file-op-trace.sh` (신규 — PostToolUse Edit/Write/Read/Bash wrapper)
  - `hooks/hooks.json` (PostToolUse Edit/Write/Read/Bash matcher 등록)
  - `tests/test_redo_log.py` (신규 — 15 case)
  - `tests/test_agent_trace.py` (신규 — 11 case)
  - `tests/test_hooks.py` (`FileOpTraceTests` + `PostToolUseFileOpTests` 신규 — 9 case)
  - `docs/process/document_update_record.md` (본 항목)
  - `docs/process/change_rationale_history.md`
  - `PROGRESS.md`
- **Summary**: PR-1 — sub 행동 사후 추적 인프라. PreToolUse/PostToolUse hook 가 sub 내부 `Edit/Write/Read/Bash` 호출마다 `agent-trace.jsonl` 1줄 append (boundary 통과 시만). 메인이 sub completion notification 평가 후 `redo-log.jsonl` 에 PASS/REDO 결정 1줄 기록 (PR-2 에서 SessionStart 메시지 + skill 추가). *행동* 만 cover — thinking / 중간 message 추적은 미래 P7 (`.output` 가공 helper). 토큰 비용 0 (hook LLM context 외부). 신규 35 case + 전체 324 tests OK / 회귀 0.

### DCN-CHG-20260501-10
- **Date**: 2026-05-01
- **Change-Type**: harness, test
- **Files Changed**:
  - `harness/run_review.py` — `_has_positive_must_fix` import (session_state). `parse_steps()` 가 `prose_full` 보유 시 `_has_positive_must_fix(prose_full)` 로 must_fix 재계산. 부재 시 jsonl `must_fix` fallback. retro 분석 정확도 회복.
  - `tests/test_run_review.py` — `test_parse_steps_recomputes_must_fix_from_prose` (legacy stale jsonl + 신규 prose negation → False 정정) + `test_parse_steps_must_fix_falls_back_to_jsonl` (prose 부재 fallback).
  - `docs/process/document_update_record.md` (본 항목)
  - `docs/process/change_rationale_history.md`
  - `PROGRESS.md`
- **Summary**: DCN-CHG-20260501-09 forward-only 한계 보강. 자장 run-ef6c2c00 (이전 PR 머지 *전* 작성된 stale jsonl) 재 review 시 MUST_FIX_GHOST 6 → 0 retro 회복 직접 검증. 290 ran / all PASS.

### DCN-CHG-20260501-09
- **Date**: 2026-05-01
- **Change-Type**: harness, agent, test, ci
- **Files Changed**:
  - `scripts/check_python_tests.sh` — pre-commit hook 안에서 git env vars (`GIT_INDEX_FILE` / `GIT_DIR` / `GIT_WORK_TREE` / `GIT_PREFIX` / `GIT_EXEC_PATH`) inherited → 자식 `git worktree add` fail 회귀 해소. `env -u <vars>` 로 unset 후 unittest 실행.
  - `harness/run_review.py` — `_resolve_prose_path()` 신규 (`.prose-staging/<bN.agent-mode>.md` Nth occurrence 매칭). `parse_steps` 가 occurrence_counter 로 같은 (agent, mode) N번째 staging 파일 매칭. fallback = legacy `<run_dir>/<agent>-<mode>.md`.
  - `harness/session_state.py` — `_MUST_FIX_NEGATION_RE` + `_has_positive_must_fix()` 신규 (라인 단위 negation 컨텍스트 검사). `_append_step_status` 의 must_fix 검출 + `prose_excerpt` cap 4 → 12 (5~12 룰 정합).
  - `agents/engineer.md` — H1 직후 `> ⚠️ CRITICAL — extended thinking 본문 드래프트 금지` banner 추가 (architect sub-mode 7 + product-planner 패턴 동일 적용).
  - `tests/test_run_review.py` — `ResolveProsePathTests` 5 신규 (Nth occurrence / fallback / no mode / bare suffix / parse_steps end-to-end).
  - `tests/test_session_state.py` — `test_must_fix_negation_no_false_positive` (자장 실 케이스 3) + `test_must_fix_positive_still_detected` (positive 3 케이스, mixed 포함).
  - `docs/process/document_update_record.md` (본 항목)
  - `docs/process/change_rationale_history.md`
  - `PROGRESS.md`
- **Summary**: 자장 run-ef6c2c00 (40 step, $118.73, 28 waste finding) /run-review 결과 검증 — 4 이슈 한 번에 fix. (1) MISSING_SELF_VERIFY 9건 false positive = parser path mismatch (skill `.prose-staging/` write vs parser legacy `<run_dir>/` read). (2) MUST_FIX_GHOST 6건 false positive = "MUST FIX 0" / "MUST FIX 없음" 부정문 매칭. (3) THINKING_LOOP 4건 (614s/1102s/429s/670s stall) engineer banner 부재. (4) prose_excerpt cap 4 vs 룰 5~12 mismatch. 신규 7 테스트 / 288 ran / all PASS.

### DCN-CHG-20260501-08
- **Date**: 2026-05-01
- **Change-Type**: agent (commands/ 는 미분류이지만 사용자 가시 skill 변경 → governance trail 정책 정합)
- **Files Changed**:
  - `commands/init-dcness.md` — Step 2.5 신규 (`~/.claude/settings.json` 의 `.permissions.allow` 에 `Read(~/.claude/plugins/cache/dcness/**)` jq append). settings 부재 시 신규 생성. 멱등 (이미 존재 시 skip). jq 미설치 시 WARN. 재설치 시 settings 보존 안내 추가.
  - `docs/process/document_update_record.md` (본 항목)
  - `docs/process/change_rationale_history.md`
- **Summary**: 사용자 보고 — SessionStart 훅이 plugin cache (`~/.claude/plugins/cache/dcness/**`) 안 SSOT 를 inject 해도 메인 Claude 가 read 권한 부재로 못 읽음. acceptEdits 모드라도 plugin cache 는 디폴트 차단 → init-dcness 가 활성화 시 명시 allow append. 멱등 jq merge 3 케이스 (existing / empty allow / no permissions) 모두 PASS 직접 검증.

### DCN-CHG-20260501-07
- **Date**: 2026-05-01
- **Change-Type**: ci, spec
- **Files Changed**:
  - `scripts/check_python_tests.sh` (신규) — staged 파일이 `harness/` / `tests/` / `agents/` / `python-tests.yml` 매칭 시만 `python3 -m unittest discover -s tests`. CI 환경 (`GITHUB_ACTIONS`) skip. 우회 시 `--no-verify` (룰 위반).
  - `scripts/hooks/pre-commit` — chain 화 (doc-sync + pytest).
  - `scripts/hooks/cc-pre-commit.sh` — `git commit` 매칭 case 안 doc-sync 통과 후 pytest 게이트 추가.
  - `docs/process/governance.md` §2.7 — 강제 메커니즘 표 신설 (게이트 / 스크립트 / 적용 범위 / 우회). 참조 파일 표에 `check_python_tests.sh` 추가.
  - `CLAUDE.md` §1 (commit 직전 단계) + 문서 지도 — 2 게이트 명시.
  - `docs/process/document_update_record.md` (본 항목)
  - `docs/process/change_rationale_history.md`
  - `PROGRESS.md`
- **Summary**: 사용자 요청 ("pytest 도 강제 못해?") 정합. doc-sync 패턴 그대로 — paths 분기 (옵션 B) 채택. 비매칭 commit 비용 0, 매칭 시 ~3초. branch protection 미사용 환경에서 mechanical 차단 확장.

### DCN-CHG-20260501-06
- **Date**: 2026-05-01
- **Change-Type**: ci, spec
- **Files Changed**:
  - `.github/workflows/python-tests.yml` — paths 필터 복구 (`harness/**` / `tests/**` / `agents/**` / 본 yml). docs-only PR 불필요 실행 회피.
  - `.github/workflows/plugin-manifest.yml` — paths 필터 복구 (`.claude-plugin/**` / `scripts/check_plugin_manifest.mjs` / 본 yml).
  - `docs/process/governance.md` §2.8 — "Branch Protection (CI 게이트 강제)" → "Branch Protection (현재 비활성)". 비활성 사유 / 도입 옵션 / 머지 룰 / 근거 재작성. doc-sync 만 실질 강제.
  - `docs/process/branch-protection-setup.md` — header 에 ⚠️ OFF 상태 명시 + 옵션 도구 안내.
  - `scripts/setup_branch_protection.mjs` — JSDoc header 에 비활성 상태 명시. 스크립트 자체 보존 (재활성용).
  - branch protection live 폐기 (`DELETE repos/alruminum/dcNess/branches/main/protection`) — `gh api` 200 → `Branch not protected` 확인.
  - `docs/process/document_update_record.md` (본 항목)
  - `docs/process/change_rationale_history.md`
  - `PROGRESS.md`
- **Summary**: DCN-CHG-20260501-04 (branch protection 도입) revert. 사용자 의도는 doc-sync 수준 mechanical 차단이지 CI 4 checks 전부 강제 아님 — 사용자 명령 ("pytest CI 적용") 을 과해석한 결과 protection 켜고 paths 필터 폐기까지 동반. 본 task 로 (1) protection OFF (2) paths 필터 복구. doc-sync 는 §2.7 3중 hook 으로 commit 시점 차단 유지. 나머지 CI 게이트는 paths 매칭 시만 발화 + 표시 레벨.

### DCN-CHG-20260501-05
- **Date**: 2026-05-01
- **Change-Type**: agent
- **Files Changed**:
  - `agents/architect/task-decompose.md` — `## impl 파일 명명 + H1 제목` 섹션 신규. 파일명 `impl/NN-<slug>.md` + H1 `# impl/NN — [Story Xa / #issue] <요약>` 강제. 자가 검증 regex 박음. 기존 `## 각 impl 파일 형식 의무` (내용 섹션) 와 짝.
  - `agents/engineer.md` — `## 커밋 단위 규칙` 안에 `### 1 batch = 1 PR` 하위 섹션 추가. impl batch 의 PR 은 코드 + impl spec + stories.md tick 1 셋트로 묶음. 자가 검증 + 안티패턴 박음.
  - `docs/process/document_update_record.md` (본 항목)
  - `docs/process/change_rationale_history.md`
- **Summary**: 사용자 제공 prompt 2개 agent 주입 — (1) architect TASK_DECOMPOSE 의 impl H1 traceability (Story Xa / #issue 한눈 매핑), (2) engineer IMPL 의 commit/PR 셋트 (코드 + impl spec + stories.md 분리 금지). 기존 룰 (각 impl 파일 형식 의무 / 커밋 단위 규칙) 과 중복 회피하며 미커버 영역 (제목 / batch 셋트) 만 보강. 두 파일 300줄 cap 미충돌 (max 200).

### DCN-CHG-20260501-04
- **Date**: 2026-05-01
- **Change-Type**: ci, spec
- **Files Changed**:
  - `.github/workflows/python-tests.yml` / `.github/workflows/plugin-manifest.yml` — paths 필터 폐기. branch protection required check 가 paths 미스매치로 발화 안 하면 PR BLOCKED 영원 → 모든 PR 에 발화. CI 비용 < 안전성.
  - `scripts/setup_branch_protection.mjs` — `required_pull_request_reviews: { count: 1, ... }` → `null`. 1인 운영 PR author self-approve 불가 (GitHub 정책) → review 의무 폐기. CI 4 checks 가 실질 게이트.
  - `docs/process/governance.md` §2.8 — 표 갱신 (review 1 → 비활성), 근거 갱신, `gh pr merge --squash --auto` 의무 룰 추가.
  - branch protection live 적용 (`PUT repos/alruminum/dcNess/branches/main/protection`):
    - required_status_checks contexts = `Document Sync gate` / `unittest discover` / `validate manifest` / `Task-ID format gate`
    - strict = true (base sync 의무)
    - required_pull_request_reviews = null
    - required_linear_history = true
    - allow_force_pushes = false
  - `docs/process/document_update_record.md` (본 항목)
  - `docs/process/change_rationale_history.md`
  - `PROGRESS.md`
- **Summary**: 사용자 명령 ("CI 로 강제해서 앞으로는 실패 못하게") 반영. DCN-30-37 ~ DCN-30-40 7+ PR 동안 CI fail 누적 + 머지 즉시 진행 회귀 차단. branch protection 적용 — CI 4 checks 모두 SUCCESS 전 squash merge 차단. 본 PR 부터 즉시 적용.

### DCN-CHG-20260501-03
- **Date**: 2026-05-01
- **Change-Type**: test
- **Files Changed**:
  - `tests/test_session_state.py:CleanupStaleRunsTests._set_slot` — fixture `started_at` / `last_confirmed_at` hardcoded `"2026-04-29T00:00:00+00:00"` → `datetime.now(timezone.utc).isoformat(timespec="seconds")`. time-bomb 회피.
  - `docs/process/document_update_record.md` (본 항목)
- **Summary**: CleanupStaleRunsTests 2건 (`test_keeps_fresh_slot` / `test_removes_completed_old_slot`) GitHub CI 7+ 회 fail 누적 — DCN-30-40 작업 중 사용자 보고 발견. 원인: fixture hardcoded ts (2026-04-29) 가 작성 시점엔 fresh 였으나 24h TTL + 시간 흐름 (2026-05-01 현재) 으로 stale 판정 → cleanup 대상 됨 → "fresh slot 유지" assertion 깨짐. fix: now() 동적 ts 사용. 281 tests all PASS (이전 240 ran 중 2 fail → 회귀 0).

### DCN-CHG-20260501-02
- **Date**: 2026-05-01
- **Change-Type**: agent, docs-only
- **Files Changed**:
  - `docs/process/main-claude-rules.md` (신규, 204줄) — 메인 Claude 행동 룰 SSOT. SessionStart inject (DCN-30-26 / -40) backup 메커니즘. 글로벌 `~/.claude/CLAUDE.md` 와 동일 레벨 강제.
    - §1 실존 검증 강제 — 글로벌 제1룰 + dcness §12 self-verify 통합. 안티패턴 7건 (DCN-30-37 sed misdiagnosis / DCN-30-40 inject 가정 / CI 미확인 등).
    - §2 dcness 인프라 — 300줄 cap (DCN-30-30) / 5 SSOT 표 / 거버넌스 / 핵심 강제 룰 4 / sub-agent path 보호 (DCN-CHG-20260501-01).
    - §3 Karpathy 4 원칙 전문 — `forrestchang/andrej-karpathy-skills` (MIT) 인용. dcness agent 별 적용 매핑.
  - `CLAUDE.md` 상단 🔴 reference 박스 + 문서 지도 표에 main-claude-rules.md 추가. 98 → 109줄.
  - `docs/process/document_update_record.md` (본 항목)
  - `PROGRESS.md`
- **Summary**: DCN-30-40 (SessionStart inject 처음부터 작동 0회 회귀) 후속. inject 깨져도 룰 인지 보장하는 backup 으로 main-claude-rules.md 신설. CLAUDE.md 가 reference 강제 — CC 가 CLAUDE.md 자동 로드 → 메인이 본 문서 read 자연 유도. 사용자 요청 3 항목 (실존 검증 강제 / dcness-guide 인프라 / Karpathy 전문) 정확 정합.

### DCN-CHG-20260501-01
- **Date**: 2026-05-01
- **Change-Type**: harness, hooks, spec, test
- **Files Changed**:
  - `harness/agent_boundary.py` (신규) — `DCNESS_INFRA_PATTERNS` 9 패턴 / `ALLOW_MATRIX` 12 agent / `READ_DENY_MATRIX` / `is_infra_project()` 4 OR 신호 / `is_opt_out()` `.no-dcness-guard` 마커 / `check_write_allowed()` / `check_read_allowed()` / `extract_bash_paths()` heuristic. handoff-matrix.md §4 spec 의 코드 SSOT.
  - `harness/hooks.py` — `handle_pretooluse_agent` 끝에 `update_live(active_agent=subagent, active_mode=mode)` 추가 (sub-agent 식별). `handle_pretooluse_file_op()` 신규 (Edit/Write/Read/Bash agent_boundary 강제). `handle_posttooluse_agent()` 신규 (live.json clear). CLI 2개 subcommand 추가.
  - `hooks/file-guard.sh` (신규) — PreToolUse Edit/Write/Read/Bash wrapper.
  - `hooks/post-agent-clear.sh` (신규) — PostToolUse Agent wrapper.
  - `hooks/hooks.json` — `Edit|Write|NotebookEdit|Read|Bash` matcher 추가 (PreToolUse) + `Agent` matcher 추가 (PostToolUse).
  - `tests/test_agent_boundary.py` (신규) — 27 테스트 (is_infra_project / write / read / opt-out / Bash heuristic / 통합).
  - `tests/test_hooks.py` — `FileOpAgentRecordTests` + `FileOpHookTests` + `PostToolUseAgentClearTests` 11 테스트 추가. import 갱신.
  - `docs/handoff-matrix.md` §4.4 코드 SSOT cross-ref + §4.5 강제 노트 추가. spec 의 INFRA_PATTERNS 리스트도 코드와 동기화 (loop-procedure / loop-catalog / dcness-guidelines / hooks·session_state·agent_boundary 보호 추가).
  - `docs/process/document_update_record.md` (본 항목)
  - `docs/process/change_rationale_history.md`
  - `PROGRESS.md`
- **Summary**: handoff-matrix.md §4.4/§4.5 spec 의 코드 enforcement 0 갭 해소. PreToolUse Edit/Write/Read/Bash 훅 신설로 sub-agent 인프라 path 침해 차단. live.json.active_agent 기록 (PreToolUse Agent) + 해제 (PostToolUse Agent) 로 메인 vs sub-agent 분기. user 프로젝트 활성 시만 enforce — dcness 자체 (`is_infra_project()` True) 는 통과. `.no-dcness-guard` opt-out 마커 + DCNESS_INFRA env 우회 가능. 38 신규 테스트 / all PASS.

### DCN-CHG-20260430-40
- **Date**: 2026-04-30
- **Change-Type**: hooks
- **Files Changed**:
  - `hooks/session-start.sh` — 2 bug fix:
    1. **JSON schema** — `{continue, additionalContext}` (top-level, CC honor X) → `{hookSpecificOutput: {hookEventName, additionalContext}}` (CC 정확 schema, claude-code-guide 검증).
    2. **content 압축** — guidelines.md 본문 inject (12,077 char, CC 10K cap 초과) → directive only (~1.2K). "지금 즉시 read 의무" + 5 SSOT path + 핵심 강제 룰 4 (read 전이라도 즉시 적용). 글로벌 `~/.claude/CLAUDE.md` 와 동일 레벨 강제.
  - `docs/process/document_update_record.md` (본 항목)
  - `docs/process/change_rationale_history.md`
  - `PROGRESS.md`
- **Summary**: DCN-30-26 SessionStart inject 처음부터 작동 0회 발견. 검증: 본 dcness 세션 jsonl `grep -c "dcness Guidelines"` = 0 + 자장 jajang 사용자 보고 (system-reminder = "OK" 만, 본문 부재). 2 bug 동시 수정. 후속 PR 5+개 (DCN-30-27 ~ -39) 모두 본 inject 작동 가정 위에 진행 — 가정 거짓 입증. 글로벌 제1룰 + dcness §12 self-verify 원칙 (DCN-30-35) 우리가 박은 룰 자체 위반. 검증 의무: 본 PR 머지 후 *반드시* 새 dcness 세션 시작 시 system-reminder 에 "DCN-30-39 자동 로드" 출현 확인. 자장 plugin reinstall 후 동일 검증.

### DCN-CHG-20260430-39
- **Date**: 2026-04-30
- **Change-Type**: agent, harness, test
- **Files Changed**:
  - `agents/pr-reviewer.md` §"에이전트 스코프 매트릭스" 헤더 cross-ref `(orchestration.md §7 정합)` → `(handoff-matrix.md §4 정합)`. DCN-30-32 split 잔재 정정.
  - `agents/architect/system-design.md` `agents/architect/task-decompose.md` `agents/architect/module-plan.md` `agents/architect/tech-epic.md` `agents/architect/light-plan.md` `agents/architect/docs-sync.md` `agents/architect/spec-gap.md` — H1 직후 `> ⚠️ CRITICAL — extended thinking 본문 드래프트 금지` banner 1 블록 추가. master 룰 (`agents/architect.md` §자기규율) 의 sub-mode 가시화. THINKING_LOOP 회귀 회피 (DCN-30-20 jajang 6분 stall).
  - `harness/run_review.py:render_report` 단계별 상세 표 — `tool_uses` 컬럼 신규. `s.tool_use_count ≥ 100` 시 `**bold**` 강조 (TOOL_USE_OVERFLOW 임계 정합, run_review.py:465). 미매칭 step 은 `-`.
  - `tests/test_run_review.py:ToolUsesColumnTests` — 3 신규 테스트 (header 컬럼 존재 / ≥ 100 bold / 미매칭 dash). `RunReport` import 추가. 45 ran / 45 PASS.
  - `docs/process/document_update_record.md` (본 항목)
  - `docs/process/change_rationale_history.md`
  - `PROGRESS.md`
- **Summary**: /run-review 후속 cleanup 3건 묶음. (1) DCN-30-32 orchestration.md split 잔재 cross-ref 1줄 정정 (pr-reviewer.md). (2) `tool_uses` 단계별 표 컬럼 추가 — TOOL_USE_OVERFLOW 회귀 측정 가시성 ↑ (DCN-30-37 임계 정합). (3) architect sub-mode 7개 prompt 에 THINKING_LOOP banner — master 룰 sub-mode 가시화로 회귀 회피율 ↑.

### DCN-CHG-20260430-38
- **Date**: 2026-04-30
- **Change-Type**: agent, harness, test, docs-only
- **Files Changed**:
  - `agents/engineer.md` `## 자가 검증 echo 의무` — anchor 자율화. `## 자가 검증` 단일 강제 → 다중 anchor 허용 (`## 자가 검증` / `## Verification` / `## 검증` / `## Self-Verify` 등 자율). substance (실측 명령 + 결과 수치) 만 의무. 첫 원칙 ("출력 형식 자유") 정합 강화.
  - `agents/engineer.md` `## 작업 분할 — IMPL_PARTIAL` `## 남은 작업` — 동일 anchor 자율화 (`## 남은 작업` / `## Remaining` / `## TODO` / `## 미완` 등).
  - `docs/process/dcness-guidelines.md` §12 안티패턴 1줄 추가 — Bash `sed -i` / `awk -i` / 광역 변환 후 *전·후* 실측 의무 (방법 자율). DCN-30-37 `MAIN_SED_MISDIAGNOSIS` 자동 검출 cross-ref.
  - `harness/run_review.py` — `SELF_VERIFY_ANCHORS` 패턴 4개 + `_has_self_verify_anchor(prose)` 신규. `detect_wastes` 에 `MISSING_SELF_VERIFY` 패턴 (MEDIUM): engineer step (IMPL_DONE / IMPL_PARTIAL / POLISH_DONE) prose 에 anchor 부재 시 emit.
  - `tests/test_run_review.py:MissingSelfVerifyTests` — 8 신규 테스트 (missing emit / 한국어 anchor / 영어 verification / Self-Verify / 짧은 검증 / prose 부재 skip / non-engineer skip / non-impl enum skip). 240 ran (이전 232) / 238 PASS / 2 pre-existing flaky 무관.
  - `docs/process/document_update_record.md` (본 항목)
  - `docs/process/change_rationale_history.md`
  - `PROGRESS.md`
- **Summary**: DCN-30-34 self-verify echo `## 자가 검증` 섹션 단일 anchor 형식 강제 → 첫 원칙 ("출력 형식 자유") 회색 영역. anchor 자율화 (다중 옵션) + substance 만 의무로 약화. `MISSING_SELF_VERIFY` 회귀 검출 패턴 추가 (DCN-30-37 4 패턴 + 본 PR 1 패턴 = 5 신규 회귀 패턴 누적). dcness-guidelines.md §12 안티패턴에 sed 후 검증 의무 1줄 추가 (#39 흡수). 4 PR migration (skill 슬림화 + procedure SSOT) + 회귀 fix 시리즈 모두 마무리.

### DCN-CHG-20260430-37
- **Date**: 2026-04-30
- **Change-Type**: harness, test
- **Files Changed**:
  - `harness/run_review.py:StepRecord` — `tool_use_count: int = 0` 필드 추가 (DCN-30-36 짝).
  - `harness/run_review.py:assign_invocations_to_steps` — invocation 의 `tool_use_count` 를 step 에 propagate.
  - `harness/run_review.py:_scan_main_sed_misdiagnosis` 신규 — CC session JSONL 안 메인 self-correction 패턴 (`정정.*0개` / `잘못 진단` / `misdiagnosis` / `sed.*변경.*0` / `실측 시 0`) 검출. 최대 3개 hits 반환.
  - `harness/run_review.py:detect_wastes` — signature 확장 (`invocations` / `repo_path` / `window` optional). 4 신규 패턴:
    - `TOOL_USE_OVERFLOW` (HIGH): step.tool_use_count ≥ 100 (자장 실측 임계). DCN-30-36 hint 사후 측정.
    - `PARTIAL_LOOP` (HIGH): IMPL_PARTIAL ≥ 3 in run (자장 무한 반복 패턴).
    - `END_STEP_SKIP` (HIGH): agent invocation count > steps row + 1 margin (메인 distract → end-step 누락 사후 검출).
    - `MAIN_SED_MISDIAGNOSIS` (HIGH): 메인 self-correction 패턴 발견 (I5 회귀 측정).
  - `harness/run_review.py:build_report` — invocations + window 을 detect_wastes 로 전달.
  - `tests/test_run_review.py:RegressionPatternsTests` — 8 신규 테스트 (TOOL_USE_OVERFLOW positive/negative/unmatched, PARTIAL_LOOP 3+/2-, END_STEP_SKIP exceeded/within margin, MAIN_SED_MISDIAGNOSIS detect). 34 ran (이전 26) / all PASS.
  - `docs/process/document_update_record.md` (본 항목)
  - `docs/process/change_rationale_history.md`
  - `PROGRESS.md`
- **Summary**: DCN-30-36 prior count hint 의 *사후 측정* 인프라 + 자장 실측 패턴 4종 자동 검출. 자장 실 데이터 검증 — run-c0ef57e0 에서 `tool_use_count=153` TOOL_USE_OVERFLOW 즉시 검출 (오프라인 회귀 측정 ✓). fix 효과 측정 가능 → 다음 epic 회고 시 자동 발화. 자율 침해 0 (사후 분석만).

### DCN-CHG-20260430-36
- **Date**: 2026-04-30
- **Change-Type**: harness, test
- **Files Changed**:
  - `harness/run_review.py:extract_agent_invocations` — `tool_use_count` 필드 추가 (`tur.get("totalToolUseCount", 0)`). 기존 사용처 영향 0 (추가 필드).
  - `harness/session_state.py:_prior_engineer_tool_use_count(sid)` 신규 — 현재 sid 의 CC session JSONL 에서 직전 `dcness:engineer` invocation 의 `totalToolUseCount` 추출. 측정 실패 silent (None).
  - `harness/session_state.py:_cli_begin_step` — `agent="engineer"` 시 직전 count > 0 이면 stderr hint (`[hint] prior engineer tool_use_count=N — 단일 호출 capacity 압박 인지 시 IMPL_PARTIAL 분할 자율 판단 권고. 강제 X (정보만).`).
  - `tests/test_session_state.py` — 3 신규 (`test_begin_step_engineer_emits_tool_use_hint` / `_no_hint_when_no_prior` / `_non_engineer_no_hint`). `_setup_fake_cc_jsonl` helper. 224 ran / 222 PASS / 2 pre-existing flaky 무관.
  - `docs/process/document_update_record.md` (본 항목)
  - `docs/process/change_rationale_history.md`
  - `PROGRESS.md`
- **Summary**: jajang impl-loop epic-08/09 회고 — engineer context overflow 5회 (102/119/153/170/223 tool uses) 자장 실측. DCN-30-34 IMPL_PARTIAL enum 만으론 실효 부족 — LLM 이 자기 tool_use_count self-monitor 불가 (CC API 미노출 본질 한계). helper 가 직전 count 측정 → stderr hint 로 흘려 메인이 다음 호출 prompt 에 명시 가능 ("이전 호출 87 tool uses 였음, 이번엔 분할 고려"). 자율 침해 X — 정보 보강만, 판단은 자율. 측정 source = `toolUseResult.totalToolUseCount` (CC session JSONL).

### DCN-CHG-20260430-35
- **Date**: 2026-04-30
- **Change-Type**: docs-only
- **Files Changed**:
  - `docs/process/dcness-guidelines.md` — §12 신설: 진단/제안 self-verify 원칙. 글로벌 `~/.claude/CLAUDE.md` "제1 룰" (실존 검증 강제) 을 dcness skill 진행 컨텍스트에 SessionStart 훅 자동 inject 로 재인용. 추측 금지 + 실측 후 단언 (검증 방법은 자율). 256줄 (300 cap 안).
  - `docs/process/document_update_record.md` (본 항목) / `docs/process/change_rationale_history.md`
- **Summary**: jajang impl-loop epic-08 의 I5 (메인 sed misdiagnosis "130개 fix" → 실제 0개) 회귀 방지. dcness-guidelines.md SSOT 단일 — skill 광역 1줄 참조 X (SessionStart 훅 자동 inject). engineer.md §자가 검증 echo (DCN-30-34) 와 짝 — agent 인용 + 메인 실행 verify 양방향 hygiene.

### DCN-CHG-20260430-34
- **Date**: 2026-04-30
- **Change-Type**: agent, spec
- **Files Changed**:
  - `agents/engineer.md` — 3 신규 섹션: ① 작업 분할 — `IMPL_PARTIAL` (단일 호출 무리 시 분할 + `## 남은 작업` 명시 + 메인 follow-up). ② 대량 동일 변환 — 도구 자율 선택 (codemod/sed/Edit). ③ 자가 검증 echo 의무 (`## 자가 검증` 섹션). 모드별 결론 enum 표에 `IMPL_PARTIAL` 추가. 174줄 (300 cap 안).
  - `agents/architect/{task-decompose,module-plan,light-plan}.md` — `known-hallucinations.md` cross-ref 1줄 각각 추가. 카탈로그는 SSOT 단일 — 토큰 누적 방지.
  - `agents/validator/code-validation.md` — 외부 도구 config schema 검증 자율 권고 1줄. hallucination 의심 시 공식 docs / 카탈로그 매칭.
  - `docs/known-hallucinations.md` (신규, 40줄) — 외부 도구 config 키 LLM 학습 데이터 노이즈 카탈로그 SSOT. 첫 entry: jest `setupFilesAfterFramework` ❌ → `setupFilesAfterEnv` ✅ (jajang epic-08 출처).
  - `docs/handoff-matrix.md` — §1.5 engineer enum 표에 `IMPL_PARTIAL` 행 추가. §2 retry 한도에 engineer split (≤ 3) 추가.
  - `docs/loop-catalog.md` — §3 `impl-batch-loop` step 4 allowed_enums 에 `IMPL_PARTIAL` 추가, sub_cycles 에 `engineer:IMPL-SPLIT-<n>` 추가, 분기 표 `IMPL_PARTIAL` 행 추가. §5 `quick-bugfix-loop` step 4 allowed_enums 도 동일.
  - `docs/process/dcness-guidelines.md` — §5 yolo 매트릭스에 `IMPL_PARTIAL` 행 추가.
  - `docs/process/document_update_record.md` (본 항목) / `docs/process/change_rationale_history.md` / `PROGRESS.md`
- **Summary**: jajang impl-loop epic-08 회고 I1/I2/I3 (engineer context overflow 3회) + I5 (메인 sed misdiagnosis) 회귀 방지. 자율 정신 정합 — 숫자 cap 강제 X (자기 capacity 자율 판단), 도구 자율 선택, 카탈로그 정보 제공 only.

### DCN-CHG-20260430-33
- **Date**: 2026-04-30
- **Change-Type**: harness, test
- **Files Changed**:
  - `harness/session_state.py` — `update_current_step` 에 stale current_step WARN 추가. begin-step 호출 시 *기존* current_step 의 `last_confirmed_at` 이 `STALE_STEP_TTL_SEC` (30분) 초과면 stderr `STALE STEP WARN`. `STALE_STEP_TTL_SEC = 30 * 60` 상수 신설.
  - `tests/test_session_state.py` — 2 케이스 추가 (`test_update_step_warn_when_prev_stale` / `test_update_step_no_warn_when_prev_fresh`).
  - `docs/process/document_update_record.md` (본 항목) / `docs/process/change_rationale_history.md`
- **Summary**: I4 (e08 batch 2 `.steps.jsonl` engineer 누락) 회귀 방지. 메인 distract → end-step skip → 다음 begin-step 호출 시 즉시 WARN. 자동 보정 X (DCN-30-25 정책 정합 — 안전).

### DCN-CHG-20260430-32
- **Date**: 2026-04-30
- **Change-Type**: docs-only
- **Files Changed**:
  - `docs/handoff-matrix.md` (신규, 256줄) — agent 측 강제 영역 SSOT. orchestration.md §4 결정표 (12 agent enum 표) + §5 retry 한도 + §6 escalate 카탈로그 + §7 권한 매트릭스 (HARNESS_ONLY_AGENTS / ALLOW / READ_DENY / 인프라 패턴 / 인프라 프로젝트 판정) 통째 이전. §1~§4 = 결정표 / Retry / Escalate / 접근 권한, §5 = 참조.
  - `docs/orchestration.md` — 540 → 298줄. §4 = handoff-matrix cross-ref 1 단락. §5/6/7 → handoff-matrix.md 로 이전. §8 → §5 (Catastrophic vs 자율) renumber. §9 → §6, §10 → §7 (proposal cross-ref 압축), §11 → §8 (참조 갱신 — handoff-matrix / loop-procedure / loop-catalog 추가). §5.1/5.2/5.3 sub-section 안 §6/§7.X 참조 → handoff-matrix §1/§2/§3/§4 로 갱신.
  - `docs/process/dcness-guidelines.md` §0.1 — "현재 알려진 위반" 항목 갱신 (orchestration.md 540줄 → 해소, 없음).
  - `docs/process/document_update_record.md` (본 항목)
  - `docs/process/change_rationale_history.md`
  - `PROGRESS.md`
- **Summary**: PR4 (DCN-30-30) 의 follow-up. orchestration.md (540줄) = 알려진 cap 위반. 책임 축 = 시퀀스 spec ↔ agent 결정/권한 으로 자연 분리. handoff-matrix.md 신설로 결정표 + retry + escalate + 권한 매트릭스 통합 (RWHarness `harness-architecture.md` §3 어휘 정합). 양 파일 모두 < 300줄 (298 / 256). 모든 §X.Y cross-ref 양방향 박힘.

### DCN-CHG-20260430-31
- **Date**: 2026-04-30
- **Change-Type**: agent (skill prompt)
- **Files Changed**:
  - `commands/quick.md` — 215 → 32줄 (85% 절감). `quick-bugfix-loop` cross-ref. Inputs (이슈 요약 / 영향 파일 / 재현 / 원하는 방향) + 비대상 + qa enum 별 후속 라우팅 (advance / 종료 / 위임).
  - `commands/impl.md` — 205 → 32줄 (84% 절감). `impl-batch-loop` cross-ref + UI 감지 시 `impl-ui-design-loop` 자동 전환. State-aware skip (DCN-30-13) + Step 4.5 (loop-catalog §3 풀스펙) cross-ref.
  - `commands/impl-loop.md` — 127 → 36줄 (72% 절감). `impl-batch-loop × N` chain. outer task `impl-<i>` / inner sub-task `b<i>.<agent>` 컨벤션 (DCN-30-12). catalog §3 + §10 cross-ref.
  - `commands/product-plan.md` — 113 → 32줄 (72% 절감). `feature-build-loop` cross-ref. Inputs (요구사항 / 사용자 시나리오 / 제약 / 우선순위 / 변경 vs 신규) — `CLARITY_INSUFFICIENT` 사전 회피.
  - `docs/process/document_update_record.md` (본 항목)
  - `docs/process/change_rationale_history.md`
  - `PROGRESS.md`
- **Summary**: 4 PR migration (skill 슬림화 + procedure SSOT) 의 마지막 PR. 5 skill 합계 660 → 132줄 (80% 절감). 모든 mechanics 제거 — `loop-procedure.md` (Step 0~8) + `loop-catalog.md` (loop spec) 단일 source. skill = 트리거 + Inputs 정형화 + 후속 라우팅 추천. 메인 Claude 가 catalog 행 + procedure 보고 동적 task 구성. 8 loop 모두 reconstruct 가능 (PR2 self-test pass 2 입증). 후속 — orchestration.md (540줄) split 별도 Task-ID.

### DCN-CHG-20260430-30
- **Date**: 2026-04-30
- **Change-Type**: docs-only, spec
- **Files Changed**:
  - `docs/loop-catalog.md` (신규, 239줄) — 8 loop 행별 풀스펙 SSOT. loop-procedure.md 의 §7.0 인덱스 + §7.1~§7.10 풀스펙 (allowed_enums / 분기 / sub_cycles / branch_prefix decision rule / Step 4.5 적용) 통째 이전.
  - `docs/loop-procedure.md` — 436 → 242줄. §7 = catalog cross-ref 1 단락 + §7.1 catastrophic 룰 정합 만 보존. §0 진입 모델 + §1~§6 Step 0~8 mechanics + §8 참조 (loop-catalog.md 추가).
  - `docs/process/dcness-guidelines.md` — §0 갱신 (procedure + catalog 2 SSOT 분담). §0.1 신설 (행동지침 md 300줄 cap 룰 + 대상/대상 외 + Why + How to apply + 현재 알려진 위반 = orchestration.md 540줄). 218 → 224줄.
  - `docs/orchestration.md` — §3 헤더 cross-ref 갱신 (loop-catalog.md 추가).
  - `docs/process/document_update_record.md` (본 항목)
  - `docs/process/change_rationale_history.md`
  - `PROGRESS.md`
- **Summary**: 사용자 지시 ("쪼개자 가급적 300라인 넘기지 말랬잖아 행동지침 md는 이것도 룰로 적어놔줘") 반영. loop-procedure.md (436줄) split + 300줄 cap 룰을 dcness-guidelines.md SSOT 에 명문화. 책임 축 = procedure (mechanics) ↔ catalog (loop spec) 으로 자연 분리. 양 파일 모두 < 300줄 (242 / 239). orchestration.md (540줄) 는 알려진 위반 — split 후속 Task-ID 예정. PR4 (4 skill bulk slim) 는 -31 로 밀림.

### DCN-CHG-20260430-29
- **Date**: 2026-04-30
- **Change-Type**: harness, agent, test
- **Files Changed**:
  - `harness/session_state.py:_cli_finalize_run` — `--auto-review` flag 추가. STATUS JSON 출력 직후 in-process 로 `harness.run_review.main(["--run-id", rid, "--repo", str(Path.cwd())])` 호출. 출력 = STATUS JSON + 빈 줄 + `--- /run-review (auto) ---` divider + run-review 리포트 chained. 실패 시 (`SystemExit` 제외 모든 예외) `AUTO_REVIEW_FAIL` stderr WARN + STATUS JSON 정상 출력 + exit 0.
  - `harness/session_state.py:_build_arg_parser` — `finalize-run` 서브커맨드에 `--auto-review` action="store_true" argparse 추가.
  - `commands/qa.md` — slim pilot. 127줄 → 28줄 (78% 절감). `qa-triage` loop 매핑 / Inputs (이슈 제목 / 재현 / 화면·기능 / 예상 vs 실제 / 에러) / 후속 라우팅 추천 5 enum. 절차는 [`docs/loop-procedure.md`](../docs/loop-procedure.md) §1~§6 + §7.5 cross-ref.
  - `tests/test_session_state.py` — 3 신규 케이스 (`test_finalize_run_auto_review_chains_report` / `test_finalize_run_auto_review_skip_on_failure` / `test_finalize_run_auto_review_off_no_chain`). `unittest.mock.patch` 으로 `harness.run_review.main` 가짜화. 219 ran / 217 PASS / 2 pre-existing flaky 무관.
  - `PROGRESS.md` — 본 항목 + DCN-30-28/27 백 entries 갱신.
  - `docs/process/document_update_record.md` (본 항목)
  - `docs/process/change_rationale_history.md`
- **Summary**: 4 PR migration (skill 슬림화 + procedure SSOT) 의 PR3. helper 단에서 review 자동 piggy-back 하도록 `--auto-review` flag 신설 — 메인 Claude 가 finalize-run 부르면 review skip 불가. qa.md = 가장 단순한 loop (`qa-triage` 1 step) pilot 으로 새 SSOT (loop-procedure.md §7.5) 만 cross-ref 해서 동작 가능 입증. PR4 (DCN-30-30) 에서 나머지 4 skill bulk slim 진입.

### DCN-CHG-20260430-28
- **Date**: 2026-04-30
- **Change-Type**: docs-only
- **Files Changed**:
  - `docs/loop-procedure.md` — §7 매트릭스 보강. 252 → 436 줄. PR1 self-test 에서 발견된 gap 반영:
    - §7.0 인덱스 (한눈) 6 컬럼만
    - §7.1~§7.8 행별 풀스펙 sub-section 8 개 — Step 별 `allowed_enums` 표 / 분기 / sub_cycles / branch_prefix decision rule / Step 4.5 적용 여부 명시
    - feature-build-loop §7.1 분기 (PRODUCT_PLAN_UPDATED skip / UX_REFINE_READY / CLARITY_INSUFFICIENT 등) 명시
    - impl-ui-design-loop §7.3 design-critic 별도 step 으로 분리 + DESIGN_LOOP_ESCALATE / VARIANTS_ALL_REJECTED 분기
    - ux-design-stage §7.6 / ux-refine-stage §7.7 designer mode (THREE_WAY 권장 / 키워드 ONE_WAY) + 사용자 PICK / Step 2.5 사용자 승인 명시
    - impl-batch-loop §7.2 state-aware skip (DCN-30-13 MODULE_PLAN_READY 마커) 보존
    - sub_cycle agent (architect:SPEC_GAP / engineer:POLISH-<n> / engineer:IMPL-RETRY-<n> / designer:SCREEN-ROUND-<n>) allowed_enums 명시
    - branch_prefix decision rule (impl-batch-loop = feat/chore/fix 결정 기준 / quick-bugfix-loop = qa enum 기반) 명시
  - `docs/process/document_update_record.md` (본 항목)
  - `docs/process/change_rationale_history.md`
- **Summary**: PR1 (DCN-30-27) self-test 결과 — §7 매트릭스 baseline reconstruct 가능하나 분기 / sub-cycle / allowed_enums full set / branch decision rule 디테일 부족. 사용자 결정 (Option A — 보강 후 PR2 진행) 따라 매트릭스를 §7.0 인덱스 + §7.1~§7.8 행별 풀스펙 으로 재구조화. PR3 (--auto-review + qa.md slim pilot) / PR4 (4 skill bulk slim) 진입 전 SSOT self-sufficiency 확보.

### DCN-CHG-20260430-27
- **Date**: 2026-04-30
- **Change-Type**: docs-only
- **Files Changed**:
  - `docs/loop-procedure.md` (신규, 252 줄) — dcness 8 loop 의 공통 *실행 절차* SSOT. Step 0 worktree+begin-run / Step 1 TaskCreate / Step 2~N agent 호출 골격 (begin-step → Agent → prose-staging Write → end-step → echo → TaskUpdate) / Step 4.5 stories.md/backlog.md sync (impl 계열) / Step 7 finalize-run --auto-review + clean 매트릭스 + 7a/7b commit-PR / Step 8 review 결과 인지. §7 = `loop × step` 매트릭스 (8 행 × 7 컬럼). 8 loop name 확정: `feature-build-loop` / `impl-batch-loop` / `impl-ui-design-loop` / `quick-bugfix-loop` / `qa-triage` / `ux-design-stage` / `ux-refine-stage` / `direct-impl-loop`.
  - `docs/process/dcness-guidelines.md` — §0 신설 (loop-procedure.md cross-ref + 의무 read 명시). SessionStart 훅이 guidelines.md inject 시 메인 Claude 가 자동으로 loop-procedure.md 도 인지.
  - `docs/orchestration.md` §3 헤더 — loop-procedure.md §1~§7 cross-ref + 8 loop name 매핑 (§3.1↔feature-build-loop 등) 추가. §3 = *시퀀스* (what), loop-procedure §7 = *실행 매트릭스* (how) 1:1.
  - `docs/process/document_update_record.md` (본 항목)
  - `docs/process/change_rationale_history.md`
- **Summary**: skill 5종 (`commands/{qa,quick,impl,impl-loop,product-plan}.md`) 이 Step 0~7 *실행 절차* 를 통째로 중복 보유 (100~215줄) — /run-review 같은 새 룰 도입 시 5 군데 동시 수정 = 중복 누적. 사용자 아키텍처 의도: skill = 트리거 + 인풋 정형화, 메인 Claude = SSOT 보고 동적 Task 구성. 본 PR (3 PR migration 의 1단계) = 절차 SSOT 신설 + 진입점 cross-ref. PR2 (`harness/session_state.py --auto-review` + qa.md slim pilot), PR3 (4 skill bulk slim) 후속.

### DCN-CHG-20260430-26
- **Date**: 2026-04-30
- **Change-Type**: spec, hooks
- **Files Changed**:
  - `docs/process/dcness-guidelines.md` (신규) — 모든 dcness skill 공통 룰 단일 SSOT. 11 섹션:
    1. 가시성 룰 (DCN-30-15)
    2. Step 기록 룰 (DCN-30-25)
    3. 루프 종료 시 `/run-review` 의무 (신규)
    4. 결과 출력 룰 — Bash collapsed 회피 (신규)
    5. yolo 모드
    6. AMBIGUOUS cascade
    7. worktree 격리
    8. (TBD) Epic / Story / Milestone 분할 기준
    9. (TBD) Skill 외 커스텀 루프 가이드
    10. 권한/툴 부족 시 사용자 요청 (DCN-30-18)
    11. (참조) Karpathy 4 원칙 (DCN-30-17)
  - `hooks/session-start.sh` — 활성 프로젝트 게이트 통과 후 위 가이드라인을 system-reminder 로 inject. CC SessionStart hook 출력 = JSON `{continue, additionalContext}`. 매 세션 자동 인지.
  - `commands/quick.md` — 범용 룰 (가시성 / Step 기록 / yolo / AMBIGUOUS / worktree) 본문 제거 + dcness-guidelines.md cross-ref 만. 약 380줄 → 215줄.
  - `docs/process/document_update_record.md` (본 항목)
  - `docs/process/change_rationale_history.md`
- **Summary**: 사용자 지적 — quick.md (light path 전용 skill) 에 범용 룰들이 다 박혀 책임 혼재. 동시에 미래 추가될 룰 (Epic/Story 분할, 커스텀 루프 가이드 등) 위한 SSOT 필요. `docs/process/dcness-guidelines.md` 신규로 모든 dcness 범용 룰 한 곳에 모음. SessionStart 훅이 활성 프로젝트에 한해 system-reminder 로 inject — CC 자동 로드 보장 + plugin 비활성 시 발화 X (orphan 0). RWHarness `harness-review-inject.py` 패턴 정합. 룰 신규 추가 시 dcness-guidelines.md 1 파일에만 append.

### DCN-CHG-20260430-25
- **Date**: 2026-04-30
- **Change-Type**: harness, spec, test
- **Files Changed**:
  - `harness/session_state.py` `_cli_end_step` — drift detector. live.json 의 current_step 과 args.agent 불일치 또는 current_step 부재 시 stderr WARN. 동작은 정상 진행 (자동 보정 X — 안전).
  - `harness/session_state.py` `_cli_finalize_run` — `--expected-steps N` 옵션. row count 미달 시 stderr WARN.
  - `commands/quick.md` SSOT — `## Step 기록 룰` 절 신규. Agent 호출 1회 = begin/end-step 1쌍 의무 + POLISH/재호출/git 작업 동일 + jajang 안티패턴 4건 명시 + helper 안전망 (drift/step count WARN) cross-ref. Step 7 finalize-run 호출에 `--expected-steps 5`.
  - `commands/impl.md` Step 7 — `--expected-steps 5` (architect/test-engineer/engineer/validator/pr-reviewer).
  - `tests/test_session_state.py` — 4 신규 케이스 (drift WARN 2 + step count WARN 2). 216/218 PASS (2 pre-existing flaky 무관).
  - `docs/process/document_update_record.md` (본 항목)
  - `docs/process/change_rationale_history.md`
- **Summary**: jajang DCN-30-23 사후 분석 — engineer / pr-reviewer / POLISH step 이 .steps.jsonl 에 누락. 원인: 메인 Claude 가 engineer 자체 PR 생성 후 git status 확인하느라 end-step 호출 skip + POLISH Agent 호출 시 begin/end-step 안 둘러쌈. mechanical 안전망 추가 — helper 측 자동 검출 (drift/step count WARN) + skill SSOT 강화 (Agent ↔ end-step 1:1 의무 + 안티패턴 4건 + POLISH 네이밍 컨벤션). 자동 보정 X (안전) — 메인이 사후 인지 + /run-review 진단으로 반복 학습.
- **Document-Exception**: 없음

### DCN-CHG-20260430-24
- **Date**: 2026-04-30
- **Change-Type**: harness
- **Files Changed**:
  - `harness/run_review.py` `render_report()` — `## 단계별 상세` 표에 `시작(local)` 컬럼 추가. UTC `.steps.jsonl` ts 를 `astimezone()` 로 system local timezone (KST) 변환해서 `HH:MM:SS` 표시.
  - `docs/process/document_update_record.md` (본 항목)
  - `docs/process/change_rationale_history.md`
- **Summary**: 사용자 보고 — 디버그 출력에서 step ts 가 `04:xx` UTC 로 표시되어 KST 와 9시간 차이로 헷갈림. dcness `.steps.jsonl` 은 ISO UTC 저장 (시스템 표준), 매칭/계산은 timezone 무관 (delta 기반). 표시 측만 system local timezone 변환. `--list` mtime 은 이미 local — 일관성 확보.

### DCN-CHG-20260430-23
- **Date**: 2026-04-30
- **Change-Type**: harness, spec, test
- **Files Changed**:
  - `harness/run_review.py` — `assign_invocations_to_steps()` 알고리즘 timestamp-proximity 기반으로 fix. 이전 (단순 순서 + agent name) 결함: step 0 invocation 부재 시 cascade 매칭 어긋남. jajang run-657d86fc 실측 — 9 step 중 2 만 매칭이었던 게 8 매칭 (step 0 invocation 정당 부재 제외).
  - `harness/session_state.py` — `_cli_run_dir()` 신규 + argparse subcommand `run-dir` 추가. 현재 active run 의 run_dir 절대 경로 stdout. skill prompt 가 prose-file path 격리에 사용.
  - `commands/quick.md` — Step 골격에서 prose-file 경로를 `/tmp/dcness-quick-<n>.md` → `<RUN_DIR>/.prose-staging/<step>.md` 로 전환. 자가 점검 4 항의 prose 종이 path 도 갱신.
  - `commands/product-plan.md` — Step 골격 prose-file 경로 run-dir 격리.
  - `commands/impl.md` — MODULE_PLAN step 의 prose-file 경로 run-dir 격리.
  - `commands/qa.md` — qa step 의 prose-file 경로 run-dir 격리.
  - `tests/test_run_review.py` — `AssignInvocationsTests` 4 케이스 갱신/추가: timestamp-proximity / unmatched / `test_handles_missing_first_invocation` (jajang 사례 regression 보호) / `test_excludes_invocation_after_step_ts`.
  - `tests/test_session_state.py` — `test_run_dir_cli_outputs_absolute_path` 신규.
  - `docs/process/document_update_record.md` (본 항목)
  - `docs/process/change_rationale_history.md`
- **Summary**: jajang 실측에서 발견된 2 결함 동시 fix. (1) `/run-review` Phase 2 매칭 cascade 결함 — step 0 invocation 부재 → 후속 step 모두 어긋남. timestamp-proximity 매칭 (inv.ts < step.ts AND step.ts - inv.ts ≤ 600s, closest before) 으로 해결. (2) skill prompt 의 `/tmp/dcness-*.md` 고정 path 결함 — 세션 격리 X, stale prose race condition. helper 의 `run-dir` subcommand 신규 + skill prompt 4개 (`quick` / `product-plan` / `impl` / `qa`) 가 `<run_dir>/.prose-staging/<step>.md` 사용. multisession 자동 격리 + 명시 cleanup 의존도 0. 211 tests 중 209 PASS (2 pre-existing flaky 무관).
- **Document-Exception**: 없음

### DCN-CHG-20260430-22
- **Date**: 2026-04-30
- **Change-Type**: agent
- **Files Changed**:
  - `commands/slim/product-plan.md` 삭제
  - `commands/slim/quick.md` 삭제
  - `commands/slim/impl.md` 삭제
  - `commands/slim/impl-loop.md` 삭제
  - `commands/slim/qa.md` 삭제
  - `docs/process/document_update_record.md` (본 항목)
  - `docs/process/change_rationale_history.md`
- **Summary**: DCN-CHG-20260430-21 의 staging 사본 (`commands/slim/`) 정리. 슬림 버전이 `commands/*.md` 본 위치에 commit 됐으므로 staging 사본 불필요. follow-up 약속 이행.

### DCN-CHG-20260430-21
- **Date**: 2026-04-30
- **Change-Type**: agent (skill prompt = agent 류 지침)
- **Files Changed**:
  - `commands/product-plan.md` — 414줄 → 108줄 (16,228 → 5,113자, **68% 절감**). 시퀀스/분기 표 통합, 가시성·yolo·worktree·AMBIGUOUS·catastrophic 룰을 `commands/quick.md` SSOT 참조로 일원화.
  - `commands/quick.md` — 516줄 → 291줄 (19,463 → 10,764자, **45% 절감**). 본 skill 을 공통 룰 SSOT 로 격상 (가시성 의무 템플릿·yolo 매트릭스·AMBIGUOUS cascade·worktree 패턴·Step 7 commit-PR 패턴 모두 본 파일에 보존). step 골격 표 1개 + step 별 enum 차이만 명시.
  - `commands/impl.md` — 426줄 → 194줄 (15,973 → 7,696자, **52% 절감**). step 표 + 분기 표. Step 4.5 (stories sync) / Step 2.0 (마커 검사) 핵심 메커니즘 보존. helper 경로 매번 inline → `HELPER` 변수 1회.
  - `commands/impl-loop.md` — 193줄 → 127줄 (8,730 → 4,787자, **45% 절감**). inner /impl 참조 + loop level 추가만 명시.
  - `commands/qa.md` — 204줄 → 123줄 (8,094 → 4,361자, **46% 절감**). 가시성·AMBIGUOUS cascade SSOT 참조.
  - `commands/slim/{product-plan,quick,impl,impl-loop,qa}.md` — 슬림 staging 사본 (Antigravity language server file revert 회피 우회 경로). 본 commit 후 추후 정리 가능.
  - `docs/process/document_update_record.md` (본 파일) — 본 항목 추가
  - `docs/process/change_rationale_history.md` — DCN-CHG-20260430-21 항목 추가
- **Summary**: 5개 dcness skill prompt 합계 **68,488 → 32,721자 (52% 절감, ~9k 토큰)**. `/product-plan` 진입 시 메인 thinking 시간 ~3분 46초 → 단축 기대. 동작 spec (시퀀스 / enum / 분기 / cycle 한도 / catastrophic 정합) 100% 보존.

### DCN-CHG-20260430-20
- **Date**: 2026-04-30
- **Change-Type**: harness, spec, test
- **Files Changed**:
  - `harness/run_review.py` — Phase 2 추가. `EXPECTED_AGENT_BUDGETS` 표 (12 agent 별 elapsed_s + min_output_tokens) + `extract_agent_invocations()` (CC session JSONL `toolUseResult` 파싱) + `assign_invocations_to_steps()` (순서 + agent name 매칭) + StepRecord 에 `duration_ms` / `output_tokens` / `total_tokens` / `cost_usd` / `matched_invocation` 필드 추가. `THINKING_LOOP` waste 패턴 신설 (duration > budget × 1.5 + output_tokens < budget × 0.3, 또는 duration > 5분 + output < 1k). 단계별 표 컬럼에 per-Agent metrics 추가.
  - `commands/run-review.md` — `THINKING_LOOP` 패턴 + Phase 2 per-Agent metrics 섹션 추가.
  - `tests/test_run_review.py` — 신규 8 케이스 (NormalizeAgentTypeTests 3 + AssignInvocationsTests 2 + ThinkingLoopDetectionTests 3). 23/23 PASS.
  - `docs/process/document_update_record.md` (본 항목)
  - `docs/process/change_rationale_history.md`
- **Summary**: 사용자 jajang 실측 보고 — product-planner sub-agent 가 6분 동안 ↓624 tokens 만 흘리고 stall ("멍때리기"). thinking 무한 loop 또는 stream stall 패턴. `/run-review` 로 자동 검출 가능 여부 요청 → Phase 2 진입. CC session JSONL `toolUseResult.usage.output_tokens` 와 `totalDurationMs` 가 per-Agent 매칭으로 추출 가능 확인. `THINKING_LOOP` 패턴 + 12 agent 별 budget 표 + 자동 매칭 알고리즘 (순서 + agent name). 사용자 사례 (product-planner 6분 + 624 tokens) 그대로 재현하는 테스트 추가.
- **Document-Exception**: 없음

### DCN-CHG-20260430-19
- **Date**: 2026-04-30
- **Change-Type**: harness, spec, test
- **Files Changed**:
  - `harness/run_review.py` (신규, ~370 LOC) — RWHarness `harness-review.py` 의 dcness 변환. `.steps.jsonl` + per-agent prose 파싱 → 잘한 점 (5 패턴) + 잘못한 점 (8 패턴) detection + run-level cost cross-correlation (CC session JSONL `usage` 합산) + markdown 리포트 생성.
  - `scripts/dcness-review` (신규, 0755) — wrapper (PYTHONPATH 자동 설정 후 `harness.run_review` CLI 실행).
  - `commands/run-review.md` (신규) — `/run-review` skill prompt. Step 0 (run 식별 — `--latest` / `--run-id` / `--list`) + Step 1 (Bash stdout character-for-character 출력 룰, RWHarness 패턴 정합) + Step 2 (후속 라우팅 권고).
  - `tests/test_run_review.py` (신규, 15 케이스) — parse_steps / waste detection 6 / good detection 4 / report render / run list.
  - `docs/process/document_update_record.md` (본 항목)
  - `docs/process/change_rationale_history.md`
- **Summary**: 사용자 메타-하네스 self-improvement 루프 요청 — RWHarness `/harness-review` 분석 후 dcness 측 가능성 확인 + Phase 1 구현. 데이터 소스 확인: (1) `.steps.jsonl` (agent/mode/enum/must_fix/prose_excerpt) (2) `<run_dir>/<agent>[-<MODE>].md` 전체 prose (3) CC session JSONL `usage` 합산. 잘한 점 5 패턴 (ENUM_CLEAN / PROSE_ECHO_OK / DDD_PHASE_A / DEPENDENCY_CAUSAL / EXTERNAL_VERIFIED_PRESENT) + 잘못한 점 8 패턴 (RETRY_SAME_FAIL / ECHO_VIOLATION / PLACEHOLDER_LEAK / MUST_FIX_GHOST / SPEC_GAP_LOOP / INFRA_READ / READONLY_BASH / EXTERNAL_VERIFIED_MISSING). 오늘 박은 룰 (DCN-30-15/16/18) 회귀 자동 검출 가능. dcness skill 9 개 됨. 200 tests 중 198 PASS (2건은 본 변경 무관 pre-existing flaky).
- **Document-Exception**: 없음

### DCN-CHG-20260430-18
- **Date**: 2026-04-30
- **Change-Type**: agent
- **Files Changed**:
  - `agents/plan-reviewer.md` — frontmatter `tools` 에 `WebFetch, WebSearch` 추가. 차원 8 (기술 실현성) 강화 — §8.1 외부 검증 의무 (PRD 명시 외부 의존 1개당 공식 문서 1회 fetch) + §8.2 조건부 약속 자동 탐지 ("M0 에서 검증" 패턴 → Must 직결 시 FAIL). 산출물에 `EXTERNAL_VERIFIED` 섹션 의무 추가.
  - `agents/architect/system-design.md` — Spike Gate 절 신규. 추상 ABC + Mock 만으로 SYSTEM_DESIGN_READY 통과 금지. PRD Must 직결 외부 의존 spike 1개 실측 의무. Spike PASS 시 concrete 구현 + sdk.md 갱신 / FAIL 시 TECH_CONSTRAINT_CONFLICT. jajang 사례 박음.
  - `agents/validator/design-validation.md` — Placeholder Leak 룰 추가 (계층 A). `[미기록]` / `[미결]` / `M0 이후` / `NotImplementedError` placeholder 가 PRD Must 핵심 가치 직결 시 → DESIGN_REVIEW_FAIL. Spike Gate 정합.
  - `agents/architect.md` — 공통 지침 (권한/툴 부족 시 사용자 요청) 추가.
  - `agents/engineer.md` — 공통 지침 추가.
  - `agents/test-engineer.md` — 공통 지침 추가.
  - `agents/product-planner.md` — 공통 지침 추가.
  - `agents/plan-reviewer.md` — 공통 지침 추가 (위 강화와 별개).
  - `agents/validator.md` — 공통 지침 추가.
  - `agents/pr-reviewer.md` — 공통 지침 추가.
  - `agents/security-reviewer.md` — 공통 지침 추가.
  - `agents/qa.md` — 공통 지침 추가.
  - `agents/designer.md` — 공통 지침 추가.
  - `agents/ux-architect.md` — 공통 지침 추가.
  - `agents/design-critic.md` — 공통 지침 추가.
  - `agents/architect/docs-sync.md` — 공통 지침 추가.
  - `docs/process/document_update_record.md` (본 항목)
  - `docs/process/change_rationale_history.md`
- **Summary**: 사용자 jajang 실전 푸딩에서 사단 발견 보고 — PRD 가 voice cloning 검증을 "M0" 로 미루고 M0 한 번도 실행 안 한 상태에서 F1~F14 구현. PR #144/#145 까지 와서야 핵심 가치 0% 검증 발견 + 후보 4개 모두 허밍 합성 불가 판명. plan-reviewer 가 이걸 잡았어야 하나 도구 (WebFetch/WebSearch) 부재 + "M0 에서 검증한다" 조건부 약속을 그대로 통과시킴. 3 단 처방 — (1) plan-reviewer WebFetch/WebSearch + 외부 검증 의무 + 조건부 약속 탐지 (2) architect Spike Gate (Mock+ABC 통과 금지) (3) validator(Design) Placeholder Leak 룰. 추가 — 공통 지침 "권한/툴 부족 시 사용자 요청" 13 agent 동시 박음. 미래의 약속은 검증이 아니다.
- **Document-Exception**: 없음

### DCN-CHG-20260430-17
- **Date**: 2026-04-30
- **Change-Type**: agent
- **Files Changed**:
  - `agents/product-planner.md` — Karpathy 원칙 1 (Think Before Speccing — 가정 surface / 다중 해석 / push back / 명확화) 신규 + 원칙 4 (Goal-Driven Spec — 수용 기준 검증 가능 binary) 보조.
  - `agents/architect.md` — Karpathy 원칙 절 신규. 원칙 2 (Simplicity First) *주요* + 원칙 1 (Think Before Designing) + 원칙 4 (Goal-Driven Spec) 보조.
  - `agents/engineer.md` — Karpathy 원칙 절 신규. 원칙 3 (Surgical Changes) *주요* + 원칙 2 (Simplicity First) + 원칙 4 (Goal-Driven Loop — TDD attempt 강화) 보조.
  - `agents/test-engineer.md` — Karpathy 원칙 절 신규. 원칙 4 (Goal-Driven Execution) *주요* + 원칙 1 (Think Before Testing) 보조.
  - `agents/validator.md` — Karpathy 원칙 절 신규. 원칙 1 (검증의 추측 금지) + 원칙 4 (Goal-Driven Verdict 정합).
  - `agents/pr-reviewer.md` — Karpathy 원칙 절 신규. 원칙 3 (Surgical Review) + 원칙 1 (Surface Assumptions).
  - `agents/security-reviewer.md` — Karpathy 원칙 절 신규. 원칙 1 (Surface Threat Model Assumptions) + 원칙 4 (Goal-Driven Findings).
  - `agents/designer.md` — Karpathy 원칙 절 신규. 원칙 2 (Simplicity 디자인 측면) + 원칙 1 (Surface Design Assumptions).
  - `agents/ux-architect.md` — Karpathy 원칙 절 신규. 원칙 1 (Surface Flow Assumptions) + 원칙 2 (Simplicity UX 측면).
  - `agents/qa.md` — Karpathy 원칙 절 신규. 원칙 1 (Think Before Triaging) *주요* + 원칙 4 (Goal-Driven Routing).
  - `docs/process/document_update_record.md` (본 항목)
  - `docs/process/change_rationale_history.md`
- **Summary**: forrestchang/andrej-karpathy-skills 의 4 원칙 (Think Before / Simplicity First / Surgical Changes / Goal-Driven Execution) 을 dcness 10 agent 에 분배 삽입. 사용자 매핑 (1→planner, 2→architect, 3→engineer) + 추가 (4→test-engineer 주요, 나머지 agent 에 적합한 원칙 보조). 중복 허용 — 각 agent 에 적합한 원칙 모두 박음. 각 agent 의 기존 룰과 정합성 검토 후 *구체 운영 방식* 으로 강화 ("추측 금지" → 4 항 구체화 등).
- **Document-Exception**: 없음

### DCN-CHG-20260430-16
- **Date**: 2026-04-30
- **Change-Type**: agent, spec
- **Files Changed**:
  - `agents/architect/system-design.md` — 전면 재작성. Phase A (Domain Model 선정의 — DDD 4 요소 + invariant + bounded context) + Phase B (Clean Architecture 4 레이어 + SOLID 5 원칙 + 의존성 설계 원칙 4축). 의존성 인과관계 1줄 의무 + 독립성 자가 검증 표 + 역방향 cascade 시 DIP 의무 + 전화앱 (녹음/요약/기록) 예시. 모듈 = 테스트 단위 = 의존성 1 묶음 3 정합. 300줄 cap (초과 시 detail 분리 링크). 현행화 룰.
  - `agents/architect/module-plan.md` — 작업 흐름에 `docs/domain-model.md` 의무 read 추가. "모듈 = 테스트 단위 정합" 절 신규 (test-engineer 가 명확한 PASS/FAIL 짤 수 있는 범위 self-check 3 항목). READY_FOR_IMPL 게이트에 4 항목 추가 (domain-model read / 테스트 단위 정합 / graceful 동작 / DIP interface 명시).
  - `agents/architect/task-decompose.md` — 태스크 도출 기준에 분할 단위 정합 검증 4 항목 추가 (testable / SRP / 의존성 1 묶음 / 미달 시 SYSTEM_DESIGN 재진입).
  - `agents/architect/spec-gap.md` — 설계 문서 동기화 표에 도메인 모델 / 시스템 구조 행 추가. "Domain Model 변경 사이클" 절 신규 (architect 단독 수정 + 영향 분석 + 300줄 cap).
  - `agents/engineer.md` — 권한 경계에 `docs/domain-model.md` 수정 금지 추가 (read only, 변경 시 SPEC_GAP_FOUND escalate). Phase 1 스펙 검토에 domain-model 의무 read + 도메인 invariant 보존 + 의존성 방향 보존 + DIP interface 임의 추가 금지.
  - `agents/test-engineer.md` — 권한 경계에 `docs/domain-model.md` 수정 금지 (read only). 작업 흐름에 domain-model + architecture 의존성 그래프 의무 read. "의존성 그래프 기반 테스트 범위" 절 신규 — 4 의존 패턴 별 테스트 케이스 의무 (단독 / 의존 / 부분 의존 / 역방향 cascade).
  - `agents/validator/code-validation.md` — 작업 흐름 step 2 에 `docs/domain-model.md` 권한 read 추가 (도메인 invariant / 의존성 방향 위반 의심 시).
  - `agents/pr-reviewer.md` — 권한 경계에 domain-model.md 권한 read 추가.
  - `agents/security-reviewer.md` — 권한 경계에 domain-model.md 권한 read 추가 (invariant 위반 = 보안 이슈 가능).
  - `docs/process/document_update_record.md` (본 항목)
  - `docs/process/change_rationale_history.md`
- **Summary**: architect SYSTEM_DESIGN + MODULE_PLAN + TASK_DECOMPOSE + SPEC_GAP 4 모드 + engineer + test-engineer + validator/pr-reviewer/security-reviewer 9 agent 강화. DDD 도메인 모델 선정의 의무 (`docs/domain-model.md` SSOT) + Clean Arch 4 레이어 + SOLID 5 + 의존성 인과관계 명시 + 역방향 cascade 시 DIP 의무 + 모듈 = 테스트 단위 정합. 300줄 cap + 항상 현행화. domain-model.md 는 architect 단독 수정 — 다른 9 agent 는 read only (engineer/test-engineer 의무 read, validator/pr-reviewer/security-reviewer 권한 read). 수정 필요 시 SPEC_GAP_FOUND escalate. 사용자 직접 지시 — 전화앱 통화기록/요약/녹음 의존성 예시로 정신 박음.
- **Document-Exception**: 없음

### DCN-CHG-20260430-15
- **Date**: 2026-04-30
- **Change-Type**: spec
- **Files Changed**:
  - `commands/quick.md` — "가시성 룰" 절 SSOT 강화. should → MUST. 의무 템플릿 (`[<task-id>.<agent>] echo` + `▎` prefix + 결론 줄). 자가 점검 4 항. 안티패턴 4 종 (압축 paraphrase / table 생략 / 결론만 echo / 늦은 echo). 토큰 비용 인지 (3~5%) 명시.
  - `commands/impl.md` — "가시성 룰" 절 강화. dcTest 위반 사례 명시 + SSOT 인용 강조 + 5 step 모두 의무 echo.
  - `commands/impl-loop.md` — "가시성 룰" 절 강화. multi-batch 환경 cumulative 누락 risk 명시 + `b<i>.<agent>` prefix.
  - `commands/qa.md` — "가시성 룰" 절 CRITICAL banner 추가.
  - `commands/product-plan.md` — "가시성 룰" 절 CRITICAL banner 추가. 7 step 모두 의무 강조.
  - `docs/process/document_update_record.md` (본 항목)
  - `docs/process/change_rationale_history.md`
- **Summary**: dcTest manual smoke 에서 메인 Claude 가 prose echo 룰을 *알면서도* 토큰 절약 본능으로 압축/생략한 사례 확인. prompt 텍스트 톤이 *should* 수준이라 LLM 이 무시 가능. should → MUST + 의무 템플릿 박힘 + 자가 점검 4 항 + 안티패턴 4 종 + 토큰 비용 인지로 격상. helper-side stdout 강제 (옵션 B/C) 는 사용자 거부 — prompt 강화로 해결. 5 skill 동일 톤 정합.
- **Document-Exception**: 없음

### DCN-CHG-20260430-14
- **Date**: 2026-04-30
- **Change-Type**: spec
- **Files Changed**:
  - `commands/impl.md` — Step 4.5 신규 (engineer IMPL `IMPL_DONE` 직후, validator 진입 전). batch 가 다룬 stories.md Story 체크박스 `[ ]` → `[x]`. 모든 Story 완료 시 backlog.md epic 라인도 `[x]`. 메인이 직접 mechanical edit (agent 위임 X).
  - `docs/process/document_update_record.md` (본 항목)
  - `docs/process/change_rationale_history.md`
- **Summary**: 글로벌 `~/.claude/CLAUDE.md` "태스크 완료 → stories.md 체크. 에픽 완료 → backlog.md 체크" 룰의 *완료* 시점 = engineer IMPL 완료 시점. impl.md 시퀀스에 step 으로 박지 않으면 매 batch 마다 누락 (실제 dcTest epic-01 에서 src 반영 후 stories.md 미체크 건 발견). Step 4.5 로 박아서 매 batch 자동 적용. validator 는 src/ 만 검증 → doc 변경 무시. pr-reviewer 가 코드 + doc 같이 검토.
- **Document-Exception**: 없음

### DCN-CHG-20260430-13
- **Date**: 2026-04-30
- **Change-Type**: agent, spec, docs-only
- **Files Changed**:
  - `agents/architect/task-decompose.md` — "각 impl 파일 형식 의무" 절 추가. 각 batch 산출 시 ## 생성/수정 파일 / ## 인터페이스 / ## 의사코드 / ## 결정 근거 / ## 다른 모듈과의 경계 + `MODULE_PLAN_READY` 마커 컨벤션 박음.
  - `commands/impl.md` Step 2 — `2.0 batch 마커 검사` 절 신규 (`MODULE_PLAN_READY` 마커 grep → SKIP_MODULE_PLAN 분기). 정상 호출은 2.1 로.
  - `docs/process/document_update_record.md` (본 항목)
  - `docs/process/change_rationale_history.md`
  - `PROGRESS.md`
- **Summary**: 사용자 통찰 — RWHarness 의 plan_loop 원래 의도 = "산출물 있으면 통과, 없으면 다시 호출". dcness 가 분기 폐기 (사다리 #2 회피) 하면서 *효율성도 함께 잃음* — 매 batch 마다 architect MODULE_PLAN 무조건 호출. 옵션 D (메인 자율 + 컨벤션) 채택 — TASK_DECOMPOSE 가 batch 산출 시 MODULE_PLAN 수준 detail + `MODULE_PLAN_READY` 마커 박음. /impl Step 2 가 마커 grep → 충족 시 skip + test-engineer 직진. 분기 0 추가 (grep 1줄 + 메인 판단). RWHarness 원래 의도 복원.
- **Document-Exception**: 없음

### DCN-CHG-20260430-12
- **Date**: 2026-04-30
- **Change-Type**: docs-only
- **Files Changed**:
  - `commands/impl-loop.md` — Step 2 의 inner sub-task 등록 의무화 (skip 금지) + `b<i>.<agent>` prefix 컨벤션 명시 + 가시성 목표 형식 (사용자 지정).
  - `commands/impl.md` — Step 1 의 sub-task 등록 의무 강조 + `/impl-loop` inner 호출 시 prefix 컨벤션 cross-ref.
  - `docs/process/document_update_record.md` (본 항목)
  - `docs/process/change_rationale_history.md`
- **Summary**: 사용자 manual smoke (`/impl-loop yolo`) 도중 발견 — 메인이 inner 5 sub-task TaskCreate 를 inline 으로 skip → outer 5 batch entry 만 보이고 inner 진행 미가시. 사용자가 명시 instruction 으로 워크어라운드. skill prompt 결함 fix — Step 2 에 ⚠️ 경고 + `b<i>.<agent>` prefix 컨벤션 박음 (사용자가 본 형식 그대로 default 화).
- **Document-Exception**: 없음

### DCN-CHG-20260430-11
- **Date**: 2026-04-30
- **Change-Type**: harness, spec, docs-only, test
- **Files Changed**:
  - `harness/session_state.py` — `_extract_prose_summary` 개선: `## 결론` / `## Summary` / `## 변경 요약` 섹션 우선 추출 + cap 확장 (8줄/600char → 12줄/1200char). `_CONCLUSION_HEADER_RE` regex 추가 (한국어 + 영어 + `\b` 회피 + generic `## 변경` 단독 매칭 차단).
  - `commands/qa.md` / `commands/quick.md` / `commands/product-plan.md` / `commands/impl.md` / `commands/impl-loop.md` — "가시성 룰" 절 신규: 매 Agent 호출 후 메인이 *text reply* 로 prose 핵심 5~12줄 echo 의무화 (CC collapsed 회피).
  - `tests/test_session_state.py` — `_extract_prose_summary` 5 신규 케이스 (결론 섹션 우선 / Summary alias / 변경 요약 / fallback / generic 단어 차단).
  - `docs/process/document_update_record.md` (본 항목)
  - `docs/process/change_rationale_history.md`
- **Summary**: 사용자 manual smoke 피드백 — CC 의 Agent / Bash 출력이 collapsed 표시라 매번 ctrl+o 눌러야 prose 핵심 보임. 두 채널 동시 보강: (1) helper stderr 자동 요약을 `## 결론` / `## Summary` 섹션 우선 추출 + cap 1200char 로 확장 (정보 밀도 ↑). (2) skill prompt 5개에 매 Agent 후 메인 text reply 로 5~12줄 echo 의무화 (text 는 collapsed X — 자동 가시). 두 채널 동시 = 사용자 ctrl+o 의존 0. 185/185 PASS.
- **Document-Exception**: 없음

### DCN-CHG-20260430-10
- **Date**: 2026-04-30
- **Change-Type**: docs-only
- **Files Changed**:
  - `docs/process/manual-smoke-guide.md` (신규) — plugin 재설치 절차 + 8 skill 별 발화 prompt + 기대 동작 + 검증 체크리스트 + 트러블슈팅 + 보고 양식.
  - `docs/process/document_update_record.md` (본 항목)
  - `docs/process/change_rationale_history.md`
- **Summary**: 사용자 manual smoke 효율 ↑ 위해 가이드 문서. 8 skill (init-dcness / qa / quick / quick worktree / quick yolo / product-plan / impl / impl-loop / smart-compact / efficiency) 별 발화 prompt + 기대 동작 + 검증 포인트. dcTest 가 smoke target. plugin 재설치 절차 + 트러블슈팅 + 보고 양식 표준화. 코드 변경 0.
- **Document-Exception**: 없음

### DCN-CHG-20260430-09
- **Date**: 2026-04-30
- **Change-Type**: docs-only
- **Files Changed**:
  - `README.md` — skill 표 7 → 8 (efficiency 추가). 행동형 / 읽기형 분류 명시.
  - `docs/process/document_update_record.md` (본 항목)
  - `docs/process/change_rationale_history.md`
- **Summary**: README skill 표 efficiency 추가 + 행동형 (yolo/worktree 적용) vs 읽기형 (read-only 분석) 분류 명시.
- **Document-Exception**: 없음 (docs-only)

### DCN-CHG-20260430-08
- **Date**: 2026-04-30
- **Change-Type**: harness, spec, docs-only, test
- **Files Changed**:
  - `harness/efficiency/__init__.py` (신규) — 패키지 docstring + attribution.
  - `harness/efficiency/analyze_sessions.py` (신규, fork) — CC 세션 JSONL 파싱 + 4 지표 점수화. dcness fix: encode_repo_path 가 `/` + `.` 둘 다 → `-` 변환 (CC 실 인코딩 룰 정합), price_for prefix 매칭 (dated suffix `claude-haiku-4-5-20251001` / variant tag `[1m]` 흡수).
  - `harness/efficiency/build_dashboard.py` (신규, fork) — Chart.js 단일 HTML 대시보드.
  - `harness/efficiency/detect_patterns.py` (신규, fork) — 토큰 thrash 패턴 탐지.
  - `harness/efficiency/build_patterns_dashboard.py` (신규, fork) — 패턴 HTML.
  - `scripts/dcness-efficiency` (신규, 0755) — wrapper (analyze / dashboard / patterns / patterns-dashboard / full subcommand).
  - `commands/efficiency.md` (신규) — `/efficiency` skill prompt (출처 attribution + dcness 패턴 정합 + 4 지표 rubric + 6 절감 휴리스틱).
  - `tests/test_efficiency.py` (신규, 10 케이스) — encode_repo_path / price_for prefix 매칭 / wrapper smoke / fixture session 통합.
  - `docs/process/document_update_record.md` (본 항목)
  - `docs/process/change_rationale_history.md`
  - `PROGRESS.md`
- **Summary**: `jha0313/skills_repo` 의 `improve-token-efficiency` skill 흡수. Claude Code 세션 JSONL 토큰/캐시/비용 분석 + HTML 대시보드. dcness fix 2건 (CC 인코딩 룰 정합, prefix 매칭). dcness skill 8 개 됨. read-only 분석 도구라 catastrophic 룰 비대상. 181/181 PASS.
- **Document-Exception**: 없음

### DCN-CHG-20260430-07
- **Date**: 2026-04-30
- **Change-Type**: docs-only
- **Files Changed**:
  - `README.md` — skill 목록 표 (7개) 추가 + 후속 항목 정리.
  - `docs/process/document_update_record.md` (본 항목)
  - `docs/process/change_rationale_history.md`
- **Summary**: README skill discoverability 향상 — 7개 skill 표 추가 (init-dcness / qa / quick / product-plan / impl / impl-loop / smart-compact). 공통 keyword (yolo / worktree) 도 명시.
- **Document-Exception**: 없음 (docs-only)

### DCN-CHG-20260430-06
- **Date**: 2026-04-30
- **Change-Type**: docs-only
- **Files Changed**:
  - `commands/impl.md` (신규) — `/impl` skill (per-batch 정식 impl 루프 — architect MODULE_PLAN → test-engineer → engineer IMPL → validator CODE_VALIDATION → pr-reviewer + clean 자동 commit/PR + yolo + worktree).
  - `commands/impl-loop.md` (신규) — `/impl-loop` skill (multi-batch sequential auto chain — 각 batch 마다 /impl 호출 + clean 자동 진행 + caveat 시 멈춤).
  - `docs/process/document_update_record.md` (본 항목)
  - `docs/process/change_rationale_history.md`
  - `PROGRESS.md`
- **Summary**: dcNess plugin 의 6+7 번째 skill. /quick 과 /product-plan 사이 갭 (정식 impl 루프 호출 진입점) 메움. /impl = per-batch (5 단계 task), /impl-loop = multi-batch wrapper (각 batch 의 /impl 자동 chain + clean 시 자동 진행). 사용자 manual smoke 발견 — /product-plan TASK_DECOMPOSE 산출 batch N 개를 메인이 즉흥 처리 (sub-task 등록 누락) 한 거 정정. 코드 변경 0 (prompt-only).
- **Document-Exception**: 없음

### DCN-CHG-20260430-05
- **Date**: 2026-04-30
- **Change-Type**: spec, harness, hooks, docs-only, test
- **Files Changed**:
  - `docs/orchestration.md` — §3.1 mermaid 에 validator DESIGN_VALIDATION 노드 + FAIL 루프 추가. §2.3 catastrophic 룰 §2.3.5 신규 (TD 직전 DESIGN_REVIEW_PASS 필수). §4.9 결정표에 DESIGN_VALIDATION 3 enum 추가.
  - `commands/product-plan.md` — Step 6.5 (validator DESIGN_VALIDATION) 신규. Step 1 의 task 등록 6 → 7. cycle 한도 (DESIGN_REVIEW_FAIL → SD 재진입 2 cycle) 명시. Step 7 의 PreToolUse 훅 §2.3.5 인용.
  - `harness/hooks.py` — `_has_design_review_pass()` 함수 + `handle_pretooluse_agent` 에 §2.3.5 검사 (architect TASK_DECOMPOSE + SYSTEM_DESIGN.md 존재 시 DESIGN_VALIDATION PASS grep).
  - `tests/test_hooks.py` — `CatastrophicDesignValidationTests` 5 케이스 추가.
  - `docs/process/document_update_record.md` (본 항목)
  - `docs/process/change_rationale_history.md`
  - `PROGRESS.md`
- **Summary**: orchestration §3.1 에 validator DESIGN_VALIDATION step 추가 — 사용자 manual smoke 도중 발견한 갭 (validator/design-validation.md agent 존재하지만 spec/skill 시퀀스에 빠져있음). architect SYSTEM_DESIGN 후 TASK_DECOMPOSE 직전 검증 cycle 추가, FAIL 시 SD 재진입 (cycle 한도 2). catastrophic §2.3.5 = TD 직전 DESIGN_REVIEW_PASS 필수 — 시스템 설계 검증 안 한 채 impl batch 분해 = 무의미. /product-plan skill Step 6.5 + hooks.py 검사 로직 + 5 테스트.
- **Document-Exception**: 없음

### DCN-CHG-20260430-04
- **Date**: 2026-04-30
- **Change-Type**: harness, spec, docs-only, test
- **Files Changed**:
  - `harness/llm_interpreter.py` (삭제) — Anthropic haiku interpreter dead code 제거.
  - `tests/test_llm_interpreter.py` (삭제) — 위 동반.
  - `harness/interpret_strategy.py` — `llm_interpreter` 인자 제거 + `_record` outcome 단순화 (`heuristic_hit` / `heuristic_ambiguous` / `heuristic_not_found` / `heuristic_empty`). LLM fallback 폐기.
  - `harness/signal_io.py` — docstring 정정 ("프로덕션 = haiku 주입" → "프로덕션 = heuristic-only, DI swap 은 테스트용").
  - `tests/test_interpret_strategy.py` — `LlmFallbackTests` 클래스 폐기, `HeuristicAmbiguousTests` 신규.
  - `docs/orchestration.md` / `docs/conveyor-design.md` — `llm_interpreter.py` 참조 제거 + heuristic-only 표현 갱신.
  - `docs/migration-decisions.md` — 메타 LLM 통합 TODO → DISCARDED 정정 + 보류 항목 정리.
  - `docs/status-json-mutate-pattern.md` — §0 정착 박스 추가 (heuristic-only 결정 + 4 이유 + 트렌드 위치). §Phase 3 acceptance 항목 정정.
  - `README.md` — heuristic-only 정착 명시 + Phase 2 후속 항목 갱신.
  - `commands/qa.md` — fail rate 측정 후 후속 표현 정정.
  - `docs/process/plugin-dryrun-guide.md` — §5 smoke test 코드 heuristic-only 로 재작성.
  - `docs/process/document_update_record.md` (본 항목)
  - `docs/process/change_rationale_history.md`
  - `PROGRESS.md`
- **Summary**: dcness 의 enum 추출 메커니즘 정착 — heuristic-only. proposal §0 의 "메타 LLM 해석" 비전을 한 발 더 가벼운 [2025+ heuristic-only + 메인 Claude cascade] 위치로 정정. `harness/llm_interpreter.py` 폐기 (삭제 — dead code, 호출 경로 0), `interpret_with_fallback` 의 `llm_interpreter=` 인자 제거. RWH 에이전트 진단의 사실 오류 (haiku 사용 단정) 정정 + 트렌드 분석 흡수. anthropic SDK 의존 0 + 도그푸딩 ANTHROPIC_API_KEY 불필요. 166/166 PASS.
- **Document-Exception**: 없음

### DCN-CHG-20260430-03
- **Date**: 2026-04-30
- **Change-Type**: docs-only
- **Files Changed**:
  - `docs/process/branch-surface-tracking.md` (신규) — 사다리 분류 (#1 형식 / #2 state hole / #2.5 외부 환경) + 신규 분기 추가 PR self-check + 임계 신호 (warning/critical) + dcness 한계 명시.
  - `docs/migration-decisions.md` — §7 RWH 사다리 카탈로그 + dcness 한계 + sticky 룰 + inverse fallacy 회피 추가.
  - `docs/process/document_update_record.md` (본 항목)
  - `docs/process/change_rationale_history.md`
- **Summary**: 2026-04-30 RWH 에이전트 진단 (3일/82커밋 git log 분석) 의 정확한 부분 4건 + 정정 부분 2건 (inverse fallacy 철회 + layer 혼동 정정 → 사다리 #2.5 신규 분류) governance 영구 자리에 흡수. RWH 의 외부 시각이 dcness self-discipline 문서로 변환. branch-surface-tracking.md = 매 PR self-check 회로, migration-decisions.md §7 = 사다리 카탈로그 + dcness 한계 sticky 명시. 코드 변경 0.
- **Document-Exception**: 없음

### DCN-CHG-20260430-02
- **Date**: 2026-04-30
- **Change-Type**: harness, spec, docs-only, test
- **Files Changed**:
  - `harness/session_state.py` — `_extract_prose_summary` / `_append_step_status` / `_read_steps_jsonl` / `_cli_finalize_run` / `_cli_auto_resolve` 함수 + 2 CLI subcommand (`finalize-run`, `auto-resolve`). end-step 가 prose 요약 stderr 자동 출력 (CC collapsed 회피, 모든 skill 자동 수혜). `.steps.jsonl` append-only 로그 추가.
  - `commands/quick.md` — yolo 모드 keyword 트리거 + Step 7 분기 (7a clean 자동 commit/PR + 7b caveat 확인). worktree exit 시 squash 흡수 검사 자동.
  - `commands/product-plan.md` — yolo 모드 keyword + auto-resolve 호출 가이드.
  - `tests/test_session_state.py` — `HelperAutomationTests` 9 케이스 추가.
  - `docs/process/document_update_record.md` (본 항목)
  - `docs/process/change_rationale_history.md`
  - `PROGRESS.md`
- **Summary**: Option A foundation. helper-side automation 도입으로 skill prompt 슬림화. (1) end-step 가 prose 요약 stderr 자동 출력 → 모든 skill 가시성 동시 향상 (CC collapsed 회피, ctrl+o 무관). (2) finalize-run subcommand → run 의 step status JSON 집계 (clean 판정용). (3) auto-resolve subcommand → yolo 모드 폴백 매트릭스 (UX_FLOW_ESCALATE → UX_FLOW_PATCHED 등). (4) /quick Step 7 = clean 자동 commit/PR + worktree squash 흡수 자동 처리, caveat 만 사용자 확인. (5) yolo keyword (yolo/auto/끝까지/막힘없이) 검출 시 CLARITY/AMBIGUOUS/ESCALATE 자동 폴백. catastrophic 룰 (PreToolUse 훅) 그대로 hard safety.
- **Document-Exception**: 없음

### DCN-CHG-20260429-42
- **Date**: 2026-04-29
- **Change-Type**: docs-only
- **Files Changed**:
  - `commands/qa.md` / `commands/quick.md` / `commands/product-plan.md` / `commands/init-dcness.md` — wrapper fallback path 변경 (`marketplaces/dcness` → cache glob `cache/dcness/dcness/*`).
  - `commands/init-dcness.md` — "재설치 시 재실행 필수" 경고 섹션 추가.
  - `docs/process/document_update_record.md` (본 항목)
  - `docs/process/change_rationale_history.md`
- **Summary**: Manual smoke 발견 — DCN-CHG-41 의 wrapper fallback path (`marketplaces/dcness`) 가 local marketplace add 시나리오에서 미존재. CLAUDE_PLUGIN_ROOT 가 slash command bash 에 미설정이라 fallback 발동 → 잘못된 경로 → ENOENT. cache glob (`~/.claude/plugins/cache/dcness/dcness/*`) 로 변경 — versioned 디렉토리 자동 픽 + local/GitHub 양쪽 install 시나리오 정합. plugin uninstall 시 data/ 디렉토리 정리되어 whitelist 소실되는 동작도 init-dcness 문서에 명시.
- **Document-Exception**: 없음

### DCN-CHG-20260429-41
- **Date**: 2026-04-29
- **Change-Type**: harness, docs-only
- **Files Changed**:
  - `scripts/dcness-helper` (신규, 실행권한 0755) — PYTHONPATH 자동 설정 wrapper. 자기 위치 (`BASH_SOURCE`) 로부터 plugin root 추출 → `python3 -m harness.session_state` 실행. CLAUDE_PLUGIN_ROOT 의존 0.
  - `commands/qa.md` / `commands/quick.md` / `commands/product-plan.md` / `commands/init-dcness.md` — 모든 helper 호출을 `python3 -m harness.session_state X` → `"${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/plugins/marketplaces/dcness}/scripts/dcness-helper" X` 로 일괄 변경 (RWH 패턴 정합).
  - `docs/process/document_update_record.md` (본 항목)
  - `docs/process/change_rationale_history.md`
  - `PROGRESS.md`
- **Summary**: Manual smoke 발견 — skill bash 환경에서 PYTHONPATH 미설정으로 `python3 -m harness.session_state ...` 호출이 ModuleNotFoundError. wrapper script (`scripts/dcness-helper`) 도입 — script 자기위치 기반 PYTHONPATH 자동 설정 + `exec python3 -m harness.session_state "$@"`. 4 skill 의 helper 호출 일괄 wrapper 경유로 변경.
- **Document-Exception**: 없음

### DCN-CHG-20260429-40
- **Date**: 2026-04-29
- **Change-Type**: harness, hooks, spec, docs-only
- **Files Changed**:
  - `harness/session_state.py` — `is_project_active` / `enable_project` / `disable_project` / `list_active_projects` / `whitelist_path` 함수 + 5 CLI subcommand (`enable` / `disable` / `is-active` / `status`). plugin-scoped whitelist (`~/.claude/plugins/data/dcness-dcness/projects.json`) + `DCNESS_WHITELIST_PATH` env override + `DCNESS_FORCE_ENABLE` 디버깅 env.
  - `hooks/session-start.sh` — PYTHONPATH=$CLAUDE_PLUGIN_ROOT prepend + 활성화 게이트 (`is-active` 실패 시 exit 0).
  - `hooks/catastrophic-gate.sh` — 동일 패턴.
  - `commands/init-dcness.md` (신규) — `/init-dcness` skill (현재 cwd main repo 활성화).
  - `tests/test_session_state.py` — `ProjectActivationTests` 10 케이스 추가.
  - `tests/test_multisession_smoke.py` — bash hook 호출 env 에 `DCNESS_FORCE_ENABLE=1` 추가 (게이트 우회).
  - `docs/process/document_update_record.md` (본 항목)
  - `docs/process/change_rationale_history.md`
  - `PROGRESS.md`
- **Summary**: dcNess plugin 활성화 게이트 도입. 기본 disabled — plugin install 만으로는 hook 발화 0 (다른 프로젝트에 영향 0). `/init-dcness` 으로 명시 활성화 시만 SessionStart / PreToolUse Agent 훅 발화. whitelist 는 plugin-scoped (CC `data/` 컨벤션) → 글로벌 `~/.claude/` 폴더 오염 0, plugin 제거 시 자동 정리. RWHarness `harness-projects.json` 패턴 정합 + γ resolution 으로 worktree 도 main repo whitelist 상속.
- **Document-Exception**: 없음

### DCN-CHG-20260429-39
- **Date**: 2026-04-29
- **Change-Type**: harness, spec, docs-only
- **Files Changed**:
  - `harness/session_state.py` — `_default_base()` γ 설계: `git rev-parse --git-common-dir` 으로 main repo `.claude/harness-state/` 를 단일 source 로 해석. cwd 별 캐시 (`_DEFAULT_BASE_CACHE`) + `_clear_default_base_cache()` 테스트 보조. 기존 cwd 폴백 보존 (비-git 환경).
  - `tests/test_session_state.py` — `DefaultBaseWorktreeTests` 5 케이스 추가 (plain repo / worktree / 비-git / 캐시 멱등 / by-pid cross-cwd 일관성).
  - `commands/quick.md` — Step 0a (worktree keyword 트리거) 추가, Step 0 → Step 0b 재명, Step 7 에 ExitWorktree 옵션.
  - `commands/product-plan.md` — 동일 패턴 (Step 0a + Step 8 ExitWorktree 옵션).
  - `docs/conveyor-design.md` — §13 Worktree 격리 패턴 신규 (옵션 검토 표 + γ 설계 + skill protocol 정합 + EnterWorktree 룰 정합 + 후속). §12.3 → §13.7 재번호.
  - `docs/process/document_update_record.md` (본 항목)
  - `docs/process/change_rationale_history.md`
  - `PROGRESS.md`
- **Summary**: Worktree 격리 옵션 C (keyword 트리거) 도입. `EnterWorktree` 호출 후 cwd 가 `.claude/worktrees/{name}/` 으로 변경돼도 helper 가 main repo `.claude/harness-state/` 를 단일 source 로 보도록 `_default_base()` 를 γ 설계 (git rev-parse --git-common-dir 기반) 로 변경. SessionStart 훅이 박은 by-pid / live.json 을 worktree 안 helper 가 그대로 사용 → catastrophic 정합 보존. `/quick` `/product-plan` skill 에 keyword 트리거 (Step 0a) + ExitWorktree 옵션 (종료 step) 추가. `/qa` 는 src/ 미수정이라 미적용.
- **Document-Exception**: 없음

### DCN-CHG-20260429-38
- **Date**: 2026-04-29
- **Change-Type**: docs-only
- **Files Changed**:
  - `commands/smart-compact.md` (신규) — `/smart-compact` skill (컨텍스트 압축 + resume prompt 생성)
  - `docs/process/document_update_record.md`
  - `docs/process/change_rationale_history.md`
- **Summary**: dcNess plugin 의 4번째 skill. CC 내장 `/compact` 와 차이 — 메인이 자체 LLM 으로 *세션 의도/결정/진행상태* 능동 추출 + 다음 세션용 single-message resume prompt 자동 생성 + clipboard 복사. 사용자가 컨텍스트 60%+ 도달 시 / "이어가기" 발화 시 / 자체 판단 시 사용. 추출 source = git log + document_update_record + change_rationale + PROGRESS + TaskList + transcript 의 미해결 의논. 코드 변경 0 (prompt-only).
- **Document-Exception**: 없음 (docs-only)

### DCN-CHG-20260429-37
- **Date**: 2026-04-29
- **Change-Type**: docs-only
- **Files Changed**:
  - `commands/quick.md` (신규) — `/quick` skill (light path 자동화: qa → architect LIGHT_PLAN → engineer IMPL → validator BUGFIX_VALIDATION → pr-reviewer)
  - `commands/product-plan.md` (신규) — `/product-plan` skill (새 기능 spec/design: product-planner → plan-reviewer → ux-architect → validator UX → architect SYSTEM_DESIGN → architect TASK_DECOMPOSE)
  - `docs/process/document_update_record.md`
  - `docs/process/change_rationale_history.md`
- **Summary**: dcNess plugin 의 2번째 + 3번째 skill 동시 신규. `/quick` = 작은 버그픽스 light path 자동 진행 (qa 분류가 FUNCTIONAL_BUG/CLEANUP 시), 5 task. `/product-plan` = 새 기능 spec/design 흐름 6 task (구현 진입은 별도). 둘 다 dcNess 컨베이어 패턴 (Task tool + helper + Agent + 훅) 정합. AMBIGUOUS cascade (`/qa` 와 동일 — 재호출 → 사용자 위임). 재진입 cycle 한도 (PLAN_REVIEW_CHANGES_REQUESTED / UX_VALIDATION FAIL = 각 2 cycle). catastrophic 룰 자동 정합 (§2.3.3 / §2.3.4 시퀀스가 자연 충족). 코드 변경 0 (prompt-only).
- **Document-Exception**: 없음 (docs-only)

### DCN-CHG-20260429-36
- **Date**: 2026-04-29
- **Change-Type**: docs-only
- **Files Changed**:
  - `commands/qa.md` (신규) — `/qa` skill (버그/이슈 분류 + 라우팅 추천)
  - `docs/process/document_update_record.md`
  - `docs/process/change_rationale_history.md`
- **Summary**: dcNess plugin 의 첫 skill 신규. `/qa` = 사용자가 "버그 있다 / 이슈 / 이상해 / 오류" 등 발화 시 진입. dcNess 컨베이어 패턴 (Task tool + Agent + helper + 훅) 으로 동작. 절차: begin-run → TaskCreate → 명확화 (필요 시) → begin-step + Agent(qa) + end-step → AMBIGUOUS cascade (재호출 → 사용자 위임) → 결과 보고 + 후속 skill 추천 → end-run. heuristic only (haiku 미사용 — API 키 의존 회피, 비용 0). `/quick`, `/ux` 미구현이라 후속 자동 라우팅 X — 사용자 결정 받음. agents/qa.md 의 5 결론 enum (FUNCTIONAL_BUG / CLEANUP / DESIGN_ISSUE / KNOWN_ISSUE / SCOPE_ESCALATE) 정합. 코드 변경 0 (prompt-only).
- **Document-Exception**: 없음 (docs-only 카테고리)

### DCN-CHG-20260429-35
- **Date**: 2026-04-29
- **Change-Type**: test, docs-only
- **Files Changed**:
  - `tests/test_multisession_smoke.py` (신규, 11 케이스) — bash 훅 + Python 파이프라인 e2e + 멀티세션 격리 검증.
  - `PROGRESS.md`
  - `docs/process/document_update_record.md`
  - `docs/process/change_rationale_history.md`
- **Summary**: 멀티세션 격리 e2e smoke 추가. 3 그룹: (1) bash pipeline (4 케이스 — bash 훅 종료코드 + 부수효과 + invalid sid silent + 빈 payload silent) (2) MultiSessionIsolation (3 케이스 — by-pid 격리 + live.json 격리 + 동시 spawn 격리) (3) CatastrophicRule e2e (4 케이스 — engineer §2.3.3 차단/통과 + pr-reviewer §2.3.1 차단 + HARNESS_ONLY_AGENTS run 컨텍스트 부재 차단). subprocess 통한 실제 bash → python 호출 + 동시 Popen 으로 race 검증. 160/160 tests PASS (149 기존 + 11 신규). 한계 명시 — 실 Claude Code 환경의 PPID 신뢰성 / stdin payload 형식은 별도 manual smoke 필요.
- **Document-Exception**: 없음 (test 카테고리, deliverable 자체)

### DCN-CHG-20260429-34
- **Date**: 2026-04-29
- **Change-Type**: harness, hooks, test, docs-only
- **Files Changed**:
  - `harness/hooks.py` (신규, ~280 LOC) — Claude Code 훅 핸들러 (SessionStart + PreToolUse Agent). 순수 Python.
  - `hooks/session-start.sh` (신규) — bash 래퍼, python 핸들러 호출 + cc_pid 전달
  - `hooks/catastrophic-gate.sh` (신규) — 동일 패턴
  - `hooks/hooks.json` (신규) — plugin 활성 시 hook 자동 등록 (RWHarness 패턴 정합)
  - `tests/test_hooks.py` (신규, 28 케이스) — handle_session_start (7) + HARNESS_ONLY_AGENTS (3) + §2.3.3 engineer (4) + §2.3.1 pr-reviewer (4) + §2.3.4 architect (5) + rid 폴백 (1) + silent allow (3) + (1)
  - `PROGRESS.md`
  - `docs/process/document_update_record.md`
  - `docs/process/change_rationale_history.md`
- **Summary**: `docs/conveyor-design.md` v2 (`DCN-CHG-20260429-32`) §7/§8 의 훅 스크립트 + 핸들러 구현. SessionStart = stdin sid 추출 + by-pid 작성 + live.json 초기화. PreToolUse Agent = HARNESS_ONLY_AGENTS (engineer / validator-PLAN/CODE/BUGFIX_VALIDATION) + §2.3 4룰 (1/3/4) 검사. rid 결정 = by-pid-current-run 우선 + live.json active_runs 가장 최근 미완료 슬롯 폴백. 모든 비-catastrophic 실패는 silent (CC 동작 방해 X). 149/149 tests PASS (121 기존 + 28 신규).
- **Document-Exception**: 없음 (harness/hooks 카테고리 deliverable = `tests/**` 동반 ✅)

### DCN-CHG-20260429-33
- **Date**: 2026-04-29
- **Change-Type**: harness, test, docs-only
- **Files Changed**:
  - `harness/session_state.py` — by-pid 레지스트리 함수 8개 + PPID chain walker + auto-detect 함수 2개 + CLI argparse subcommands 5개 (init-session/begin-run/end-run/begin-step/end-step) 추가. 약 +280 LOC.
  - `tests/test_session_state.py` — by-pid 레지스트리 테스트 12 + cleanup 1 + CLI 테스트 7 = 신규 20 케이스. 49 → 69 케이스.
  - `PROGRESS.md`
  - `docs/process/document_update_record.md`
  - `docs/process/change_rationale_history.md`
- **Summary**: `docs/conveyor-design.md` v2 (`DCN-CHG-20260429-32`) 의 §4/§5 multi-session 인프라 코드화. by-pid 레지스트리 = `.by-pid/{cc_pid}` (sid 매핑) + `.by-pid-current-run/{cc_pid}` (rid 매핑) — 멀티세션 정합 핵심. CLI subcommands = SessionStart 훅 (`init-session`) + helper protocol (`begin-run`/`end-run`/`begin-step`/`end-step`) 진입점. PPID chain walker = python helper 가 grandparent CC main pid 추출 (`os.getppid()` = bash → `ps -o ppid=` = CC main). auto_detect_session_id / auto_detect_run_id = by-pid 우선 + env/pointer 폴백. 121/121 tests PASS (101 기존 + 20 신규).
- **Document-Exception**: 없음 (harness 카테고리 deliverable = `tests/**` 동반 ✅)

### DCN-CHG-20260429-32
- **Date**: 2026-04-29
- **Change-Type**: docs-only
- **Files Changed**:
  - `docs/conveyor-design.md` — 대폭 rewrite (Python `run_conveyor` 모델 → Task tool + Agent + helper + 훅 패턴). 멀티세션 by-pid 레지스트리 layout 추가.
  - `docs/process/document_update_record.md` (본 항목)
  - `docs/process/change_rationale_history.md`
- **Summary**: PR #29 의 v1 design (Python 컨베이어) 폐기 후 Task tool 패턴으로 대체. 폐기 이유 = subagent 호출이 Python 안에서 일어나면 PreToolUse 훅 미발화 + 사용자 가시성 0 + 메인 자율도 0. 새 모델 = 메인이 매 step Task lifecycle 운영하며 Agent 도구 직접 호출 → CC 가 자동으로 컨텍스트 격리 + 훅 발화. helper (`begin-run/begin-step/end-step/end-run`) 가 Bash 로 호출되며 by-pid 레지스트리 (`DCNESS_RUN_ID` env 폐기 — Bash subprocess 휘발성 회피) 로 멀티세션 정합. 코드 변경 0 — 후속 Task -33 (session_state.py 확장) / -34 (hooks 신규) 가 실 구현.
- **Document-Exception**: 없음

### DCN-CHG-20260429-30
- **Date**: 2026-04-29
- **Change-Type**: harness, test, docs-only
- **Files Changed**:
  - `harness/session_state.py` (신규, ~370 LOC) — OMC+RWH 차용 세션/run 격리 API
  - `tests/test_session_state.py` (신규, 49 케이스) — session_id / pointer / atomic write / live.json envelope / active_runs / cleanup
  - `docs/process/document_update_record.md` (본 항목)
  - `docs/process/change_rationale_history.md`
  - `PROGRESS.md`
- **Summary**: `docs/conveyor-design.md` §4/§6/§9 spec 의 첫 코드 구현. session_id resolution 2-tier (env > project pointer, 글로벌 폴백 제외) + regex 검증 (OMC) + run_id `run-{token_hex(4)}` + atomic write (O_EXCL+fsync+rename+dir fsync, 0o600 RWH 패턴) + live.json with `_meta` envelope (RWH 자기참조 sessionId 검증) + active_runs map (OMC SkillActiveStateV2 차용, soft tombstone, heartbeat) + cleanup_stale_runs (24h TTL). 101/101 tests PASS (52 기존 + 49 신규). 회귀 0.
- **Document-Exception**: 없음 (harness 카테고리 deliverable = `tests/**` 동반 ✅)

### DCN-CHG-20260429-29
- **Date**: 2026-04-29
- **Change-Type**: docs-only
- **Files Changed**:
  - `docs/conveyor-design.md` (신규, ~12 절 ~500 줄) — plugin runtime 인프라 spec SSOT
  - `docs/orchestration.md` §9 정정 — "결정 보류 옵션 카탈로그" → "메인-주도 컨베이어 + PreToolUse 훅 채택" 명시 + 폐기된 옵션 (a)/(b)/(c) 카탈로그 보존
  - `docs/process/document_update_record.md` (본 항목)
  - `docs/process/change_rationale_history.md`
- **Summary**: PR #28 (`DCN-CHG-20260429-28` 옵션 c JSON 결정자 모델) close 후 새 spec 박음. **메인 클로드 = 시퀀스 결정자, 컨베이어 = 멍청한 순회기, catastrophic = PreToolUse 훅** 모델로 갈아엎음. proposal §2.5 (prose-only) 정합. 12 절 = 정체성·등장인물·흐름·데이터 모델·멀티세션·디렉토리·live.json (OMC active_runs + RWH `_meta` 차용)·훅 책임·catastrophic·atomic write·PM 옵션 (follow-up)·폐기 + 참조. 코드 변경 0 — 별도 Task 에서 실 구현 (impl_driver / session_state / 훅 신규).
- **Document-Exception**: 없음 (docs-only 카테고리, deliverable 의무 N/A)

### DCN-CHG-20260429-27
- **Date**: 2026-04-29
- **Change-Type**: agent, docs-only
- **Files Changed**:
  - `agents/architect.md` + `agents/architect/{system-design,module-plan,spec-gap,task-decompose,tech-epic,light-plan,docs-sync}.md` (8)
  - `agents/validator.md` + `agents/validator/{plan,code,design,bugfix,ux}-validation.md` (6)
  - `agents/{engineer,test-engineer,designer,design-critic}.md` (4)
  - `agents/{security-reviewer,pr-reviewer,plan-reviewer,qa}.md` (4)
  - `agents/{ux-architect,product-planner}.md` (2)
  - `PROGRESS.md` (사후 보강 entry)
  - `docs/process/document_update_record.md` (본 항목)
  - `docs/process/change_rationale_history.md`
- **Summary**: 사용자 요청 — agents/*.md 너무 길고 복잡하고 제약 많음 → dcNess 정신 (자율성 + 자율 판단) 정합 일괄 정리. **4350 → 1683 줄 (61% 감소)**, 모든 파일 ≤ 150 줄. 변환 6 원칙: (A) "🔴 정체성" 강박 섹션 + "절대 출력 금지 패턴" → frontmatter `name`/`description` 1 줄 메타로 대체 (B) 원칙 다중 → 1 줄 + 자율 판단 (C) Phase 1~7 강박 → "수행 흐름 (자율 조정 가능)" 1 단락 (D) 마크다운 템플릿 박힘 → "정보 의무 (형식 자유)" (E) 결론 enum 예시 반복 → 헤더 1 회 (F) "절대 금지" 다중 → catastrophic 1~2 + 권고 prose. 페르소나 1~2 줄, Anti-AI-Smell 1 단락 압축. "폐기된 컨벤션" 섹션 24 파일 모두 제거 (orchestration.md / status-doc 참조로 대체) + 모든 파일 끝에 cross-link 1 단락 추가. 코드 변경 0, 테스트 회귀 0 (52/52 PASS 유지).
- **Document-Exception**: 없음 (agent + docs-only 카테고리, deliverable 의무 N/A)
- **Date**: 2026-04-29
- **Change-Type**: agent, docs-only
- **Files Changed**:
  - `agents/architect.md` + `agents/architect/{system-design,module-plan,spec-gap,task-decompose,tech-epic,light-plan,docs-sync}.md` (8 파일 — 헤더 메타 자연어화, `@MODE:` 표 접두사 제거, "폐기된 컨벤션" 원리 보존)
  - `agents/validator.md` + `agents/validator/{plan,code,design,bugfix,ux}-validation.md` (6 파일 — 동일 변환)
  - `agents/engineer.md`, `agents/test-engineer.md`, `agents/designer.md`, `agents/design-critic.md` (4 파일)
  - `agents/security-reviewer.md`, `agents/pr-reviewer.md`, `agents/plan-reviewer.md`, `agents/qa.md` (4 파일)
  - `agents/ux-architect.md`, `agents/product-planner.md` (2 파일 — "절대 출력 금지 패턴" 의 `@MODE:X:Y` 예시도 자연어 모드명으로 정리)
  - `PROGRESS.md` (사후 보강 entry)
  - `docs/process/document_update_record.md` (본 항목)
  - `docs/process/change_rationale_history.md`
- **Summary**: 외부 review 지적 반영 — "agent docs 안 `@MODE:X:Y` / `@PARAMS:` JSON 블록 / `@CONCLUSION_ENUM:` 라인 / `@OUTPUT JSON schema` 메모 = status JSON schema 의 약화 변형 = 형식 사다리 부활 흔적, proposal §2.5 원칙 3 위반". 24 파일 모두 sweep — 177 hit → 0. 헤더 메타 블록 (`@MODE:X:Y` + ` ```@PARAMS: { ... } @CONCLUSION_ENUM: A | B``` `) 자연어 3 라인 ("**모드** / **결론** / **호출자가 prompt 로 전달하는 정보**") 으로 변환. 표 안 `@MODE:` 접두사 제거 (모드명만 남김). 본문 안 `@PARAMS.issue` 같은 참조도 자연어 ("호출자가 prompt 로 전달한 이슈 본문") 변환. "폐기된 컨벤션" 본문은 *원리 보존* (마커/스키마 사용 금지 명시) + 형식 어휘 자체는 제거 — 의미만 박음.
- **Document-Exception**: 없음 (agent + docs-only, deliverable 의무 N/A)
- **Date**: 2026-04-29
- **Change-Type**: agent, docs-only
- **Files Changed**:
  - `docs/orchestration.md` (신규 — 오케스트레이션 SSOT 11 섹션, RWHarness §4.2/§4.3/§3 통합)
  - `docs/status-json-mutate-pattern.md` (§11.4 에 본 SSOT cross-link 추가)
  - `CLAUDE.md` (§3 docs map 에 orchestration.md 추가)
  - `PROGRESS.md` (Phase 3 사후 보강 entry 추가)
  - `docs/process/document_update_record.md` (본 항목)
  - `docs/process/change_rationale_history.md`
- **Summary**: Phase 3 사후 보강 — 오케스트레이션 SSOT 신규 작성. proposal §2.5 원칙 4 ("impl_loop 시퀀스 보존") + §11.4 ("작업 순서 강제") 가 명시했지만 *시퀀스 정의 spec* 자체가 dcNess 안에 부재했던 사용자 지적 보강. RWHarness `harness-spec.md` §4.2 (게이트 시퀀스) + §4.3 (진입 경로 6 시나리오) + `harness-architecture.md` §3 (호출 권한 / Write 허용 / Read 금지 / INFRA_PATTERNS) 통째 dcNess 형식으로 변환. 형식 강제 어휘 (`---MARKER---` 마커, `_handoffs/{from}_to_{to}_{ts}.md` 파일, `class Flag` boolean) 모두 prose + signal_io / interpret_strategy 표현으로 치환. 11 섹션: 정체성·적용모드·게이트시퀀스 (큰 흐름 mermaid)·진입경로 (mini graph 6개)·13 agent 결론 enum 결정표·retry 한도·escalate 카탈로그·핸드오프 매트릭스·catastrophic vs 자율·코드 driver 결정 보류 (옵션 a/b/c)·proposal 인용. 옵션 (c) Orchestration Agent + 동적 시퀀스 (driver 가 sequence 파라미터 받음, 메타 LLM 이 prose 보고 동적 갱신, catastrophic backbone 만 코드 강제) 신규 발상으로 §9 에 박음 — 사용자 회의 발상 출처.
- **Document-Exception**: 없음 (agent + docs-only 카테고리 모두 deliverable 의무 N/A — agent 는 agents/* 변경 없이 CLAUDE.md cross-link 만)
- **Date**: 2026-04-29
- **Change-Type**: spec, agent, docs-only
- **Files Changed**:
  - `docs/process/plugin-dryrun-guide.md` (신규 — proposal §12 풀어쓴 11 섹션 운영 가이드)
  - `docs/status-json-mutate-pattern.md` (§6 Phase 3 acceptance 4 항목 모두 PASS 표시 + dcNess 한정 5 항목 추가)
  - `CLAUDE.md` (§3 docs map 에 plugin-dryrun-guide.md 추가)
  - `PROGRESS.md` (Phase 3 종결 표시 + acceptance 매핑 표 + Phase 4 진입 TODO)
  - `docs/process/document_update_record.md` (본 항목)
  - `docs/process/change_rationale_history.md`
- **Summary**: Phase 3 iter 5 (FINAL) — Phase 3 종결 시그널 + plugin 배포 dry-run 가이드. proposal §6 의 Phase 3 acceptance 4 항목 정합 (자연 만족 2 + 신규 워크플로 1 + 비대상 1) + dcNess 한정 추가 5 항목 (Task-ID 검증 / branch protection / haiku interpreter / heuristic-fallback + analyzer / 본 가이드) 모두 PASS 표시. plugin-dryrun-guide 는 사전검증 → manifest → marketplace → 충돌회피 → smoke test → 1 cycle 도그푸딩 → 완전 제거/롤백 → acceptance → Phase 4 후속 11 섹션. Phase 4 (4 기둥 fitness) TODO 진입.
- **Document-Exception**: 없음 (spec 카테고리 deliverable = `docs/proposals/**` 또는 `docs/spec/**` 가 의무이지만 status-json-mutate-pattern.md 가 docs/ 직속이라 docs-only 분류 — 게이트 비요구. proposal SSOT 자체 갱신은 spec 의도지만 분류 매트릭스 제약으로 docs-only 처리됨)
- **Date**: 2026-04-29
- **Change-Type**: harness, ci, test, docs-only
- **Files Changed**:
  - `harness/interpret_strategy.py` (신규 — heuristic-first + LLM-fallback 합성, outcome 5종 telemetry)
  - `tests/test_interpret_strategy.py` (신규 — 7 케이스, mock LLM, telemetry on/off)
  - `tests/test_llm_interpreter.py` (수정 — telemetry_dir 누락 3 케이스 fix, cwd `.metrics/` 오염 회피)
  - `scripts/analyze_metrics.mjs` (신규 — heuristic + LLM JSONL 집계 리포트, JSON/사람 포맷)
  - `PROGRESS.md` (Phase 3 iter 4 완료 표시)
  - `docs/process/document_update_record.md` (본 항목)
  - `docs/process/change_rationale_history.md`
- **Summary**: Phase 3 iter 4 — proposal R1 (ambiguous 카탈로그) + R8 (cycle 비용 측정) + §5 Phase 4 fitness 인프라. `interpret_with_fallback(prose, allowed, llm_interpreter=, telemetry_dir=)` 가 휴리스틱 → LLM fallback 을 합성하면서 매 호출 outcome (heuristic_hit / llm_fallback_hit / llm_fallback_unknown / heuristic_ambiguous_no_fallback / heuristic_not_found 등) 을 `.metrics/heuristic-calls.jsonl` 에 append. `analyze_metrics.mjs` 가 두 JSONL 통합 분석 (outcome 분포 / 비용 / 모델별 / allowed enum 별 / 최근 ambiguous 5개 / Phase 4 fitness 목표 PASS/WATCH 판정). 52/52 PASS, 회귀 0.
- **Document-Exception**: 없음 (harness 카테고리 deliverable = `tests/**` 동반 ✅)
- **Date**: 2026-04-29
- **Change-Type**: harness, test, docs-only
- **Files Changed**:
  - `harness/llm_interpreter.py` (신규 — Anthropic haiku interpreter 팩토리, telemetry, prompt 구성, ambiguous fallback)
  - `tests/test_llm_interpreter.py` (신규 — 16 케이스, mock client DI, telemetry on/off, signal_io 통합)
  - `.gitignore` (`.metrics/` 추가 — telemetry 디렉토리)
  - `PROGRESS.md` (Phase 3 iter 3 완료 표시)
  - `docs/process/document_update_record.md` (본 항목)
  - `docs/process/change_rationale_history.md`
- **Summary**: Phase 3 iter 3 — `harness/signal_io.py` 의 `interpret_signal(..., interpreter=)` swap point 에 주입할 Anthropic Claude haiku interpreter 구현. `make_haiku_interpreter(client=None, model='claude-haiku-4-5-20251001')` 팩토리. system prompt 가 allowed enum + UNKNOWN 출력 강제. 응답 파싱: 첫 단어 → 대문자 → allowed 매칭 안 되면 `MissingSignal('ambiguous')`. telemetry: 호출별 (model/allowed/parsed/input_tokens/output_tokens/cost_usd/elapsed_ms) `.metrics/meta-llm-calls.jsonl` append (proposal R8). `DCNESS_LLM_TELEMETRY=0` 으로 비활성. 비용 추정 모델 ~$0.0001/호출 (haiku 4.5 가격 기준). 16 테스트 PASS — 실 API 호출 0 (mock client DI 만).
- **Document-Exception**: 없음 (harness 카테고리 deliverable = `tests/**` 동반 ✅)
- **Date**: 2026-04-29
- **Change-Type**: ci, agent, docs-only
- **Files Changed**:
  - `scripts/setup_branch_protection.mjs` (신규 — branch protection 멱등 적용 스크립트, dry-run 지원)
  - `docs/process/branch-protection-setup.md` (신규 — 자동/수동 적용 + 검증 + 회귀 시나리오 가이드)
  - `docs/process/governance.md` (§2.8 신설 — branch protection 룰 정의 + §3 참조 표 갱신)
  - `CLAUDE.md` (§3 docs map 에 신규 3 파일 추가)
  - `PROGRESS.md` (Phase 3 iter 2 완료 표시)
  - `docs/process/document_update_record.md` (본 항목)
  - `docs/process/change_rationale_history.md`
- **Summary**: Phase 3 iter 2 — main 브랜치 보호 적용 스크립트 + 가이드 + governance §2.8 신설. proposal §5 Phase 3 "Gate 5 (LGTM flag) → branch protection required reviewers" 외부화. 4 status checks(`Document Sync gate`, `unittest discover`, `validate manifest`, `Task-ID format gate`) + 1 approving review + force-push/삭제 차단 + linear history. 스크립트는 admin 권한 필요(403 시 수동 가이드 fallback).
- **Document-Exception**: 없음 (deliverable 동반 의무 ci/agent 카테고리 모두 N/A — agent 는 agents/ 변경 없음, 본 변경은 CLAUDE.md cross-link 만)
- **Date**: 2026-04-29
- **Change-Type**: ci
- **Files Changed**:
  - `scripts/check_task_id.mjs` (신규 — Task-ID 형식 검증 스크립트, 로컬/CI/PR-title 3 모드)
  - `.github/workflows/task-id-validation.yml` (신규 — CI 게이트, base..head 범위 + PR title 동시 검사)
  - `PROGRESS.md` (Phase 3 시작 + iter 1 완료 표시)
  - `docs/process/document_update_record.md` (본 항목)
  - `docs/process/change_rationale_history.md`
- **Summary**: Phase 3 iter 1 — Task-ID 형식 검증 게이트(`DCN-CHG-YYYYMMDD-NN`)를 GitHub Actions + 로컬 스크립트로 도입. proposal §5 Phase 3 의 "Task-ID 형식 검증 → workflow regex" 이행. 모든 비-머지 커밋의 메시지(subject+body) 가 정확히 1개 토큰 포함하는지 검사하고 PR title 도 추가 검증. 머지 커밋(2개+ parent)은 squash 합본 자동 메시지 케이스로 면제. 다중 Task-ID(governance §2.1 "단 하나" 위반) 도 차단. Document-Exception-Task 토큰도 동일 패턴이라 자연 인정.
- **Document-Exception**: 없음 (ci 단일 카테고리, deliverable 동반 의무 없음)
- **Date**: 2026-04-29
- **Change-Type**: agent, docs-only
- **Files Changed**:
  - `agents/ux-architect.md` (신규 — UX_FLOW / UX_SYNC / UX_SYNC_INCREMENTAL / UX_REFINE 4 모드 inline, UX_FLOW_READY / UX_FLOW_PATCHED / UX_REFINE_READY / UX_FLOW_ESCALATE)
  - `agents/product-planner.md` (신규 — PRODUCT_PLAN / PRODUCT_PLAN_CHANGE / ISSUE_SYNC 3 모드, PRODUCT_PLAN_READY / CLARITY_INSUFFICIENT / PRODUCT_PLAN_CHANGE_DIFF / PRODUCT_PLAN_UPDATED / ISSUES_SYNCED)
  - `PROGRESS.md` (Phase 2 iter 5 완료 + Phase 2 종결 표시)
  - `docs/process/document_update_record.md` (본 항목)
  - `docs/process/change_rationale_history.md`
- **Summary**: Phase 2 iter 5 (FINAL) — ux-architect + product-planner 두 에이전트를 dcNess prose writing guide 형식으로 net-new 작성. **Phase 2 종결** — 13 agent docs 모두 prose-only 변환 완료 (validator 6 docs Phase 1 + iter 1~5 의 12 + 1 = 18 docs). 형식 강제 (`---MARKER:X---` + `@OUTPUT` JSON) 100% 폐기. RWHarness 의 자기인식 경계 (절대 출력 금지 패턴) / Anti-AI-Smell / 카테고리 클리셰 회피 / 라이트+다크 두 모드 의무 / Outline-First 자기규율 / Diff-First 변경 프로토콜 / thinking 본문 드래프트 금지 모두 보존.

### DCN-CHG-20260429-18
- **Date**: 2026-04-29
- **Change-Type**: agent, docs-only
- **Files Changed**:
  - `agents/designer.md` (신규 — 2×2 매트릭스 4 모드, DESIGN_READY_FOR_REVIEW / DESIGN_LOOP_ESCALATE, Phase 0~4 풀 라이프사이클)
  - `agents/design-critic.md` (신규 — VARIANTS_APPROVED / VARIANTS_ALL_REJECTED / UX_REDESIGN_SHORTLIST, 4 기준 점수표)
  - `PROGRESS.md` (Phase 2 iter 4 완료 표시)
  - `docs/process/document_update_record.md` (본 항목)
  - `docs/process/change_rationale_history.md`
- **Summary**: Phase 2 iter 4 — designer (2×2 매트릭스: SCREEN/COMPONENT × ONE_WAY/THREE_WAY = 4 모드 inline) + design-critic 두 에이전트를 dcNess prose writing guide 형식으로 net-new 작성. designer 는 Pencil MCP 다수 도구 보유 (write 포함). 형식 강제 (`---MARKER:X---` 텍스트 + `@OUTPUT` JSON) 폐기. View 전용 원칙 / 차별화 의무 / Phase 4 outline-first / DESIGN_HANDOFF 패키지 / 4 기준 점수표 / VARIANTS_ALL_REJECTED 3 라운드 escalate 정책 모두 보존. designer 는 4 모드를 별도 sub-doc 로 분리하지 않고 inline (RWHarness 원본 패턴 따름).

### DCN-CHG-20260429-17
- **Date**: 2026-04-29
- **Change-Type**: agent, docs-only
- **Files Changed**:
  - `agents/engineer.md` (신규 — IMPL_DONE / SPEC_GAP_FOUND / IMPLEMENTATION_ESCALATE / TESTS_FAIL / POLISH_DONE, Phase 1 스펙 검토 + Phase 2 구현 + 듀얼 모드 + 재시도 한도 + 커밋 룰)
  - `agents/test-engineer.md` (신규 — TESTS_WRITTEN / SPEC_GAP_FOUND, TDD attempt 0 전용)
  - `PROGRESS.md` (Phase 2 iter 3 완료 표시)
  - `docs/process/document_update_record.md` (본 항목)
  - `docs/process/change_rationale_history.md`
- **Summary**: Phase 2 iter 3 — engineer + test-engineer 두 에이전트를 dcNess prose writing guide 형식으로 net-new 작성. engineer 는 src/** Write 도구 보유 + Pencil MCP. test-engineer 는 src/ 읽기 금지(catastrophic-prevention) + impl 경로만 사용. 형식 강제 (`---MARKER:X---` 텍스트 + `@OUTPUT` JSON) 폐기. 듀얼 모드 가드레일 / DESIGN_HANDOFF 수신 / 재시도 한도(attempt 3 + spec_gap 2) / attempt 1+ 토큰 최소화 / 커밋 단위 1논리적변경 정책 모두 보존.

### DCN-CHG-20260429-16
- **Date**: 2026-04-29
- **Change-Type**: agent, docs-only
- **Files Changed**:
  - `agents/architect.md` (신규 — 마스터, 7 모드 인덱스, Outline-First 자기규율, TRD 현행화 룰, prose writing guide)
  - `agents/architect/system-design.md` (신규 — SYSTEM_DESIGN_READY)
  - `agents/architect/module-plan.md` (신규 — READY_FOR_IMPL, depth/design frontmatter, DB 영향도, 듀얼 모드 가드레일)
  - `agents/architect/spec-gap.md` (신규 — SPEC_GAP_RESOLVED / PRODUCT_PLANNER_ESCALATION_NEEDED / TECH_CONSTRAINT_CONFLICT)
  - `agents/architect/task-decompose.md` (신규 — READY_FOR_IMPL, Outline-First)
  - `agents/architect/tech-epic.md` (신규 — SYSTEM_DESIGN_READY)
  - `agents/architect/light-plan.md` (신규 — LIGHT_PLAN_READY)
  - `agents/architect/docs-sync.md` (신규 — DOCS_SYNCED / SPEC_GAP_FOUND / TECH_CONSTRAINT_CONFLICT)
  - `PROGRESS.md` (Phase 2 iter 2 완료 표시)
  - `docs/process/document_update_record.md` (본 항목)
  - `docs/process/change_rationale_history.md`
- **Summary**: Phase 2 iter 2 — RWHarness 의 architect 8 docs (마스터 + 7 모드) 를 dcNess prose writing guide 형식으로 net-new 작성. 모드별 결론 enum (SYSTEM_DESIGN_READY / READY_FOR_IMPL / SPEC_GAP_RESOLVED / LIGHT_PLAN_READY / DOCS_SYNCED 등) 을 마지막 단락 명시 패턴으로. Outline-First 자기규율 + Schema-First + TRD 현행화 + impl frontmatter (depth/design) + 듀얼 모드 가드레일 정책 보존. 형식 강제 (`---MARKER:X---` 텍스트 + `@OUTPUT` JSON) 폐기.

### DCN-CHG-20260429-15
- **Date**: 2026-04-29
- **Change-Type**: agent, docs-only
- **Files Changed**:
  - `agents/pr-reviewer.md` (신규 — prose writing guide, LGTM/CHANGES_REQUESTED enum)
  - `agents/plan-reviewer.md` (신규 — 8 차원 PRD 심사, PLAN_REVIEW_PASS/CHANGES_REQUESTED)
  - `agents/qa.md` (신규 — 이슈 분류, FUNCTIONAL_BUG / CLEANUP / DESIGN_ISSUE / KNOWN_ISSUE / SCOPE_ESCALATE)
  - `agents/security-reviewer.md` (신규 — OWASP+WebView, SECURE/VULNERABILITIES_FOUND)
  - `PROGRESS.md` (Phase 2 iter 1 완료 표시 + iter 2~5 picker 정의)
  - `docs/process/document_update_record.md` (본 항목)
  - `docs/process/change_rationale_history.md`
- **Summary**: Phase 2 iter 1 — RWHarness 의 4 read-only 에이전트 (pr-reviewer, plan-reviewer, qa, security-reviewer) 를 dcNess prose writing guide 형식으로 net-new 작성. validator.md 와 동일 패턴 (마지막 단락 enum + 자기완결 + preamble/agent-config 의존 제거). 본 4 agent 는 모두 read-only (Read/Glob/Grep) + qa 만 추적 ID 폴백용 Bash + GitHub MCP. RWHarness 형식강제 (텍스트 마커 + @OUTPUT JSON) 폐기.

### DCN-CHG-20260429-14
- **Date**: 2026-04-29
- **Change-Type**: agent, ci, docs-only
- **Files Changed**:
  - `CLAUDE.md` (§4 단일 모듈 테스트 명령어 → `tests.test_signal_io`)
  - `.github/workflows/python-tests.yml` (헤더 코멘트 — state_io → signal_io)
  - `.gitignore` (.claude/harness-state 코멘트 — status JSON → prose)
  - `.claude-plugin/marketplace.json` (description / metadata / plugin tags — status-json-mutate → prose-only)
  - `docs/migration-decisions.md` (§0 framework 질문 + §2.3 Plugin 배포 모드 — prose-only 표현으로 정정)
  - `docs/process/document_update_record.md` (본 항목)
  - `docs/process/change_rationale_history.md`
- **Summary**: DCN-CHG-20260429-13 후 잔존하는 stale `status JSON` / `state_io` 표현 sweep — 현재/forward-looking 문서 + plugin manifest + CI workflow 코멘트만 정정. 과거 이력 record 항목은 governance §2.4 스코핑 정합으로 미수정 (당시 사실 보존).
- **Document-Exception**: history 보존 — 이전 Task-ID 의 record/rationale 항목 본문은 *그 시점 사실* 이라 수정하지 않는다. governance §2.4 의 "현재 diff 추가 라인만 유효" 정합.

### DCN-CHG-20260429-13
- **Date**: 2026-04-29
- **Change-Type**: spec, harness, agent, test, docs-only
- **Files Changed**:
  - `docs/status-json-mutate-pattern.md` (제목/§1~§12 전면 개정 — Prose-Only Pattern 으로 정정, 형식 강제 폐기)
  - `harness/state_io.py` (삭제 — JSON schema 강제 자체가 형식 사다리)
  - `harness/signal_io.py` (신규 — prose write/read + interpret_signal 휴리스틱 + DI swap point)
  - `tests/test_state_io.py` (삭제)
  - `tests/test_validator_schemas.py` (삭제 — schema round-trip 자체가 폐기)
  - `tests/test_signal_io.py` (신규 — 29 케이스, prose 라운드트립 + 해석 휴리스틱 + DI)
  - `agents/validator.md` (재작성 — `@OUTPUT_*` 형식 강제 제거, prose writing guide 로)
  - `agents/validator/plan-validation.md` (재작성)
  - `agents/validator/code-validation.md` (재작성)
  - `agents/validator/design-validation.md` (재작성)
  - `agents/validator/bugfix-validation.md` (재작성)
  - `agents/validator/ux-validation.md` (재작성)
  - `docs/migration-decisions.md` (state_io DONE → DISCARDED + signal_io 신규, validator docs REFACTOR 갱신)
  - `README.md` (status-JSON 표현 → prose-only 표현)
  - `PROGRESS.md` (Phase 1 재정의 — prose-only 기반 acceptance)
  - `docs/process/document_update_record.md` (본 항목)
  - `docs/process/change_rationale_history.md`
- **Summary**: status-JSON-mutate-pattern.md 개정(형식 강제 폐기 → prose-only + 메타 LLM 해석)에 맞춰 dcNess Phase 1 산출물 재정렬. 기존 state_io.py + schema-bound validator docs + 32+9 schema 테스트를 모두 폐기하고, prose I/O + 휴리스틱 interpreter (DI swap point) + prose-writing-guide 형식의 validator 6 docs + 29 prose 테스트로 교체. 형식 강제 LOC ~290 → ~80 으로 순감소. 메타 LLM 통합은 Phase 2 swap point 로 남김.

### DCN-CHG-20260429-01
- **Date**: 2026-04-29
- **Change-Type**: ci, docs-only
- **Files Changed**:
  - `docs/process/governance.md` (신규)
  - `docs/process/document_update_record.md` (신규)
  - `docs/process/change_rationale_history.md` (신규)
  - `docs/process/document_impact_matrix.md` (신규)
  - `scripts/check_document_sync.mjs` (신규)
  - `scripts/hooks/pre-commit` (신규)
  - `scripts/hooks/cc-pre-commit.sh` (신규)
  - `.claude/settings.json` (신규)
  - `.github/PULL_REQUEST_TEMPLATE.md` (신규)
  - `AGENTS.md` (신규)
  - `PROGRESS.md` (신규)
- **Summary**: 거버넌스 시스템 초기 구축 — Document Sync 게이트(`check_document_sync.mjs`) + 3중 pre-commit 강제(git hook + Claude Code hook + AGENTS 지침) + SSOT(`governance.md`).
- **Document-Exception**: bootstrap commit — 거버넌스 자체 도입이라 이전 산출물 없음. 본 항목 자체가 self-record.

### DCN-CHG-20260429-02
- **Date**: 2026-04-29
- **Change-Type**: agent, ci, docs-only
- **Files Changed**:
  - `CLAUDE.md` (신규 — 메인 Claude 작업 지침)
  - `docs/process/governance.md` (§2.2 agent 패턴에 `^CLAUDE\.md$`, `^AGENTS\.md$` 추가)
  - `scripts/check_document_sync.mjs` (CATEGORY_RULES agent 토큰에 동일 패턴 추가)
  - `docs/process/document_update_record.md` (본 항목)
  - `docs/process/change_rationale_history.md`
  - `PROGRESS.md`
- **Summary**: 프로젝트 루트 CLAUDE.md 신규 + 게이트 룰에 루트 정책 파일(`CLAUDE.md` / `AGENTS.md`) `agent` 카테고리 분류 추가.

### DCN-CHG-20260429-03
- **Date**: 2026-04-29
- **Change-Type**: harness, test, agent, docs-only
- **Files Changed**:
  - `harness/state_io.py` (신규 — Phase 1 핵심 모듈)
  - `tests/test_state_io.py` (신규 — 32 케이스, 5 failure modes 검증)
  - `CLAUDE.md` (§4 개발 명령어에 테스트 실행 명령 추가)
  - `docs/process/document_update_record.md` (본 항목)
  - `docs/process/change_rationale_history.md`
  - `PROGRESS.md`
- **Summary**: Phase 1 foundation — `harness/state_io.py` 신규(write/read/clear + R8 5 failure modes 단일 normalize) + 테스트 32 케이스 전부 PASS. `parse_marker` 사다리 폐기를 위한 첫 모듈.

### DCN-CHG-20260429-05
- **Date**: 2026-04-29
- **Change-Type**: docs-only
- **Files Changed**:
  - `docs/migration-decisions.md` (신규 — RWHarness 모듈 분류표)
  - `docs/process/document_update_record.md` (본 항목)
- **Summary**: `status-json-mutate-pattern.md` §11.2 framework 적용 — RWHarness 의 `harness/` / `hooks/` / `agents/` / `scripts/` / `orchestration/` / `.claude-plugin/` 모듈을 PRESERVE / DISCARD / REFACTOR 로 분류. dcNess 메인 작업 모드(§11.4) 정합으로 hook/impl_loop 류는 자연 폐기, agent docs 변환 + state_io.py 만 net-new.
- **Document-Exception**: 본 변경은 분류 *결정 기록* 이라 추가 deliverable 부재. heavy 카테고리 미해당 — `docs-only` 단독.

### DCN-CHG-20260429-12
- **Date**: 2026-04-29
- **Change-Type**: agent
- **Files Changed**:
  - `AGENTS.md` (Status JSON Mutate 패턴 섹션 추가 + 참조 보강)
  - `docs/process/document_update_record.md` (본 항목)
  - `docs/process/change_rationale_history.md`
- **Summary**: AGENTS.md 보강 — 외부 에이전트(Codex 등) 가 본 저장소에 PR 보낼 때 status JSON Write 패턴을 인지하도록 명시. 폐기된 `---MARKER:X---` 컨벤션 사용 금지 + 결과 파일 경로 + schema 필수 필드 + read_status 가이드.

### DCN-CHG-20260429-11
- **Date**: 2026-04-29
- **Change-Type**: docs-only
- **Files Changed**:
  - `README.md` (대폭 보강 — 정체성·차이점·Phase 1 현황·Quick Start·코드 예·거버넌스·후속)
  - `docs/process/document_update_record.md` (본 항목)
- **Summary**: README.md 보강 — Phase 1 완료 외부 공개. RWHarness vs dcNess 차이 표 + 1차 구현 컴포넌트 매핑 + Quick Start (의존성 / 셋업 / 검증 / 코드 사용 예) + 거버넌스 / 다음 단계 / 참조 문서 지도.

### DCN-CHG-20260429-10
- **Date**: 2026-04-29
- **Change-Type**: ci
- **Files Changed**:
  - `scripts/check_plugin_manifest.mjs` (신규 — manifest 무결성 validator)
  - `.github/workflows/plugin-manifest.yml` (신규 — CI workflow)
  - `docs/process/document_update_record.md` (본 항목)
  - `docs/process/change_rationale_history.md`
  - `PROGRESS.md`
- **Summary**: Plugin manifest 무결성 검증 — `plugin.json` + `marketplace.json` 의 required 필드 + name regex + 두 파일 간 name 정합 검증. `claude plugin validate` (CLI 의존) 대신 Node-only minimum guard.

### DCN-CHG-20260429-09
- **Date**: 2026-04-29
- **Change-Type**: ci
- **Files Changed**:
  - `.github/workflows/python-tests.yml` (신규)
  - `docs/process/document_update_record.md` (본 항목)
  - `docs/process/change_rationale_history.md`
  - `PROGRESS.md`
- **Summary**: Python unittest 자동 회귀 차단 — `tests/test_state_io.py` (32) + `tests/test_validator_schemas.py` (9) 자동 실행. paths 필터로 `harness/` / `tests/` / `agents/` 변경 시만 발동(docs-only PR 면제).

### DCN-CHG-20260429-08
- **Date**: 2026-04-29
- **Change-Type**: ci
- **Files Changed**:
  - `.github/workflows/document-sync.yml` (신규 — Document Sync 게이트 CI workflow)
  - `docs/process/document_update_record.md` (본 항목)
  - `docs/process/change_rationale_history.md`
  - `PROGRESS.md`
- **Summary**: Document Sync 게이트 CI level 추가 — PR 단위로 base..head diff 를 검사. 로컬 게이트(git pre-commit + Claude Code PreToolUse) 가 우회된 경우(`--no-verify` 등) CI 가 *최후 차단*. proposal 4-pillar #2 (CI 게이트) 정합.

### DCN-CHG-20260429-07
- **Date**: 2026-04-29
- **Change-Type**: test
- **Files Changed**:
  - `tests/test_validator_schemas.py` (신규 — 9 케이스)
  - `docs/process/document_update_record.md` (본 항목)
- **Summary**: validator agent docs 의 모든 ```json``` 예시 status JSON 이 `state_io.read_status` 와 round-trip 통과하는지 자동 검증. 마스터의 매트릭스 정합 + 폐기 컨벤션(`---MARKER:X---` 결정 원천) / preamble 자동 주입 의존 부재 검증 포함. 향후 docs 변경 시 schema 깨지면 즉시 fail.
- **Document-Exception**: `test` 단독 카테고리 — heavy 미해당으로 rationale 면제. 본 변경은 DCN-CHG-20260429-06 의 *follow-up acceptance* 항목 직접 구현이라 rationale 동반은 잉여.

### DCN-CHG-20260429-06
- **Date**: 2026-04-29
- **Change-Type**: agent
- **Files Changed**:
  - `agents/validator.md` (신규 — 마스터 + 5 모드 인덱스)
  - `agents/validator/plan-validation.md` (신규)
  - `agents/validator/code-validation.md` (신규)
  - `agents/validator/design-validation.md` (신규)
  - `agents/validator/bugfix-validation.md` (신규)
  - `agents/validator/ux-validation.md` (신규)
  - `docs/process/document_update_record.md` (본 항목)
  - `docs/process/change_rationale_history.md`
- **Summary**: validator agent docs 6개 신규 — RWHarness 의 `agents/validator*.md` 를 status JSON Write 형식으로 변환. `@OUTPUT_FILE` / `@OUTPUT_SCHEMA` / `@OUTPUT_RULE` 컨벤션 채택. `---MARKER:X---` 텍스트 컨벤션 + preamble.md 자동 주입 의존 + agent-config 별 layer 모두 폐기.

### DCN-CHG-20260429-04
- **Date**: 2026-04-29
- **Change-Type**: agent, ci, docs-only
- **Files Changed**:
  - `.claude-plugin/plugin.json` (신규 — plugin 메타)
  - `.claude-plugin/marketplace.json` (신규 — marketplace 정의)
  - `docs/process/governance.md` (§2.2 agent 패턴에 `^\.claude-plugin/` 추가)
  - `scripts/check_document_sync.mjs` (CATEGORY_RULES agent 토큰 동기 갱신)
  - `docs/process/document_update_record.md` (본 항목)
  - `docs/process/change_rationale_history.md`
  - `PROGRESS.md`
- **Summary**: Plugin 배포 인프라 — `dcness@dcness` plugin/marketplace manifest 신규. `status-json-mutate-pattern.md` §12 (RWHarness → 신규 Plugin 전환 절차) 정합. governance §2.2 의 `agent` 카테고리에 `.claude-plugin/` 패턴 추가하여 plugin manifest 변경에도 record/rationale 동반 강제.
