# dcNess

> **Status**: `0.2.0` — Phase 1~3 완료 · Epic 3 완료 (release 브랜치 배포 채널 전환) · Plugin 배포 dry-run 진행 중
> **Origin**: [`alruminum/realworld-harness`](https://github.com/alruminum/realworld-harness) fork-and-refactor
> **Spec**: [`docs/plugin/prose-only-principle.md`](docs/plugin/prose-only-principle.md) (Prose-Only 원칙)

Lightweight harness — **prose-only + heuristic enum 추출** 결정론 + **함정 회피 5원칙** 기반.

## 무엇이 다른가

| 항목 | 선행 하네스 | dcNess |
|---|---|---|
| 결정론 메커니즘 | `parse_marker` regex + `MARKER_ALIASES` 사다리 (~180 LOC) | `signal_io.interpret_signal` — agent prose 자유 emit, **heuristic-only** 단어경계 매칭으로 결론 enum 추출. ambiguous 시 메인 Claude cascade |
| 형식 강제 | `---MARKER:X---` + alias 변형 12개 | **0** — 형식 / flag / schema 모두 agent 자율. harness 강제 = 작업 순서 + 접근 영역만 |
| 컨텍스트 layer | 5 layer (CLAUDE.md + agents + agent-config + preamble + sub-doc) | 2 layer (CLAUDE.md + agents) — preamble / agent-config 자동 주입 폐기 |
| 게이트 | hook 7+ (agent-boundary / commit-gate / etc.) | 거버넌스 + 3 CI workflow (Document Sync + Python tests + Plugin manifest) |
| LOC 목표 | 5000 | 2500 ~ 3000 |

핵심 발상 (proposal §2 + 정착 박스):

> "agent 는 prose 자유롭게 emit.
>  harness 는 prose 의 결론 enum 을 *휴리스틱 단어경계 매칭* 으로 추출.
>  ambiguous 시 메인 Claude 가 cascade (재호출 / 사용자 위임).
>  형식 강제 0, flag 0, schema 0, **메타 LLM 호출 0**."

## 1차 구현 (Phase 1) 현황

✅ **완료** — validator 단일 agent 단위로 prose-only 패턴 검증.

| 컴포넌트 | 위치 | 상태 |
|---|---|---|
| Signal I/O 모듈 | [`harness/signal_io.py`](harness/signal_io.py) | 29 단위 테스트 통과 (round-trip / path 화이트리스트 / 휴리스틱 / DI swap) |
| Validator agent docs | [`agents/validator.md`](agents/validator.md) + [`agents/validator/*.md`](agents/validator) (5 모드) | prose writing guide (결론 + 이유) |
| Plugin manifest | [`.claude-plugin/plugin.json`](.claude-plugin/plugin.json) + [marketplace.json](.claude-plugin/marketplace.json) | 다른 플러그인과 공존 가능 (`name=dcness`) |
| CI workflows | [`.github/workflows/`](.github/workflows) | 3 종 (document-sync / python-tests / plugin-manifest) |

자세한 현황: [`PROGRESS.md`](PROGRESS.md)

## Quick Start (개발자)

### 의존성

- Python 3.11+ (테스트 실행)
- Node.js 20+ (git-naming 게이트)
- 외부 패키지 0 (표준 라이브러리만 — heuristic-only 정착으로 anthropic SDK 의존 0)

### 셋업

```sh
git clone https://github.com/alruminum/dcNess.git
cd dcNess

# git pre-commit hook 설치 (1회)
cp scripts/hooks/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

### 검증

```sh
# 단위 테스트 (signal_io)
python3 -m unittest discover -s tests -v

# Document Sync 게이트 (수동 실행 — commit 시 자동 호출)
node scripts/check_document_sync.mjs

# Plugin manifest 검증
node scripts/check_plugin_manifest.mjs
```

### 코드 사용 예 (`signal_io`)

```python
from harness.signal_io import (
    MissingSignal,
    interpret_signal,
    read_prose,
    write_prose,
)

# Agent 측 (또는 harness 가 stdout 캡처 후) — prose 저장
write_prose(
    "validator", "run_001",
    """## 검증 결과

A 스펙 일치 / B 의존성 모두 통과. C 경고 1건 (FAIL 아님).

## 결론

PASS
""",
    mode="CODE_VALIDATION",
)

# Orchestrator 측 — prose 읽고 결론 enum 1개 추출
try:
    prose = read_prose("validator", "run_001", mode="CODE_VALIDATION")
    conclusion = interpret_signal(prose, ["PASS", "FAIL", "SPEC_MISSING"])
    if conclusion == "PASS":
        ...  # 다음 단계 진입
except MissingSignal as e:
    # 3 reasons (not_found / empty / ambiguous) 단일 catch
    if e.reason == "ambiguous":
        ...  # writing guide 정정 input — .metrics/ambiguous-prose.jsonl 누적
    else:
        ...  # 즉시 fail (not_found / empty)

# 프로덕션 dcness — heuristic-only (메타 LLM 호출 X)
# 휴리스틱 ambiguous → MissingSignal propagate → 메인 Claude 가 cascade
# `interpreter=` 인자는 테스트용 DI swap 만 보존
```

## 거버넌스 (필수)

본 저장소의 모든 변경은 [`CLAUDE.md`](CLAUDE.md) 에 따른다 (SSOT).

- **게이트**: main-block + git-naming + pytest (pre-commit hook 자동 실행)
- **branch → PR → merge** 필수. main 직접 push 금지.

PR 절차: [`CLAUDE.md`](CLAUDE.md) §5.

## 다음 단계

[`PROGRESS.md`](PROGRESS.md) §TODO 참조. 핵심 후보:

- Plugin 배포 dry-run — 플러그인 공존 검증
- 후속 skill `/ux` (designer + design-critic, Pencil MCP 의존) — `commands/` 카테고리 확장 후보

## Skill 목록 (`commands/`, 10개)

| 발화 | 역할 |
|---|---|
| `/init-dcness` | dcness 활성화 게이트 — 현 cwd main repo 를 plugin-scoped whitelist 추가 |
| `/qa` | 버그/이슈 분류 (FUNCTIONAL_BUG / CLEANUP / DESIGN_ISSUE / KNOWN_ISSUE / SCOPE_ESCALATE) |
| `/quick` | light path 자동화 (qa → architect LIGHT_PLAN → engineer → validator BUGFIX_VALIDATION → pr-reviewer + clean 자동 commit/PR) |
| `/product-plan` | 새 기능 spec/design (product-planner → plan-reviewer → ux-architect → validator UX → architect SD → validator DESIGN_VALIDATION → architect TASK_DECOMPOSE) |
| `/impl` | per-task 정식 impl 루프 (architect MODULE_PLAN → test-engineer → engineer → validator CODE_VALIDATION → pr-reviewer) |
| `/impl-loop` | multi-task sequential auto chain (각 task 마다 /impl 호출 + clean 자동 진행) |
| `/smart-compact` | 컨텍스트 압축 + 다음 세션 resume prompt 자동 생성 |
| `/efficiency` | Claude Code 세션 토큰/캐시/비용 분석 + HTML 대시보드 + 6 절감 휴리스틱 |
| `/run-review` | dcness conveyor run 사후 분석 — 각 step 잘한 점·잘못한 점·비용 추출, self-improvement 루프 시작점 |
| `/audit-redo` | redo-log + agent-trace 결합 분석 — (sub, mode) 별 redo 빈도 + Layer 1/2 개선 후보 제안 |

행동형 skill (`/quick` `/product-plan` `/impl` `/impl-loop`) 공통:
- yolo keyword (`yolo` / `auto` / `끝까지` / `막힘 없이` / `다 알아서`) 검출 시 CLARITY/AMBIGUOUS/ESCALATE 자동 폴백 (catastrophic 룰은 hard safety)
- worktree keyword (`worktree` / `wt` / `격리` / `isolate`) 검출 시 EnterWorktree 격리

읽기형 skill (`/qa` `/smart-compact` `/efficiency` `/run-review` `/audit-redo`) 은 keyword 무관 (read-only 분석).

## 참조 문서

| 문서 | 역할 |
|---|---|
| [`docs/plugin/prose-only-principle.md`](docs/plugin/prose-only-principle.md) | Prose-Only 원칙 현행 SSOT (대 원칙 + Anti-Pattern 5원칙) |
| [`docs/archive/status-json-mutate-pattern.md`](docs/archive/status-json-mutate-pattern.md) | Prose-Only 원전 proposal (Phase 분할 / Risks / Plugin 전환 절차) (역사 자료) |
| [`docs/archive/migration-decisions.md`](docs/archive/migration-decisions.md) | 모듈 PRESERVE / DISCARD / REFACTOR 분류 (역사 자료) |
| [`docs/archive/document_update_record.md`](docs/archive/document_update_record.md) | (frozen) 옛 WHAT 로그 — 현재는 GitHub PR/issue/git log 가 SSOT |
| [`docs/archive/change_rationale_history.md`](docs/archive/change_rationale_history.md) | (frozen) 옛 WHY 로그 — 현재는 PR description/이슈 thread/commit body 가 SSOT |
| [`PROGRESS.md`](PROGRESS.md) | 현재 상태 / TODO / Blockers |
| [`AGENTS.md`](AGENTS.md) | 외부 에이전트(Codex 등) 지침 |
| [`CLAUDE.md`](CLAUDE.md) | 메인 Claude 작업 지침 |

## License

MIT — see [`LICENSE`](LICENSE) (TBD).
