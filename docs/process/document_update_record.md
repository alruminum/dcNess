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
