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
"${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/plugins/marketplaces/dcness}/scripts/dcness-helper" enable
```

- 현재 cwd 의 main repo root 추출 (γ resolution — `git rev-parse --git-common-dir`)
- `~/.claude/plugins/data/dcness-dcness/projects.json` 의 `projects` 배열에 추가 (중복 자동 제거)
- 다음 세션부터 SessionStart / PreToolUse Agent 훅 발화 시작

## 절차

### Step 1 — 현재 상태 확인

```bash
"${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/plugins/marketplaces/dcness}/scripts/dcness-helper" status
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
"${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/plugins/marketplaces/dcness}/scripts/dcness-helper" enable
```

출력 예시:
```
[dcness] enabled: /Users/dc.kim/project/foo
[dcness] whitelist: /Users/dc.kim/.claude/plugins/data/dcness-dcness/projects.json
```

### Step 3 — 사용자 안내

```
[dcness] 활성화 완료
- 프로젝트: <main repo root>
- whitelist: ~/.claude/plugins/data/dcness-dcness/projects.json

다음 세션부터 발화하는 것:
- SessionStart 훅 — by-pid / live.json 자동 생성
- PreToolUse Agent 훅 — catastrophic 룰 (orchestration.md §2.3) 검사

사용 가능한 skill:
- /qa  — 이슈 분류
- /quick — 작은 버그픽스 light path
- /product-plan — 새 기능 spec/design
- /smart-compact — 컨텍스트 압축 + resume prompt

비활성화 — `/disable-dcness` 또는 `"${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/plugins/marketplaces/dcness}/scripts/dcness-helper" disable`.

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
