---
name: init-dcness
description: 현재 프로젝트를 dcNess plugin 활성 대상으로 등록하는 부트스트랩 스킬. dcNess 는 디폴트로 모든 프로젝트에서 비활성 (hook pass-through). 본 스킬 호출 시 현재 cwd 의 main repo 를 plugin-scoped whitelist (`~/.claude/plugins/data/dcness-dcness/projects.json`) 에 추가해 SessionStart / PreToolUse Agent 훅이 발화하기 시작한다. 사용자가 "init-dcness", "dcness 활성화", "이 프로젝트에 dcness 켜", "dcness 시작", "/init-dcness" 등을 말할 때 사용. 비활성화는 `/disable-dcness` (또는 본 스킬에서 status 확인 후 안내).
---

# Init dcNess Skill — 프로젝트 활성화

> dcNess plugin 은 디폴트 disabled. 명시 활성화 필요. plugin install 만으로는 hook 발화 0 (pass-through).

## 언제 사용

- 사용자 발화: "init-dcness", "dcness 활성화", "/init-dcness", "이 프로젝트에 dcness 켜"
- 새 프로젝트에 dcness plugin 사용 시작 시
- 비활성 → 활성 전환 시

## 핵심 동작

```bash
"$(ls -d ${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/plugins/cache/dcness/dcness/*} 2>/dev/null | sort -V | tail -1)/scripts/dcness-helper" enable
```

- 현재 cwd 의 main repo root 추출 (γ resolution — `git rev-parse --git-common-dir`)
- `~/.claude/plugins/data/dcness-dcness/projects.json` 의 `projects` 배열에 추가 (중복 자동 제거)
- 다음 세션부터 SessionStart / PreToolUse Agent 훅 발화 시작

## 절차

### Step 1 — 현재 상태 확인

```bash
"$(ls -d ${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/plugins/cache/dcness/dcness/*} 2>/dev/null | sort -V | tail -1)/scripts/dcness-helper" status
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
"$(ls -d ${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/plugins/cache/dcness/dcness/*} 2>/dev/null | sort -V | tail -1)/scripts/dcness-helper" enable
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

### Step 2.6 — git-naming 강제 (thin shim, fat plugin)

브랜치명·커밋·PR 제목 형식 위반을 로컬과 (선택적으로) CI 양쪽에서 자동 차단한다.

> **#198 정정**: mjs / dcness-rules.md 는 사용자 repo 에 cp 안 한다 — plugin SSOT 직접 호출. commit-msg hook 만 thin shim 으로 always-overwrite 한다 (`.git/hooks/` 위치 강제 + plugin 업데이트 자동 갱신).

```bash
PLUGIN_ROOT="$(ls -d ${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/plugins/cache/dcness/dcness/*} 2>/dev/null | sort -V | tail -1)"
PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"

# 1. commit-msg hook (thin shim) — always-overwrite
#    내용은 plugin path 동적 resolve + check_git_naming.mjs 호출 1줄. 본체 로직 plugin 안.
cp "$PLUGIN_ROOT/scripts/hooks/commit-msg" "$PROJECT_ROOT/.git/hooks/commit-msg"
chmod +x "$PROJECT_ROOT/.git/hooks/commit-msg"
echo "[dcness] .git/hooks/commit-msg 갱신 (thin shim → plugin SSOT 호출)"

# 2. post-checkout hook (thin shim) — always-overwrite
#    브랜치 생성/전환 직후 브랜치명 형식 검증 (위반 시 경고 + git branch -m 안내)
cp "$PLUGIN_ROOT/scripts/hooks/post-checkout" "$PROJECT_ROOT/.git/hooks/post-checkout"
chmod +x "$PROJECT_ROOT/.git/hooks/post-checkout"
echo "[dcness] .git/hooks/post-checkout 갱신 (thin shim → plugin SSOT 호출)"

# 3. pre-push hook (thin shim) — always-overwrite
#    push 전 브랜치명 형식 검증 — local PASS / 원격 CI FAIL mismatch 회귀 차단 (#255 W4)
#    main 직접 push 차단 + 브랜치명 위반 차단 둘 다 수행.
cp "$PLUGIN_ROOT/scripts/hooks/pre-push" "$PROJECT_ROOT/.git/hooks/pre-push"
chmod +x "$PROJECT_ROOT/.git/hooks/pre-push"
echo "[dcness] .git/hooks/pre-push 갱신 (thin shim → plugin SSOT 호출, 브랜치명 검증 + main push 차단)"

# 4. legacy 정리 안내 — 옛 cp 패턴 잔재 제거 권고
if [ -f "$PROJECT_ROOT/scripts/check_git_naming.mjs" ]; then
  echo "[dcness] NOTE — scripts/check_git_naming.mjs 가 사용자 repo 에 잔존. 이제 plugin SSOT 에서 호출하므로 제거 권장:"
  echo "         git rm scripts/check_git_naming.mjs"
fi
if [ -f "$PROJECT_ROOT/docs/plugin/skill-guidelines.md" ]; then
  echo "[dcness] NOTE — docs/plugin/skill-guidelines.md 가 사용자 repo 에 잔존. session-start.sh 가 이제 plugin SSOT 에서 read. 제거 권장:"
  echo "         git rm docs/plugin/skill-guidelines.md"
fi
```

#### 3. CI 강제 — 사용자 선택 (옵션)

GitHub Actions 에서 git-naming 강제 원하는지 묻는다.

```
[dcness] GitHub Actions CI 에서 git-naming 강제할까요?
  - PR open / sync 시마다 브랜치명 + PR 제목 자동 검증
  - 본 thin yml 1개만 사용자 repo 에 깔리고, 검증 본체는 alruminum/dcNess composite action 호출
  - 로컬 commit-msg hook 만으로 충분하면 n
(Y/n)
```

- **Y**: 다음 thin yml 을 `$PROJECT_ROOT/.github/workflows/git-naming-validation.yml` 로 *always-overwrite* (이미 존재해도 갱신 — plugin 업데이트 자동 반영):

  ```yaml
  name: git-naming-validation
  on:
    pull_request:
      branches: [main]
      types: [opened, synchronize, reopened, edited]
  permissions:
    contents: read
    pull-requests: read
  jobs:
    naming:
      name: git-naming-spec gate
      runs-on: ubuntu-latest
      steps:
        - uses: alruminum/dcNess/.github/actions/git-naming@main
          with:
            branch: ${{ github.head_ref }}
            title: ${{ github.event.pull_request.title }}
  ```

  - 사용자 repo 에 mjs / 검증 로직 본체 cp 0 — 모두 dcNess repo composite action 안.
  - 사용자가 `@main` 대신 `@v1.2.3` 등 tag pin 으로 버전 고정 가능.
  - 머지 후 push → 다음 PR 부터 CI 자동 발화.

- **n**: skip. 로컬 commit-msg hook 만으로 강제 (push 전 차단).

출력 예시 (Y 선택):
```
[dcness] .git/hooks/commit-msg 갱신 (thin shim → plugin SSOT 호출)
[dcness] .github/workflows/git-naming-validation.yml 갱신 (composite action 호출)
[dcness] CI 활성화 — 머지 후 push 시 다음 PR 부터 발화
```

#### 4. PR body close-keyword 게이트 — 사용자 선택 (옵션)

GitHub Actions 에서 PR body `Closes #N` 키워드 강제 원하는지 묻는다.

```
[dcness] GitHub Actions CI 에서 PR body close-keyword 강제할까요?
  - PR open / edit / sync 시마다 PR body 에 `Closes #N` (또는 Fixes/Resolves) 1+ 매치 강제
  - 본 프로젝트는 regular merge → commit message 안 Closes 만으론 issue auto-close 안 됨 (PR body 만 인식)
  - 예외 우회: PR body 에 `Document-Exception-PR-Close: <사유>` line 박으면 통과
  - 본 thin yml 1개만 사용자 repo 에 깔리고, 검증 본체는 alruminum/dcNess composite action 호출
  - issue lifecycle 강제 안 하면 n
(Y/n)
```

- **Y**: 다음 thin yml 을 `$PROJECT_ROOT/.github/workflows/pr-body-validation.yml` 로 *always-overwrite*:

  ```yaml
  name: pr-body-validation
  on:
    pull_request:
      branches: [main]
      types: [opened, synchronize, reopened, edited]
  permissions:
    contents: read
    pull-requests: read
  jobs:
    pr-body:
      name: PR body close-keyword gate
      runs-on: ubuntu-latest
      steps:
        - uses: alruminum/dcNess/.github/actions/pr-body@main
          with:
            body: ${{ github.event.pull_request.body }}
  ```

  - 사용자 repo 에 mjs / 검증 로직 본체 cp 0 — 모두 dcNess repo composite action 안.
  - 머지 후 push → 다음 PR 부터 CI 자동 발화.

- **n**: skip. issue auto-close 는 메인 Claude 자율 (회귀 위험 — 본 게이트 권장).

출력 예시 (Y 선택):
```
[dcness] .github/workflows/pr-body-validation.yml 갱신 (composite action 호출)
[dcness] PR body close-keyword 게이트 활성화
```

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

본 Step inline 템플릿은 `docs/plugin/design.md` (dcness self repo) §사용 예시와 coupling — Story #125 의 spec 변경 시 본 Step 템플릿도 **수동 동기 의무**. 자동화 검토는 Epic #129 후속 추적.

#### 5. 기존 활성화 프로젝트 — re-run 안내

이미 `/init-dcness` 활성화한 기존 프로젝트는 본 Step 2.7 가 자동 발화하지 않음. 사용자가 본 plug-in 업데이트 받은 후 `/init-dcness` 재실행해야 Step 2.7 발화. 본 안내는 dcness release note / README 에 별도 명시.

### Step 2.8 — 초기 docs 폼 시드 (PRD / ARCHITECTURE / ADR)

신규 프로젝트가 기획 논의 후 채워넣을 표준 placeholder 3종을 시드한다. *부재할 때만* 깔리며 (멱등), 이미 존재하면 skip — 사용자 작업물 보호.

본 Step 은 **bash 자동화 X — 메인 Claude 가 절차 따라 사용자 응답 받고 진행**.

용도:

- `docs/PRD.md` — 목표 / 사용자 / 핵심 기능 / MVP 제외 / 수용 기준 / 디자인 방향
- `docs/ARCHITECTURE.md` — 디렉토리 / 패턴 / 데이터 흐름 / 상태 관리 / 외부 의존성
- `docs/ADR.md` — 철학 + 첫 ADR 자리 (placeholder 다수 박지 않음 — 억지 채움 방지)

UI 폼은 Step 2.7 의 `docs/design.md` 가 담당 — 별도 `UI_GUIDE.md` 안 깐다.

#### 1. 프로젝트 docs 디렉토리 확인

```bash
PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"
mkdir -p "$PROJECT_ROOT/docs"
```

#### 2. 부재 파일 시드 (3개 각각 멱등)

각 파일에 대해:

```
[dcness] docs/PRD.md 가 없습니다. 기획 논의 후 채울 placeholder 폼을 깔까요? (Y/n)
```

- 사용자 답변 받은 후에만 메인 Claude 가 plug-in 의 `templates/project-init/<FILE>.md` 를 사용자 repo `docs/<FILE>.md` 로 cp.
- 이미 파일 존재 시 묻지 않고 `이미 존재 — skip` 출력.

```bash
PLUGIN_ROOT="$(ls -d ${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/plugins/cache/dcness/dcness/*} 2>/dev/null | sort -V | tail -1)"
PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"

for FILE in PRD.md ARCHITECTURE.md ADR.md; do
  if [ -f "$PROJECT_ROOT/docs/$FILE" ]; then
    echo "[dcness] docs/$FILE 이미 존재 — skip"
  else
    # 사용자 동의 (Y/n) 받은 후에만 cp 실행. 동의 없이 silent cp 금지.
    cp "$PLUGIN_ROOT/templates/project-init/$FILE" "$PROJECT_ROOT/docs/$FILE"
    echo "[dcness] docs/$FILE 시드 완료 — 기획 논의 후 채워넣으세요"
  fi
done
```

#### 3. 멱등 보장

- 두 번 실행해도 추가 변경 없음 — 파일 있으면 skip.
- 사용자가 \"n\" 답변 시 다음 호출 때 다시 묻되 사용자가 빠르게 \"n\" 가능.

#### 4. 출처 / 갱신 의무

본 Step 이 cp 하는 폼은 plug-in `templates/project-init/{PRD,ARCHITECTURE,ADR}.md` 가 SSOT. 폼 형식 변경 시 본 디렉토리에서 갱신 — 사용자 repo 의 기존 파일은 cp 대상 아니므로 자동 반영 안 됨 (사용자 작업물 보호 원칙).

#### 5. 기존 활성화 프로젝트 — re-run 안내

이미 `/init-dcness` 활성화한 기존 프로젝트는 본 Step 2.8 이 자동 발화하지 않음. 사용자가 본 plug-in 업데이트 받은 후 `/init-dcness` 재실행해야 Step 2.8 발화. 단 시드는 *부재 시만* 이라 기존 docs 가 있으면 skip — 안전.

### Step 2.9 — TDD 게이트 (옵션, polyglot universal + affected detection)

GitHub Actions CI 에서 *PR 머지 전 affected 테스트 PASS 강제*. branch protection 의 `required status check` 에 등록되면 진짜 mechanical wall (admin 외 우회 불가) 가 됨.

> **배경 (#320 #1)**: jajang Epic 12 task 03 에서 plan §3.5 가 `useAuthStore 기존 (변경 X)` 명시했는데 engineer 가 selector 패턴으로 바꿔서 *기존* 26 테스트 깨짐. CI 테스트 게이트 + branch protection 으로 mechanical 차단.

> **phase 3 — affected detection 자동**: composite action 이 4 언어 (node / python / rust / go) 자동 검출 + 변경분 affected 만 실행. 사용자 설정 0.
>
> - **node**: nx / turbo / pnpm workspaces 자동 검출 → `nx affected` / `turbo --filter=...[base]` / `pnpm -F "...[base]"` (dependency 그래프 자동 포함). 단일 패키지 / yarn classic / npm workspaces → 풀 폴백.
> - **python**: 변경 `.py` 파일의 *가장 가까운 상위* `pyproject.toml` / `setup.py` 식별 → 그 안에서만 pytest. 변경 0건 → skip.
> - **rust**: `[workspace]` 검출 시 변경 파일 → member 매핑 → `cargo test -p <member>`. 단일 crate → `cargo test`.
> - **go**: 변경 `.go` 파일의 package path 추출 → `go test ./<path>/...`. 변경 0건 → skip.
>
> jajang (apps/mobile=js + apps/api=python) 같은 polyglot 모노레포 자동 cover — 웹 변경 = mobile 테스트만, api 변경 = api 테스트만.

#### 1. 지원 언어 검출

다음 마커 중 1+ 매치 시 TDD 게이트 적용 가능:

| 언어 | 검출 마커 | 테스트 명령 |
|---|---|---|
| node | `package.json` | `<pm> test` (pm = pnpm/yarn/bun/npm 자동) |
| python | `pyproject.toml` / `setup.py` / `setup.cfg` / `requirements*.txt` | `pytest` (unittest 자동 검출 포함) |
| rust | `Cargo.toml` | `cargo test --all` |
| go | `go.mod` | `go test ./...` |

```bash
PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"
HAS_SUPPORTED=false
[ -f "$PROJECT_ROOT/package.json" ] && HAS_SUPPORTED=true
[ -f "$PROJECT_ROOT/pyproject.toml" ] || [ -f "$PROJECT_ROOT/setup.py" ] \
  || [ -f "$PROJECT_ROOT/setup.cfg" ] \
  || ls "$PROJECT_ROOT"/requirements*.txt 2>/dev/null | grep -q . \
  && HAS_SUPPORTED=true
[ -f "$PROJECT_ROOT/Cargo.toml" ] && HAS_SUPPORTED=true
[ -f "$PROJECT_ROOT/go.mod" ] && HAS_SUPPORTED=true
if [ "$HAS_SUPPORTED" = "false" ]; then
  echo "[dcness] 지원 언어 (node/python/rust/go) 검출 안 됨 — TDD 게이트 skip"
  # Step 2.9 종료
fi
```

지원 외 (Elixir / Ruby / Java / .NET / PHP / Swift 등) 는 phase 3 후속. 본 단계 silent skip.

#### 2. 사용자 옵트인

지원 언어 검출 시 사용자에게 묻는다.

```
[dcness] GitHub Actions CI 에서 TDD 게이트 강제할까요?
  - PR 마다 affected 테스트 자동 실행 — 1건이라도 FAIL 시 PR 머지 차단 (branch protection 필요)
  - polyglot universal — node / python / rust / go 자동 검출
  - 변경분 기반 (사용자 설정 0):
    - node: nx / turbo / pnpm workspaces 자동 detect → affected 만. 의존성 그래프 자동 포함.
    - python: 변경 .py 의 root pyproject 식별 → 그 안에서만 pytest
    - rust: workspace 멤버 자동 매핑 → cargo test -p <member>
    - go: 변경 package path 만 → go test ./<path>/...
  - 본 thin yml 1개만 사용자 repo 에 깔리고, 검증 본체는 alruminum/dcNess composite action 호출
  - 로컬에서만 테스트 돌리고 CI 강제 원치 않으면 n
(Y/n)
```

- **Y**: 다음 thin yml 을 `$PROJECT_ROOT/.github/workflows/tdd-gate.yml` 로 *always-overwrite* (이미 존재해도 갱신):

  ```yaml
  name: tdd-gate
  on:
    pull_request:
      branches: [main]
      types: [opened, synchronize, reopened]
  permissions:
    contents: read
  jobs:
    test:
      name: TDD gate (full test suite)
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v4
        - uses: alruminum/dcNess/.github/actions/tdd-gate@main
  ```

  - 사용자 repo 에 검증 로직 cp 0 — package manager 검출 / install / test 실행 전부 dcNess composite action 안.
  - 사용자가 `@main` 대신 `@v1.2.3` 등 tag pin 으로 버전 고정 가능.
  - 머지 후 push → 다음 PR 부터 CI 자동 발화.

- **n**: skip. 로컬 hook + 사용자 자율로만 테스트 enforce. CI 우회 가능 — 회귀 위험 ↑.

출력 예시 (Y 선택):
```
[dcness] .github/workflows/tdd-gate.yml 갱신 (composite action 호출)
[dcness] TDD 게이트 활성화 — 머지 후 push 시 다음 PR 부터 발화
```

#### 3. branch protection 안내 (사용자 수동 실행 권유)

CI workflow 깔린 것만으론 *PR 머지를 차단* 안 됨 — branch protection 의 `required status checks` 에 등록되어야 진짜 wall. 아래 명령 안내:

```
[dcness] TDD 게이트가 진짜 mechanical wall 이 되려면 GitHub Branch Protection 의 required status check 에 'TDD gate (full test suite)' 등록 필요.

자동 설정 (admin 권한 시):
  gh api -X PUT repos/<OWNER>/<REPO>/branches/main/protection \
    -f required_status_checks.strict=true \
    -f 'required_status_checks.contexts[]=TDD gate (full test suite)' \
    -f enforce_admins=null \
    -f required_pull_request_reviews=null \
    -f restrictions=null

또는 GitHub UI 에서: Settings → Branches → main → Edit → 'Require status checks to pass before merging' → 'TDD gate (full test suite)' 검색 후 추가

(주의 — 첫 PR 1건 이상 CI 통과 후에만 GitHub 가 status check 후보 인식. 처음엔 PR 띄운 후 등록.)
```

본 안내는 *출력만* — 메인 Claude 가 사용자 권한 확인 후 자동 실행할지 사용자 결정에 위임 (admin 권한 가정 위험 회피).

#### 4. 한계 (phase 3)

- 지원 언어 4 (node / python / rust / go) — Elixir / Ruby / Java / .NET / PHP / Swift 는 phase 4 후속.
- branch protection 자동 설정 안 함 — admin 권한 가정 위험. 안내문만 출력.
- python: poetry / pdm / uv 같은 modern tooling = pip 폴백. 진정한 native 지원은 phase 4.
- python/rust/go 의 dependency 그래프 자동 포함 = phase 4 (현재는 path 기반).
- node yarn classic / npm workspaces / bun = 풀 스위트 폴백 (native affected filter 약함).
- rust: toolchain pin 필요 시 사용자 workflow 에서 추가. 기본은 ubuntu-latest 의 stable.

#### 5. 기존 활성화 프로젝트 — re-run 안내

이미 `/init-dcness` 활성화한 기존 프로젝트는 본 Step 2.9 가 자동 발화하지 않음. 사용자가 본 plug-in 업데이트 받은 후 `/init-dcness` 재실행해야 발화.

### Step 2.10 — Pre-commit TDD 게이트 (옵션, commit 단 차단)

CI tdd-gate (Step 2.9) 가 *PR 머지 차단* 인 반면, 본 Step 2.10 은 *commit 자체 차단* — 깨진 코드가 *push 전*, *PR 전* 단계에서 거름. branch protection 의존성 0 — 진짜 자체완결 wall.

> **배경 (#320 #1 phase 4)**: CI 게이트 는 branch protection 등록 *후* 만 wall. 사용자 추가 설정 의존성. 또한 `gh pr checks --watch` 강제 (git-naming-spec §6) 가 Claude 흐름 병목. commit-msg hook 으로 commit 단 차단 = 사용자 추가 설정 0 + 즉시 발화.

> **진짜 TDD**: test-engineer 작성 test → engineer 구현 → test 통과해야 commit. *변경분 test 만* 실행 (5~15개 단위, 수초). 풀 스위트 아님.

#### 1. 룰

commit-msg hook 발화 시점에:

1. **옵트인 마커 검사** — `.dcness/tdd-gate-enabled` 파일 없으면 silent PASS (다른 프로젝트 영향 회피)
2. **skip marker 검사** — commit message 안 `[skip-test: <사유>]` 매치 → PASS (단순 typo / 문서 변경 우회)
3. **staged 분석**:
   - `staged_src` = staged 안 코드 확장자 파일 (test 제외)
   - `staged_test` + `branch_diff_test` (origin/main...HEAD 의 test) → `all_test`
4. **분기**:
   - `staged_src` 0 → PASS (docs / config 변경)
   - `staged_src` 1+ 있고 `all_test` 0 → BLOCK
   - `all_test` 1+ → 그 test 실행 → 1건이라도 FAIL → BLOCK

#### 2. 사용자 옵트인

```
[dcness] Pre-commit TDD 게이트 활성화할까요?
  - staged 안 src 변경 = test 변경 함께 staged 또는 같은 branch 안 있어야 commit 통과
  - 검출된 test 만 실행 (5~15개 단위, 수초) — 풀 스위트 X
  - 4 언어 자동 검출 (node jest/vitest, python pytest, rust cargo, go go test)
  - dcness 의 3-commit 구조 (docs/tests/src) 와 자연 정합 — commit2 의 test 가 branch diff 에 인식됨
  - 우회: commit message 에 `[skip-test: <사유>]` marker
  - 옵트인 마커 `.dcness/tdd-gate-enabled` 가 활성화 신호. 다른 프로젝트 영향 0.
(Y/n)
```

- **Y**:
  - `.dcness/tdd-gate-enabled` 빈 파일 작성 (git add 권장 — 팀 공유)
  - 사용자에게 commit-msg shim 이 이미 깔려있음을 안내 (Step 2.6 의 thin shim 이 자동으로 TDD 게이트 chain 호출)
- **n**: skip — 마커 작성 안 함. hook 은 silent pass-through.

```bash
PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"
mkdir -p "$PROJECT_ROOT/.dcness"
touch "$PROJECT_ROOT/.dcness/tdd-gate-enabled"
echo "[dcness] .dcness/tdd-gate-enabled 마커 작성 — pre-commit TDD 게이트 활성. 다음 commit 부터 발화."
echo "[dcness] 권장: git add .dcness/tdd-gate-enabled (팀 공유)"
```

#### 3. 3-commit 구조 정합

dcness 의 impl-task-loop 가 박는 3-commit (loop-procedure §3.4):

| commit | stage | staged_src | all_test | TDD 게이트 |
|---|---|---|---|---|
| commit1 (docs) | `docs/impl/NN-*.md` | 0 | 0 | PASS |
| commit2 (tests) | `src/__tests__/**` | 0 (test 만) | branch test | PASS + test 실행 |
| commit3 (src) | `src/**` + stories.md | 있음 | commit2 의 test 가 branch diff 에 인식 | PASS + test 실행 |

위반 (3-commit 구조 우회 / 임의 commit):
- src 만 stage, test 0 → BLOCK
- 사용자 `[skip-test: <사유>]` marker 또는 test 추가 후 재시도

#### 4. 한계 (v0.2.13)

- node test runner: jest / vitest 자동. 그 외 (mocha / ava 등) → `npm test` 폴백
- python: `pytest <files>` 직접. unittest 만 쓰는 프로젝트 면 marker 우회
- rust: 단순화 — `cargo test` 풀 폴백 (변경 test 파일만 실행 native 한계)
- go: 변경 test 의 dirname → `go test ./<dir>/...`
- 형식 강제 + 실행 강제 둘 다 — 변경분만이라 빠름 (수초)

#### 5. 기존 활성화 프로젝트 — re-run 안내

이미 `/init-dcness` 활성화한 기존 프로젝트는 본 Step 2.10 이 자동 발화하지 않음. plug-in 업데이트 + `/init-dcness` 재실행 시 발화. commit-msg shim 은 이미 chain 로직 박혀있어 마커만 작성하면 즉시 동작.

### Step 2.11 — 자동 commit + PR (인프라 머지 자동화)

Step 2.6 ~ 2.10 까지 *깔린 파일들* (workflow yml / `.dcness/` 마커 등) 은 working tree 변경 상태로 머무름 — 사용자가 git add / commit / push / PR 까지 직접 진행하지 않으면 **main 머지 안 됨 → workflow 가 GitHub 에 안 등록 → CI 게이트 dead code**. 본 Step 이 그 부담을 자동화.

#### 1. 변경 파일 검출

```bash
PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"
cd "$PROJECT_ROOT"

# dcness 가 cp 한 파일만 명시 path — 사용자 다른 untracked 안 건드림
NEW_FILES=$(git status --short \
  .github/workflows/ .dcness/ 2>/dev/null \
  | grep -E '^\?\?' | awk '{print $2}')
MODIFIED=$(git status --short \
  .github/workflows/ .dcness/ 2>/dev/null \
  | grep -E '^.M' | awk '{print $2}')
CHANGES="$NEW_FILES $MODIFIED"
CHANGES_TRIM=$(echo $CHANGES | tr -s ' ')

# 변경 없으면 skip
if [ -z "$CHANGES_TRIM" ]; then
  echo "[dcness] working tree 안 dcness 인프라 변경 없음 — Step 2.11 skip"
  # Step 2.11 종료, Step 3 으로
fi
```

#### 2. 현재 branch 검사 — main 외 진행 중이면 skip

```bash
CUR_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ "$CUR_BRANCH" != "main" ]; then
  echo "[dcness] 현재 branch = '$CUR_BRANCH' (main 아님) — 자동 commit skip"
  echo "  사용자 작업 중인 branch 보호. 수동 처리:"
  echo "    git checkout main && /init-dcness  # 재실행"
  echo "  또는 본 변경을 현재 branch 에 직접 stage:"
  for f in $CHANGES; do echo "    git add $f"; done
  # Step 2.11 종료
fi
```

#### 3. 사용자 동의

```
[dcness] dcness 인프라 변경 자동 commit + PR 만들까요?
  변경 파일 (N개):
    .github/workflows/git-naming-validation.yml (신규)
    .github/workflows/pr-body-validation.yml (신규)
    .github/workflows/tdd-gate.yml (신규)
    .dcness/tdd-gate-enabled (신규)
  자동 진행 시:
    1. branch 생성: docs/dcness-init-{timestamp}
    2. 위 파일들 stage + commit (메시지 자동)
    3. push + PR 생성 (자동 머지 옵션은 사용자 결정)
  n 시 수동 처리 (직접 stage/commit/PR)
(Y/n)
```

#### 4. 자동 진행 (Y 선택 시)

```bash
TS=$(date +%Y%m%d_%H%M%S)
BR="docs/dcness_init_${TS}"

git checkout -b "$BR"

# 명시 path 만 stage — 다른 untracked 안 건드림
for f in $CHANGES; do
  git add "$f"
done

git commit -m "[docs] dcNess init — workflows + 마커 stage

dcness plug-in 의 인프라 파일 main 등록:
$(for f in $CHANGES; do echo "  - $f"; done)

본 commit 머지 후 다음 PR 부터:
- git-naming-validation 발화
- pr-body-validation 발화
- tdd-gate (CI affected) 발화
- pre-commit TDD 게이트 (.dcness/tdd-gate-enabled 인지) 발화
"

git push -u origin "$BR"

gh pr create --title "[docs] dcNess init — workflows + 마커 stage" --body "$(cat <<EOF
## 변경 요약

dcness plug-in 의 인프라 파일들 main 등록.

## 포함

$(for f in $CHANGES; do echo "- \`$f\`"; done)

## 관련 이슈

Document-Exception-PR-Close: dcness init 인프라 PR — issue 매핑 없음. dcness plug-in 의 \`/init-dcness\` Step 2.11 자동 생성.

## 머지 후 발화

- \`git-naming-validation\` CI 자동
- \`pr-body-validation\` CI 자동
- \`tdd-gate\` (CI affected) 자동
- pre-commit TDD 게이트 (\`.dcness/tdd-gate-enabled\` 인지) 즉시 발화
EOF
)"
```

#### 5. 머지 안내

```
[dcness] PR 생성 완료. 다음:
  1. PR 머지 (gh pr merge <num> --auto --merge)
  2. main pull (git checkout main && git pull)
  3. 다음 feature PR 부터 모든 게이트 자동 발화
```

#### 6. 한계

- 현재 branch != main 일 때 자동 진행 X — 사용자 작업 보호 (`git stash` 위험 회피)
- 사용자가 *이미 PR 만든 인프라 변경* 있을 때 중복 시도 가능 — 메인 Claude 가 사전 `gh pr list --search "dcness init"` 검사 권장
- `gh` CLI 미설치 시 push 까지만 + 사용자 수동 PR 권유

### Step 3 — 사용자 안내

```
[dcness] 활성화 완료
- 프로젝트: <main repo root>
- whitelist: ~/.claude/plugins/data/dcness-dcness/projects.json

다음 세션부터 발화하는 것:
- SessionStart 훅 — by-pid / live.json 자동 생성
- PreToolUse Agent 훅 — catastrophic 룰 (orchestration.md §2.3) 검사

git-naming 강제 (Step 2.6 완료 시):
- 로컬: .git/hooks/commit-msg (thin shim) — 커밋 제목 형식 위반 차단. 본체 로직 plugin SSOT 안.
- CI (사용자 선택): .github/workflows/git-naming-validation.yml — composite action 호출 1줄
- dcness-rules.md / check_git_naming.mjs 는 사용자 repo cp 안 함 — plugin SSOT 직접 호출 (#198)

design.md SSOT (Step 2.7 완료 시):
- CLAUDE.md 매트릭스에 docs/design.md 행 등록 (UI 작업 시 read 후보)
- (UI 프로젝트인 경우) docs/design.md minimal 템플릿 시드 — 컬러 / 타이포그래피 / 컴포넌트 토큰 채워 사용

초기 docs 폼 시드 (Step 2.8 완료 시):
- docs/PRD.md / ARCHITECTURE.md / ADR.md placeholder — 기획 논의 후 채워넣는 용도
- 부재 시만 시드 (멱등) — 기존 파일은 보호

TDD 게이트 (Step 2.9 완료 시 — polyglot universal + affected detection):
- .github/workflows/tdd-gate.yml — PR 마다 affected 테스트 강제 (composite action 호출)
- 지원 언어 4: node / python / rust / go 자동 검출 + 변경분만 실행
- node: nx / turbo / pnpm workspaces 자동 detect → dependency 그래프 포함 affected
- python/rust/go: 변경 파일 path 기반 root 식별 → 해당 root 만 테스트
- branch protection 의 required status checks 등록은 사용자 수동 (안내문 출력)
- 사용자 설정 0 — 도구 분기 / 위임 명령 작성 불필요 (#320 #1 phase 3 root fix)

Pre-commit TDD 게이트 (Step 2.10 완료 시 — commit 단 차단):
- commit-msg hook chain — git-naming 검증 후 TDD 게이트 발화
- 옵트인 마커 `.dcness/tdd-gate-enabled` 있을 때만 발화 (다른 프로젝트 영향 0)
- staged src 변경 = staged 또는 branch diff 안 test 함께 있어야 commit 통과
- 검출된 변경분 test 만 실행 (5~15개 단위, 수초) — 풀 스위트 X
- 4 언어 자동 (node jest/vitest, python pytest, rust cargo, go go test)
- 우회: commit message 안 `[skip-test: <사유>]` marker
- branch protection 의존성 0 — 진짜 자체완결 wall (#320 #1 phase 4 root fix)

자동 commit + PR (Step 2.11 완료 시):
- Step 2.6 ~ 2.10 깔린 인프라 파일들 자동 stage + commit + push + PR
- 현재 branch = main 일 때만 자동 진행 (사용자 작업 중 branch 보호)
- 사용자가 *까먹어도* dcness CI 가 dead code 안 됨 (#320 사용자 피드백 root fix)

사용 가능한 skill:
- /qa  — 이슈 분류
- /quick — 작은 버그픽스 light path
- /product-plan — 새 기능 spec/design
- /smart-compact — 컨텍스트 압축 + resume prompt

비활성화 — `/disable-dcness` 또는 `"$(ls -d ${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/plugins/cache/dcness/dcness/*} 2>/dev/null | sort -V | tail -1)/scripts/dcness-helper" disable`.

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
- `docs/archive/conveyor-design.md` §13 — worktree γ resolution (활성화도 main repo 기준)
- 이전 하네스 패턴 대비: whitelist 위치가 글로벌 `~/.claude/harness-projects.json` 대신 plugin-scoped `~/.claude/plugins/data/dcness-dcness/projects.json`
