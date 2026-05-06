# AGENTS — Common Instructions

본 저장소는 **Document Sync 거버넌스**를 강제한다. 규칙 정의의 SSOT 는 [`docs/internal/governance.md`](docs/internal/governance.md). 본 파일은 *지침* 일 뿐 규칙을 *재기술하지 않는다*.

## 모든 에이전트(사람 포함) 강제 절차

1. **작업 시작**: Task-ID 발급 — `DCN-CHG-YYYYMMDD-NN` (governance §2.1).
2. **작업 완료 직전** 다음 파일 갱신:
   - `docs/internal/document_update_record.md` (모든 변경)
   - `docs/internal/change_rationale_history.md` (spec / agent / harness / hooks / ci 변경 시)
   - `PROGRESS.md` (harness / hooks / ci 변경 시)
   - 카테고리별 deliverable (governance §2.6)
3. **commit 직전 반드시**: `node scripts/check_document_sync.mjs` 실행. 실패 시 누락 항목 보충 후 재시도.
4. **PR**: `.github/PULL_REQUEST_TEMPLATE.md` 체크리스트 모두 작성.

## 금지

- `git commit --no-verify` 등 hook 우회.
- 과거 머지된 `Document-Exception` 으로 현재 위반 회피 (governance §2.4 스코핑).
- Task-ID 없이 commit.
- `governance.md` 외 파일에 거버넌스 룰 *재기술*. 참조만.

## 환경별 설정

### Claude Code

`.claude/settings.json` 에 PreToolUse hook(`cc-pre-commit.sh`)이 등록되어 `git commit` 실행 시 자동으로 게이트가 작동한다. 별도 조치 불필요.

### 외부 에이전트 (Codex 등) / 사람

git pre-commit hook 1회 설치:

```sh
cp scripts/hooks/pre-commit .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit
```

이후 모든 `git commit` 이 자동 검사된다.

## 예외 처리

정당한 예외(deliverable 디렉토리 부재, 외부 의존 변경 등)는 commit 메시지나 변경된 산출물에:

```
Document-Exception: <사유 한 줄>
Document-Exception-Task: DCN-CHG-YYYYMMDD-NN
```

`document_update_record.md` 의 해당 Task 항목에도 사유 명시 필수.

## Prose-Only 패턴 (validator 등 검증 에이전트)

본 저장소는 [`docs/plugin/prose-only-principle.md`](docs/plugin/prose-only-principle.md) (Prose-Only 원칙) 에 따라 검증 결과를 **자유 prose** 로 emit 한다. 검증 에이전트(validator, plan-reviewer, pr-reviewer, security-reviewer 등) 호출 시:

1. **stdout 으로 prose**: 형식 자유 (markdown / 평문 / 표). harness 가 prose 파일로 저장(`.claude/harness-state/<run_id>/<agent>[-<MODE>].md`).
2. **결론 enum**: prose 의 *마지막 단락* 에 mode-specific enum 단어 1개 명시 (예: `PASS` / `FAIL` / `SPEC_MISSING`). 모호한 표현 금지.
3. **이유 필수**: 결론 근거 = 파일 path + 라인 번호 + 구체적 사실. 추측 금지.
4. **폐기된 컨벤션**:
   - `---MARKER:X---` 마지막 줄 정형 + `MARKER_ALIASES` 폴백 (사다리 자체 폐기)
   - status JSON `@OUTPUT_FILE` / `@OUTPUT_SCHEMA` / `@OUTPUT_RULE` (이전 dcNess 패턴 — JSON 형식도 형식 강제)
   - `preamble.md` 자동 주입 / agent-config 별 layer (자기완결 docs)
   - 모두 사용 금지.

자세한 형식 + 모드별 enum: [`agents/validator.md`](agents/validator.md), [`docs/plugin/prose-only-principle.md`](docs/plugin/prose-only-principle.md) §1.

orchestrator 측 해석은 [`harness/signal_io.py`](harness/signal_io.py) 의 `interpret_signal(prose, allowed)` 사용 — `MissingSignal` 단일 normalize (not_found / empty / ambiguous). 메타 LLM 통합은 `interpreter=` 인자로 swap.

## 참조

- [`docs/internal/governance.md`](docs/internal/governance.md) — SSOT (모든 거버넌스 규칙)
- [`docs/plugin/prose-only-principle.md`](docs/plugin/prose-only-principle.md) — Prose-Only 원칙 현행 SSOT
- [`docs/internal/document_impact_matrix.md`](docs/internal/document_impact_matrix.md) — 변경 → 검토 문서 빠른 참조
- [`PROGRESS.md`](PROGRESS.md) — 현재 상태 / TODO / Blockers
- [`README.md`](README.md) — 프로젝트 개요 + Quick Start
