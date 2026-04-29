# dcNess Governance — Document Sync SSOT

> **Status**: ACTIVE
> **Bootstrap**: DCN-CHG-20260429-01
> **Scope**: 본 저장소(dcNess)의 모든 commit / PR / 작업자(사람·Claude Code·Codex·기타 에이전트)

## 0. 목적

코드/정책/빌드 변경 시 관련 문서가 **같은 commit** 에 함께 수정되도록 CI가 강제한다.

본 문서는 모든 거버넌스 규칙의 **SSOT (Single Source of Truth)** 다. 다른 파일은 본 문서를 *참조* 만 한다(재기술 금지).

## 1. 정체성 정합

본 거버넌스는 `docs/status-json-mutate-pattern.md` §10/§11 정합:
- 메인 Claude 직접 작업 모드 (architect/validator/engineer 위임 강제 없음)
- 본 거버넌스 시스템만 도입 (RWHarness 가드 미적용)
- 함정 회피 5원칙(§2.5) 준수: 룰 순감소, 강제 vs 권고 분리, agent 자율성, 흐름 강제 최소, hook 추가 전 측정

## 2. 명세

### 2.1 Task-ID 형식

`DCN-CHG-YYYYMMDD-NN`

- `DCN`: 프로젝트 식별자(dcNess)
- `YYYYMMDD`: 작업 시작일(KST)
- `NN`: 같은 날 내 순번(`01`–`99`, zero-pad)
- 모든 작업은 단 하나의 Task-ID. 동일 ID가 두 로그(`document_update_record.md`, `change_rationale_history.md`)를 묶는다.

### 2.2 Change-Type 토큰

| 토큰 | 감시 경로 (regex) | 의미 |
|---|---|---|
| `spec` | `^docs/spec/`, `^docs/proposals/`, `^prd\.md$`, `^trd\.md$` | 헌법 / 사양 문서 |
| `agent` | `^agents/`, `^\.claude/agent-config/` | agent prompt / 정책 |
| `harness` | `^harness/`, `^src/` | 하네스 코어 / 소스 코드 |
| `hooks` | `^hooks/`, `^\.claude/hooks/` | 차단·검증 hook |
| `ci` | `^\.github/workflows/`, `^scripts/` | CI / 빌드 / 게이트 스크립트 |
| `test` | `^tests/`, `\.test\.`, `_test\.` | 테스트 코드 |
| `docs-only` | `^docs/` (위 카테고리 미해당) | 단순 문서 |

분류 우선순위: 표의 *위에서 아래로*. 한 파일이 여러 패턴에 매칭되면 **상위** 토큰 채택.

### 2.3 작업 절차

1. **시작**: Task-ID 발급(`DCN-CHG-YYYYMMDD-NN`).
2. **수행**: 코드/문서 수정.
3. **완료 직전**:
   - `docs/process/document_update_record.md` 에 WHAT 항목 추가
   - 코드/정책/빌드 변경(2.6 §heavy)이면 `docs/process/change_rationale_history.md` 에 WHY 항목 추가
   - `PROGRESS.md` 갱신(2.6 §progress 카테고리 변경 시)
4. **commit**: `node scripts/check_document_sync.mjs` 통과 후 commit.
5. **PR**: `.github/PULL_REQUEST_TEMPLATE.md` 체크리스트 작성.
6. **리뷰**: CI 게이트 통과 + 리뷰어 승인 후 squash merge.

### 2.4 예외 처리 — `Document-Exception:`

정당한 예외(예: deliverable 디렉토리가 아직 없는 단계, 외부 의존 변경) 시 commit 메시지 또는 변경된 산출물에 다음 토큰 포함:

```
Document-Exception: <사유 한 줄>
Document-Exception-Task: DCN-CHG-YYYYMMDD-NN
```

**스코핑 규칙(절대)**:
- 예외는 **현재 diff 의 추가 라인**(`+` 로 시작)에 포함된 경우에만 유효.
- 과거 누적 엔트리(이미 머지된 로그 안의 옛 `Document-Exception`)는 **무효**.
- 예외 사용 시 `document_update_record.md` 의 해당 Task 항목에 사유 명시 필수.

### 2.5 CI 게이트 스펙 (`scripts/check_document_sync.mjs`)

**입력**:
- 로컬(인자 없음): `git diff --cached --name-only` ∪ `git diff --name-only HEAD`
- CI(`<base> <head>`): `git diff --name-only <base> <head>`

**처리**:
1. 변경 파일 목록 → §2.2 표로 토큰 분류
2. 카테고리별 필수 산출물 동반 검사(§2.6)
3. 누락 시 Document-Exception 검사(§2.4)
4. 둘 다 미충족 시 `exit 1` + 위반 항목 출력

**출력**: `[doc-sync] PASS` 또는 `[doc-sync] FAIL — violations: …`

### 2.6 카테고리별 필수 산출물

| 등장 카테고리 | 필수 동반 |
|---|---|
| **any** (모든 변경) | `docs/process/document_update_record.md` 갱신 |
| `spec` / `agent` / `harness` / `hooks` / `ci` 중 하나 이상 (§heavy) | + `docs/process/change_rationale_history.md` 갱신 |
| `harness` / `hooks` / `ci` 중 하나 이상 (§progress) | + `PROGRESS.md` 갱신 |
| `spec` 변경 시 | + `docs/spec/**` 또는 `docs/proposals/**` 안 산출물 변경 *(또는 Document-Exception)* |
| `harness` 변경 시 | + `tests/**` 또는 `docs/impl/**` 변경 *(또는 Document-Exception)* |

### 2.7 강제 메커니즘 (3중)

1. **`.git/hooks/pre-commit`** — 모든 사람. 설치: `cp scripts/hooks/pre-commit .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit`
2. **`.claude/settings.json` PreToolUse hook** — Claude Code 자동
3. **`AGENTS.md` 규칙 명시** — Codex 등 다른 에이전트 강제

CI 레벨(`.github/workflows/document-sync.yml`)은 별도 Task-ID 로 추가.

## 3. 참조 파일

이하 파일들은 본 SSOT 의 *적용 도구* 다. 규칙 재기술 금지.

| 파일 | 역할 |
|---|---|
| `docs/process/document_update_record.md` | WHAT 로그(작업별 변경 파일·요약) |
| `docs/process/change_rationale_history.md` | WHY 로그(작업별 동기·대안·결정·후속) |
| `docs/process/document_impact_matrix.md` | 변경 → 검토 문서 매핑 빠른 참조표 |
| `scripts/check_document_sync.mjs` | CI 게이트 구현 |
| `scripts/hooks/pre-commit` | git pre-commit hook |
| `scripts/hooks/cc-pre-commit.sh` | Claude Code PreToolUse hook |
| `.claude/settings.json` | Claude Code 설정(PreToolUse 등록) |
| `.github/PULL_REQUEST_TEMPLATE.md` | PR 체크리스트 |
| `AGENTS.md` | 외부 에이전트 지침 |
| `PROGRESS.md` | 현재 상태·TODO·Blockers |

## 4. SSOT 자체의 변경

본 문서 자체의 변경은 `change_rationale_history.md` 에 Task-ID 와 함께 기록한다.
