# CLAUDE.md — dcNess 프로젝트 작업 지침

> 본 파일은 메인 Claude (Claude Code) 가 dcNess 저장소에서 작업할 때의 지침이다.
> 거버넌스 규칙은 [`docs/process/governance.md`](docs/process/governance.md) (SSOT) 에 있다 — 본 파일은 *재기술하지 않고 절차·링크만 박는다*.

> 🔴 **[필수 — 본 프로젝트 작업 *직전* read 의무]**
>
> 본 CLAUDE.md 와 동일 레벨 강제로 다음 문서 *반드시 read*:
>
> 👉 **[`docs/process/main-claude-rules.md`](docs/process/main-claude-rules.md)** — 메인 Claude 행동 룰 SSOT
>
> 내용:
> - §0 **대원칙** — 강제 = (1) 작업 순서 + (2) 접근 영역. 그 외 agent 자율.
> - §1 **실존 검증 강제** (제1룰)
> - §2 **dcness 인프라** (300줄 cap / 5 SSOT / 거버넌스 / 핵심 강제 룰 4 / sub-agent path 보호)
> - §3 **Karpathy 4 원칙 전문**
>
> SessionStart inject 작동 안 해도 본 문서 read 로 룰 인지 보장. 미인지 진행 = 룰 위반.

## 0. 프로젝트 정체성

> 🔴 **메인 Claude 가 자주 까먹는 핵심 — 매번 작업 전 반드시 인지**

### 0.1 본 프로젝트 = 하네스 인프라 (plug-in 배포물)

- 본 프로젝트(dcness)는 **Claude Code 용 plug-in 으로 배포**된다.
- 사용자(외부 프로젝트)는 **`/init-dcness` 스킬을 통해 활성화**한다.
- 본 프로젝트에 추가하는 모든 기능은 **dcness 자체를 위한 것이 아니라**, **활성화한 외부 프로젝트에 적용되기 위한 것**이다.
- 따라서 "이 프로젝트에서 잘 작동하는가" 가 아니라 **"활성화한 외부 프로젝트에서 잘 작동하는가"** 가 기준.

### 0.2 dcness 자체는 init-dcness 미적용 — 자기 규격 미얽매임

- 본 dcness 저장소는 자기 자신에 `/init-dcness` 를 실행하지 **않는다**.
- 따라서 dcness plug-in 의 규격(`stories.md` 강제 / `issue-lifecycle.md §1.1` 흐름 / `product-planner` 시퀀스 등) 에 **얽매이지 않는다**.
- dcness 자체의 작업은 다음 4개만 따른다:
  - `docs/process/governance.md` (Task-ID + Change-Type + 동반 갱신)
  - `docs/process/git-naming-spec.md` (브랜치·커밋·PR 네이밍)
  - GitHub 이슈 (필요 시 자유 형식, 메타-스토리·stories.md 불필요)
  - 본 CLAUDE.md
- **헷갈리지 마라**: plug-in 규격은 *외부 활성화 프로젝트* 용이지, dcness 자기 자신용이 아니다.

### 0.3 내부 ID 를 외부 배포물에 박지 마라

- `DCN-CHG-YYYYMMDD-NN` 같은 **내부 변경 추적 ID** 는 dcness 내부 거버넌스(`docs/process/document_update_record.md` / `change_rationale_history.md` / commit message) 용이다.
- **외부에 배포되는 파일** (= plug-in 사용자가 보게 되는 파일: `agents/**`, `commands/**`, `skills/**`, `hooks/**`, 그리고 plug-in 사용자가 따라야 하는 SSOT 인 `docs/issue-lifecycle.md` 등) 안에는 **내부 ID 를 본문으로 박지 않는다**.
- 외부 사용자에게 "DCN-CHG-20260504-01 에서 ..." 같은 표현은 **잡음**이다. 그 변경 이유 / 작동 룰만 자연어로 설명하면 충분.
- 단 dcness 자체 거버넌스 로그(`document_update_record.md` / `change_rationale_history.md` / commit message / 본 dcness 자체의 docs/process/) 안에서는 ID 표기 필수 — 이건 *내부* 추적이라 OK.

### 0.4 작성 스타일 — 쉬운 한글 + § 표시 명확히

- 외래어 (Caveats / Disclaimer / Note / TBD 등) 보다는 **명확한 한글** 사용. (예: "Caveats" → "주의사항" / "TBD" → "추후 결정")
- 영어 약어가 더 정확한 곳(API / SDK / SSOT / PR / CI 등 산업 표준어)은 그대로 사용.
- **`§` 기호는 명확하게 사용** — `§N`, `§N.M` 형식. 어디서 인용했는지 **반드시 명시** (예: `governance.md §2.3` / `main-claude-rules.md §0`).
- 단순히 "위 섹션" / "아래 참조" 같은 모호한 표현 X — 항상 `파일명 §번호` 박을 것.

### 0.5 추가한 기능은 반드시 배포 경로에도 포함

- 본 저장소(dcness self) 에만 추가하면 **외부 활성화 프로젝트에서는 작동하지 않는다** — 과거 사례: 기능을 dcness 자체에 추가했는데 정작 설치한 외부 프로젝트(jajang)는 그 기능이 없어 작동 안 함.
- 모든 기능 추가 작업은 **배포 경로 검증 의무** 가 동반된다. 다음 중 *해당하는 모든 경로* 가 갱신돼야 작업 완료:
  1. **plug-in 본체 파일** (`agents/**`, `commands/**`, `skills/**`, `hooks/**`) — 사용자가 plug-in 업데이트 시 자동 적용. 본 저장소의 같은 경로에 변경 = plug-in 도 자동 갱신 (단 사용자가 plug-in 버전 업 받은 후).
  2. **`/init-dcness` 스킬이 사용자 프로젝트로 *복사·배포* 하는 파일** (예: `scripts/check_*.mjs`, `scripts/hooks/commit-msg`, `.github/workflows/*.yml`) — 본 저장소에만 추가하면 신규 프로젝트는 받지만 *기존 활성화 프로젝트* 는 못 받음. **`commands/init-dcness.md` 의 deploy 스텝에 반드시 추가** + 기존 사용자가 재배포받을 방법 고지.
  3. **사용자가 따라야 하는 SSOT 문서** (예: `docs/issue-lifecycle.md`, `docs/process/git-naming-spec.md` 중 사용자용 부분) — 본 저장소 docs 만 갱신하면 사용자는 못 봄. plug-in 배포물 쪽으로 옮기거나 init-dcness 가 복사하도록 처리.
- 기능 추가 PR 본문에 **"배포 경로 검증"** 항목 명시 — 어떤 경로(1/2/3) 로 사용자 환경에 도달하는지, 누락 없는지.
- **검증 안 된 변경은 dcness 자체에서만 작동하는 환상**. 사용자에게 안 닿으면 기능 추가 의미 없음.

---

### 0.6 모드 (위 0.1~0.5 정체성 위에서)

- **목적**: RWHarness fork-and-refactor — status-JSON-mutate 결정론 + 4 기둥 정합 + 함정 회피 5원칙 (`docs/status-json-mutate-pattern.md` §1~§2.5).
- **모드**: **메인 Claude 직접 작업** (`status-json-mutate-pattern.md` §10 / §11.4 정합).
  - architect / validator / engineer 위임 강제 **없음**.
  - RWHarness 가드 미적용 환경. **단** Document Sync 거버넌스만 강제.
  - 글로벌 `~/.claude/CLAUDE.md` 의 RWHarness 위임 룰(에이전트 분기 / 인프라 프로젝트 분기)은 본 프로젝트에 **미적용**. 본 파일이 우선한다.

## 1. 작업 절차 (모든 변경 공통)

> SSOT: [`docs/process/governance.md`](docs/process/governance.md) §2.3.

1. **Task-ID 발급**: `DCN-CHG-YYYYMMDD-NN` (governance §2.1).
2. **변경 분류**: governance §2.2 표에서 Change-Type 토큰 결정.
3. **수정 작업**.
4. **완료 직전 동반 갱신**:
   - `docs/process/document_update_record.md` (모든 변경)
   - `docs/process/change_rationale_history.md` (spec / agent / harness / hooks / ci 변경 시)
   - `PROGRESS.md` (harness / hooks / ci 변경 시)
   - 카테고리별 deliverable (governance §2.6)
5. **commit 직전**: doc-sync + pytest 2 게이트 통과 (자동).
   - `node scripts/check_document_sync.mjs` (모든 commit)
   - `sh scripts/check_python_tests.sh` (`harness/` / `tests/` / `agents/` / `python-tests.yml` staged 시만)
   - 자동: Claude Code PreToolUse hook (`scripts/hooks/cc-pre-commit.sh`) + git pre-commit hook 이 동시 차단.
6. **branch → PR → squash merge** (직접 `main` push 금지).

## 2. 거버넌스 핵심 (전체 룰은 SSOT 참조)

- **Task-ID 형식**: `DCN-CHG-YYYYMMDD-NN` (governance §2.1)
- **Change-Type 7종**: `spec` / `agent` / `harness` / `hooks` / `ci` / `test` / `docs-only` (governance §2.2)
- **예외**: `Document-Exception:` 토큰 (governance §2.4 — *현재 diff 추가 라인만 유효*, 과거 누적 무효)
- **3중 강제**: git pre-commit hook + Claude Code PreToolUse hook + AGENTS.md (governance §2.7)

> ⚠️ **금지**: `--no-verify` 등 hook 우회. 룰 재기술. Task-ID 없는 commit. 과거 머지된 Exception 으로 현재 위반 회피.

## 3. 문서 지도

### 즉시 읽기 (세션 시작 시 항상)

| 파일 | 역할 |
|---|---|
| [`docs/process/main-claude-rules.md`](docs/process/main-claude-rules.md) | 🔴 **메인 Claude 행동 룰 SSOT** — 실존 검증 / dcness 인프라 / Karpathy 4 원칙 |
| [`docs/process/governance.md`](docs/process/governance.md) | 거버넌스 SSOT — Task-ID / Change-Type / 게이트 전체 룰 |
| [`docs/process/git-naming-spec.md`](docs/process/git-naming-spec.md) | 브랜치·커밋·PR 네이밍 규칙 SSOT — 모든 커밋 작업에 적용 |

### 작업 시 읽기 (lazy — 해당 작업 직전에만)

| 파일 | 언제 읽나 |
|---|---|
| [`docs/process/document_update_record.md`](docs/process/document_update_record.md) | 모든 변경 기록 시 (WHAT 로그) |
| [`docs/process/change_rationale_history.md`](docs/process/change_rationale_history.md) | spec / agent / harness / hooks / ci 변경 시 (WHY 로그) |
| [`docs/process/document_impact_matrix.md`](docs/process/document_impact_matrix.md) | 변경 영향 범위 검토 시 |
| [`docs/status-json-mutate-pattern.md`](docs/status-json-mutate-pattern.md) | 하네스 설계·Phase 수정 시 |
| [`docs/orchestration.md`](docs/orchestration.md) | 오케스트레이션 로직(시퀀스·retry·escalate) 수정 시 |
| [`PROGRESS.md`](PROGRESS.md) | 현재 상태·TODO·Blockers 확인 시 |
| [`AGENTS.md`](AGENTS.md) | 외부 에이전트(Codex 등) 지침 수정 시 |
| [`.github/PULL_REQUEST_TEMPLATE.md`](.github/PULL_REQUEST_TEMPLATE.md) | PR 체크리스트 확인 시 |
| [`docs/process/branch-protection-setup.md`](docs/process/branch-protection-setup.md) | 브랜치 보호 설정 변경 시 |
| [`docs/process/plugin-dryrun-guide.md`](docs/process/plugin-dryrun-guide.md) | 플러그인 배포 dry-run 시 |
| [`scripts/check_document_sync.mjs`](scripts/check_document_sync.mjs) | Document Sync 게이트 구현 참조 시 |
| [`scripts/check_python_tests.sh`](scripts/check_python_tests.sh) | pytest 게이트 구현 참조 시 |
| [`scripts/hooks/pre-commit`](scripts/hooks/pre-commit) | git pre-commit hook 수정 시 |
| [`scripts/hooks/cc-pre-commit.sh`](scripts/hooks/cc-pre-commit.sh) | Claude Code PreToolUse hook 수정 시 |

## 4. 개발 명령어

```sh
# Document Sync 게이트 수동 실행 (commit 전 자동 호출됨)
node scripts/check_document_sync.mjs

# git hook 설치 (clone 후 1회)
cp scripts/hooks/pre-commit .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit
cp scripts/hooks/commit-msg .git/hooks/commit-msg && chmod +x .git/hooks/commit-msg

# 하네스 단위 테스트 실행
python3 -m unittest discover -s tests -v
python3 -m unittest tests.test_signal_io -v   # 단일 모듈
```

> 빌드 / 런타임 명령어는 코드 도입 시 본 섹션에 추가 (별도 Task-ID).

## 5. 커밋 / PR 절차

> 네이밍·메시지·PR 템플릿 상세: **[`docs/process/git-naming-spec.md`](docs/process/git-naming-spec.md)** (즉시 읽기 문서).

```
1. git checkout -b {브랜치명} main         # git-naming-spec §1 패턴
2. (변경 + 거버넌스 동반 파일 갱신)
3. git add {파일}
4. node scripts/check_document_sync.mjs    # 게이트 수동 확인 (선택)
5. git commit -m "..."                      # hook 자동 게이트
6. git push -u origin {브랜치명}
7. gh pr create --title "..." --body "..."  # git-naming-spec §4~§5 템플릿
8. gh pr merge                              # regular merge (squash 금지)
9. git checkout main && git pull
```

- **main 직접 commit/push 금지**. 항상 branch → PR → regular merge.
- **squash merge 금지** — 커밋별 히스토리 보존 목적.
- **branch 는 merge 후에도 삭제하지 않는다**.

## 6. 환경변수

현재 없음. 도입 시 본 섹션에 (이름·용도·기본값·필수 여부) 추가.
