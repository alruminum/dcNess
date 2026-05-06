---
name: init-dcness
description: 현재 프로젝트를 dcNess plugin 활성 대상으로 등록하는 부트스트랩 스킬. dcNess 는 디폴트로 모든 프로젝트에서 비활성 (hook pass-through). 본 스킬 호출 시 현재 cwd 의 main repo 를 plugin-scoped whitelist (`~/.claude/plugins/data/dcness-dcness/projects.json`) 에 추가해 SessionStart / PreToolUse Agent 훅이 발화하기 시작한다. 사용자가 "init-dcness", "dcness 활성화", "이 프로젝트에 dcness 켜", "dcness 시작", "/init-dcness" 등을 말할 때 사용. 비활성화는 `/disable-dcness` (또는 본 스킬에서 status 확인 후 안내).
---

# Init dcNess Skill — 프로젝트 활성화

> dcNess plugin 은 디폴트 disabled. RWHarness 처럼 명시 활성화 필요. plugin install 만으로는 hook 발화 0 (pass-through).

## 언제 사용

- 사용자 발화: "init-dcness", "dcness 활성화", "/init-dcness", "이 프로젝트에 dcness 켜"
- 새 프로젝트에 dcness plugin 사용 시작 시
- 비활성 → 활성 전환 시

## 핵심 동작

```bash
"$(ls -d ${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/plugins/cache/dcness/dcness/*} 2>/dev/null | head -1)/scripts/dcness-helper" enable
```

- 현재 cwd 의 main repo root 추출 (γ resolution — `git rev-parse --git-common-dir`)
- `~/.claude/plugins/data/dcness-dcness/projects.json` 의 `projects` 배열에 추가 (중복 자동 제거)
- 다음 세션부터 SessionStart / PreToolUse Agent 훅 발화 시작

## 절차

### Step 1 — 현재 상태 확인

```bash
"$(ls -d ${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/plugins/cache/dcness/dcness/*} 2>/dev/null | head -1)/scripts/dcness-helper" status
```

출력 예시:
```
[dcness] cwd project root: /Users/dc.kim/project/foo
[dcness] active: NO
[dcness] whitelist file: /Users/dc.kim/.claude/plugins/data/dcness-dcness/projects.json
[dcness] no active projects (whitelist empty)
```

이미 활성 (`active: YES`) 이면 step 2 skip → step 3.

### Step 2 — 활성화

```bash
"$(ls -d ${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/plugins/cache/dcness/dcness/*} 2>/dev/null | head -1)/scripts/dcness-helper" enable
```

출력 예시:
```
[dcness] enabled: /Users/dc.kim/project/foo
[dcness] whitelist: /Users/dc.kim/.claude/plugins/data/dcness-dcness/projects.json
```

### Step 2.5 — Read 권한 부여 (`~/.claude/settings.json`)

SessionStart 훅이 plugin cache (`~/.claude/plugins/cache/dcness/**`) 안 SSOT 문서를 inject 하려면 메인 Claude 가 해당 경로 Read 허용 필요. `acceptEdits` 모드라도 plugin cache 는 디폴트 차단 → 명시적 allow 의무.

```bash
PERM='Read(~/.claude/plugins/cache/dcness/**)'
SETTINGS="$HOME/.claude/settings.json"
if [ ! -f "$SETTINGS" ]; then
  mkdir -p "$(dirname "$SETTINGS")"
  printf '{"permissions":{"allow":[]}}\n' > "$SETTINGS"
fi
if command -v jq >/dev/null 2>&1; then
  if jq -e --arg p "$PERM" '(.permissions.allow // []) | index($p)' "$SETTINGS" >/dev/null; then
    echo "[dcness] permission 이미 존재: $PERM"
  else
    tmp=$(mktemp)
    jq --arg p "$PERM" '.permissions = (.permissions // {}) | .permissions.allow = ((.permissions.allow // []) + [$p] | unique)' "$SETTINGS" > "$tmp" && mv "$tmp" "$SETTINGS"
    echo "[dcness] permission 추가: $PERM → $SETTINGS"
  fi
else
  echo "[dcness] WARN — jq 미설치. $SETTINGS .permissions.allow 에 '$PERM' 수동 추가 필요" >&2
fi
```

출력 예시 (신규 추가):
```
[dcness] permission 추가: Read(~/.claude/plugins/cache/dcness/**) → /Users/dc.kim/.claude/settings.json
```

이미 등록된 사용자는 멱등 — `이미 존재` 메시지.

### Step 2.6 — git-naming 강제 (commit-msg hook + CI)

브랜치명·커밋·PR 제목 형식 위반을 로컬과 CI 양쪽에서 자동 차단한다.

```bash
PLUGIN_ROOT="$(ls -d ${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/plugins/cache/dcness/dcness/*} 2>/dev/null | head -1)"
PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"

# 1. check_git_naming.mjs 배포 (commit-msg hook + CI 의존)
mkdir -p "$PROJECT_ROOT/scripts"
if [ ! -f "$PROJECT_ROOT/scripts/check_git_naming.mjs" ]; then
  cp "$PLUGIN_ROOT/scripts/check_git_naming.mjs" "$PROJECT_ROOT/scripts/"
  echo "[dcness] scripts/check_git_naming.mjs 배포"
else
  echo "[dcness] scripts/check_git_naming.mjs 이미 존재 — skip"
fi

# 2. GitHub Actions workflow 배포
mkdir -p "$PROJECT_ROOT/.github/workflows"
if [ ! -f "$PROJECT_ROOT/.github/workflows/git-naming-validation.yml" ]; then
  cp "$PLUGIN_ROOT/.github/workflows/git-naming-validation.yml" "$PROJECT_ROOT/.github/workflows/"
  echo "[dcness] .github/workflows/git-naming-validation.yml 배포"
else
  echo "[dcness] git-naming-validation.yml 이미 존재 — skip"
fi

# 3. commit-msg hook 설치
if [ ! -f "$PROJECT_ROOT/.git/hooks/commit-msg" ]; then
  cp "$PLUGIN_ROOT/scripts/hooks/commit-msg" "$PROJECT_ROOT/.git/hooks/commit-msg"
  chmod +x "$PROJECT_ROOT/.git/hooks/commit-msg"
  echo "[dcness] .git/hooks/commit-msg 설치"
else
  echo "[dcness] .git/hooks/commit-msg 이미 존재 — skip"
fi

# 4. dcness-guidelines.md 배포 (SessionStart 훅이 읽는 파일)
mkdir -p "$PROJECT_ROOT/docs/process"
cp "$PLUGIN_ROOT/docs/process/dcness-guidelines.md" "$PROJECT_ROOT/docs/process/dcness-guidelines.md"
echo "[dcness] docs/process/dcness-guidelines.md 배포"
```

출력 예시:
```
[dcness] scripts/check_git_naming.mjs 배포
[dcness] .github/workflows/git-naming-validation.yml 배포
[dcness] .git/hooks/commit-msg 설치
[dcness] docs/process/dcness-guidelines.md 배포
```

`git-naming-validation.yml` 은 PR open 시 CI 에서 브랜치명·PR 제목을 자동 검사한다. `commit-msg` hook 은 로컬에서 커밋 제목을 사전 차단한다. 두 파일은 커밋 후 프로젝트 repo 에 push 해야 CI 에서 동작한다.

### Step 2.7 — design.md SSOT awareness

dcness plug-in 의 디자인 시스템 SSOT 는 `docs/design.md` (Google `design.md` 공식 spec 채택). plug-in agents (designer / ux-architect / engineer / validator/code-validation 등) 가 UI 작업 시 read 한다. 활성화 프로젝트가 UI 를 다루면 본 SSOT 를 인지/활용해야 plug-in 룰이 완전 작동.

본 Step 은 **bash 자동화 X — 메인 Claude 가 절차 따라 사용자 응답 받고 진행**. 두 단계 모두 멱등.

#### 1. 사용자 CLAUDE.md 매트릭스 패치 제안

프로젝트 root 의 `CLAUDE.md` 가 존재하면 read.

- 파일 부재 시 본 단계 skip.
- "lazy 읽기" / "작업 시 읽기" 매트릭스 안에 `docs/design.md` 행 부재 시 다음을 사용자에게 출력:

  ```
  [dcness] CLAUDE.md 매트릭스에 design.md 행이 없습니다. 다음 행을 추가할까요?

  | docs/design.md | UI 모듈 작업 / 디자인 시스템 변경 시 |

  → §3 (또는 동등) lazy 매트릭스에 추가합니다. (Y/n)
  ```

- 사용자 답변 받은 후에만 메인 Claude 가 Edit 으로 박음. 답 없이 silent skip 금지 — 명시적 응답 1회 의무.
- 이미 `docs/design.md` 행 있으면 본 단계 skip (`이미 등록됨 — skip` 출력).

#### 2. UI 프로젝트 여부 + design.md 템플릿 시드

```
[dcness] 이 프로젝트는 UI (화면 / 컴포넌트 / 시각 디자인) 를 다룹니까? (Y/n)
```

- **n**: 본 단계 종료 (예: dcness self / 백엔드 전용 / CLI 도구).
- **Y**: `docs/design.md` 부재 시 다음 minimal 템플릿 출력 + Write 동의 1회 질문:

  ```yaml
  ---
  version: alpha
  name: <project name>
  description: |
    <atmosphere 한 줄: 브랜드 톤 + 타입 voice + 컬러 철학>

  colors:
    primary: "#hex"
    neutral: "#hex"
    canvas: "#hex"
  typography:
    headline-lg:
      fontFamily: "Inter, sans-serif"
      fontSize: 32px
      fontWeight: 600
      lineHeight: 1.2
  ---

  ## Overview
  <프로젝트의 전반적 시각 톤 / 정체성 묘사>

  ## Colors
  - **Primary** (`{colors.primary}` — #hex): primary CTA / 강조 요소
  - **Canvas** (`{colors.canvas}` — #hex): 페이지 배경
  ```

  ```
  [dcness] 위 템플릿을 docs/design.md 로 생성할까요? (Y/n)
  ```

  사용자 동의 시 메인 Claude 가 `docs/design.md` Write. 거절 시 skip.

- 이미 `docs/design.md` 파일 존재하면 본 단계 skip (`이미 존재 — skip`).

#### 3. 멱등 보장

- 두 번 실행해도 추가 변경 없음 — 매트릭스 행 있으면 1번 skip / `docs/design.md` 있으면 2번 skip.
- 사용자가 \"n\" 답변 시 다음 호출 때 다시 묻지 않게 하려면 별도 marker 필요 (v1 범위 외 — 매번 묻되 사용자가 빠르게 \"n\" 가능).

#### 4. 출처 / 갱신 의무

본 Step inline 템플릿은 `docs/design.md` (dcness self repo) §사용 예시와 coupling — Story #125 의 spec 변경 시 본 Step 템플릿도 **수동 동기 의무**. 자동화 검토는 Epic #129 후속 추적.

#### 5. 기존 활성화 프로젝트 — re-run 안내

이미 `/init-dcness` 활성화한 기존 프로젝트는 본 Step 2.7 가 자동 발화하지 않음. 사용자가 본 plug-in 업데이트 받은 후 `/init-dcness` 재실행해야 Step 2.7 발화. 본 안내는 dcness release note / README 에 별도 명시.

### Step 3 — 사용자 안내

```
[dcness] 활성화 완료
- 프로젝트: <main repo root>
- whitelist: ~/.claude/plugins/data/dcness-dcness/projects.json

다음 세션부터 발화하는 것:
- SessionStart 훅 — by-pid / live.json 자동 생성
- PreToolUse Agent 훅 — catastrophic 룰 (orchestration.md §2.3) 검사

git-naming 강제 (Step 2.6 완료 시):
- 로컬: .git/hooks/commit-msg — 커밋 제목 형식 위반 차단
- CI: .github/workflows/git-naming-validation.yml — 브랜치명·PR 제목 위반 차단
- scripts/check_git_naming.mjs 를 커밋 후 push 해야 CI 활성화
- docs/process/dcness-guidelines.md 배포 — SessionStart 훅이 세션마다 읽는 룰 파일

design.md SSOT (Step 2.7 완료 시):
- CLAUDE.md 매트릭스에 docs/design.md 행 등록 (UI 작업 시 read 후보)
- (UI 프로젝트인 경우) docs/design.md minimal 템플릿 시드 — 컬러 / 타이포그래피 / 컴포넌트 토큰 채워 사용

사용 가능한 skill:
- /qa  — 이슈 분류
- /quick — 작은 버그픽스 light path
- /product-plan — 새 기능 spec/design
- /smart-compact — 컨텍스트 압축 + resume prompt

비활성화 — `/disable-dcness` 또는 `"$(ls -d ${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/plugins/cache/dcness/dcness/*} 2>/dev/null | head -1)/scripts/dcness-helper" disable`.

** Claude Code 세션 재시작 권장** — SessionStart 훅은 현재 세션엔 적용 안 됨.
```

### Step 4 (선택) — `harness/` 모듈 import 검증

cross-project 시나리오에선 plugin hook 이 `${CLAUDE_PLUGIN_ROOT}` 를 PYTHONPATH 에 추가해
`harness.session_state` import 가능. dcNess repo 안에서 직접 활성화하는 경우 cwd 가 plugin
root 가 아니라도 `harness/` 가 cwd 에 있으니 정상 동작.

문제 발생 시:
```bash
python3 -c "import harness.session_state; print('OK')"
```

`ModuleNotFoundError` 면 plugin 설치 누락 → `claude plugin install dcness@dcness` 재실행.

## ⚠️ 재설치 시 재실행 필수

`claude plugin uninstall dcness@dcness && claude plugin install dcness@dcness` 시
`~/.claude/plugins/data/dcness-dcness/` 가 CC 에 의해 정리됨 → whitelist 소실 → 모든 프로젝트
inactive 로 회귀. 재설치 후엔 각 활성 프로젝트마다 `/init-dcness` 다시 실행 필요.

`~/.claude/settings.json` 의 Read 권한 (Step 2.5) 은 재설치 시에도 보존 (CC 가 settings 자동 정리 X). `/init-dcness` 재실행 시 멱등 — 이미 있으면 skip.

## 한계 / 후속

- **세션 재시작 필요** — SessionStart 훅은 *세션 시작 시점* 에 한 번 발화. 활성화 직후 현재 세션에는 by-pid 미생성. 새 `claude` 세션 띄워야 hook 발화 시작.
- **`/disable-dcness` skill 미구현 (v1)** — 본 skill 의 cousin. 명시 비활성화 진입점. v2 후속.
- **whitelist 파일 직접 편집 가능** — 관리/감사 시 `cat ~/.claude/plugins/data/dcness-dcness/projects.json` 으로 확인. 손편집 권장 X (atomic write 컨벤션 우회).
- **plugin uninstall 시 자동 cleanup** — CC 가 `data/` 디렉토리 자동 정리 (CC 공식 컨벤션). dcness 만 제거하면 whitelist 도 함께 소실.

## 참조

- `harness/session_state.py` — `is_project_active` / `enable_project` / `disable_project` / CLI subcommands
- `hooks/session-start.sh` / `hooks/catastrophic-gate.sh` — 첫 줄에 `is-active` 게이트
- `docs/conveyor-design.md` §13 — worktree γ resolution (활성화도 main repo 기준)
- RWHarness `init-rwh` — 패턴 참조 (whitelist 위치는 글로벌 `~/.claude/harness-projects.json` 대신 plugin-scoped `~/.claude/plugins/data/dcness-dcness/projects.json`)
