# Story 3.1 검증 보고서 — marketplace.json source.ref 실측 결과

> Epic 3 (#152) 블로커 검증. **결론: GREEN — Story 3.2~3.4 진행 가능.**

## 검증 목적

`marketplace.json` 플러그인 엔트리의 `source.ref` 필드가 특정 브랜치 콘텐츠만 plugin cache 로 복사하는지 실측.
작동 안 하면 Epic 3 전체 폐기.

---

## 1. 공식 spec 검증 (GREEN)

**출처**: `https://code.claude.com/docs/en/plugin-marketplaces` 실측 (2026-05-06)

### Plugin source 스키마

| Source 타입 | 필드 |
|---|---|
| `github` | `repo` (필수), `ref?` (브랜치/태그), `sha?` (40자 커밋 SHA) |
| `url` | `url` (필수), `ref?`, `sha?` |
| `git-subdir` | `url` (필수), `path` (필수), `ref?`, `sha?` |

### 공식 release channels 예시 (spec 직접 인용)

```json
{
  "name": "stable-tools",
  "plugins": [
    {
      "name": "code-formatter",
      "source": {
        "source": "github",
        "repo": "acme-corp/code-formatter",
        "ref": "stable"
      }
    }
  ]
}
```

→ Epic 3 의 패턴 (`ref: "release"`) 이 공식 지원 사례와 동일 구조.

### Marketplace source vs Plugin source 구분 (중요)

| 개념 | 설명 | ref 지원 |
|---|---|---|
| **Marketplace source** | 사용자가 `/plugin marketplace add` 시 marketplace.json 을 fetch 하는 위치 | ref 지원 (sha 미지원) |
| **Plugin source** | marketplace.json 안 plugin entry 의 `source` 필드 | ref + sha 모두 지원 |

→ dcness 전략: **marketplace 는 main 브랜치에서 fetch, plugin source 는 `release` 브랜치 지정** (Plugin source ref 활용).

---

## 2. 실측 테스트 (GREEN)

### 테스트 구성

1. `release-dryrun` 브랜치 생성 (main 에서 분기, commit `aec36da`)
   - 제거: `docs/internal/` (governance.md, main-claude-rules.md, self-guidelines.md)
   - 제거: `docs/archive/` (11개 파일)
   - 유지: agents/, commands/, hooks/, scripts/, docs/plugin/, harness/, tests/

2. 테스트 marketplace 설정:

```json
{
  "name": "dcness-sourceref-test",
  "plugins": [
    {
      "name": "dcness-dryrun",
      "source": {
        "source": "github",
        "repo": "alruminum/dcNess",
        "ref": "release-dryrun"
      }
    }
  ]
}
```

3. 설치 실행:

```sh
claude plugin marketplace add /tmp/dcness-source-ref-test
GITHUB_TOKEN=$(gh auth token) claude plugin install dcness-dryrun@dcness-sourceref-test
```

### cache 검증 결과

```
~/.claude/plugins/cache/dcness-sourceref-test/dcness-dryrun/0.1.0-alpha/
  agents/       ✅ 존재
  commands/     ✅ 존재
  hooks/        ✅ 존재
  scripts/      ✅ 존재
  docs/plugin/  ✅ 존재 (9개 파일)
  docs/internal/ ❌ 미존재 (검증 목표 달성)
  docs/archive/  ❌ 미존재 (검증 목표 달성)
  harness/      존재 (Story 3.2 제거 후보 — 이번 검증 범위 외)
  tests/        존재 (Story 3.2 제거 후보 — 이번 검증 범위 외)
```

cache 용량: `1.4MB` (release-dryrun 기준)
제거 대상 크기: `docs/internal/ 24KB + docs/archive/ 584KB ≈ 600KB`

---

## 3. 결론 및 후속 결정

### Epic 3 진행 판정: **GREEN**

`{ "source": "github", "repo": "alruminum/dcNess", "ref": "release" }` 형태가 검증됨.
Story 3.2~3.4 진행 가능.

### Story 3.2~3.4 인수사항

| 항목 | 결정 필요 시점 |
|---|---|
| `harness/`, `tests/` release 브랜치 포함 여부 | Story 3.2 PR |
| `AGENTS.md`, `PROGRESS.md` release 브랜치 포함 여부 | Story 3.2 PR |
| `plugin.json` version 필드 bump 정책 | Story 3.4 PR |
| release 브랜치 branch protection 설정 | Story 3.3 필수 |

### release 브랜치 branch protection 설명

release 브랜치는 GitHub Actions workflow (Story 3.3) 만 push 가능해야 함.
직접 commit 허용 시 `sync_release.sh` 의 force reset 으로 데이터 손실 위험.
`docs/archive/branch-protection-setup.md` 가이드 참조.

### 최종 marketplace.json 형태 (Story 3.4 변경 대상)

```json
{
  "plugins": [
    {
      "name": "dcness",
      "source": {
        "source": "github",
        "repo": "alruminum/dcNess",
        "ref": "release"
      }
    }
  ]
}
```

---

## 4. 테스트 정리

- `release-dryrun` 브랜치: GitHub 에 보존 (Story 3.2 에서 `release` 브랜치로 전환 또는 별도 생성 시 참조)
- 테스트 marketplace (`dcness-sourceref-test`): 제거 완료
- `~/.ssh/known_hosts`: github.com ED25519 키 추가 (local 사이드이펙트)
- git URL 재작성: `git config --global url."https://github.com/".insteadOf "git@github.com:"` 설정됨 (의도한 변경)
