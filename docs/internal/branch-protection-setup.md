# release 브랜치 보호 설정 가이드

> **목적**: `release` 브랜치는 `release-sync.yml` workflow 만이 갱신한다. 사람 직접 push / PR merge 로의 갱신을 차단해 "다음 main merge 에서 사라짐" 사고를 방지한다.

## 배경

`sync_release.sh` 는 main 기반 force-reset 방식이다 — release 위 직접 commit 은 다음 sync 에서 덮어써진다. branch protection 없으면 사용자가 release 위 hotfix 를 쌓아두다가 즉시 사라지는 사고 발생.

## GitHub UI 설정 절차

> Settings → Branches → Branch protection rules → Add rule

**Branch name pattern**: `release`

### 설정 항목

| 항목 | 값 | 이유 |
|---|---|---|
| Restrict who can push to matching branches | ✅ 활성화 | 사람 직접 push 차단 |
| 허용 actor 추가 | `github-actions[bot]` | workflow GITHUB_TOKEN 허용 |
| Allow force pushes | ✅ 활성화 ("Specify who can force push") | sync 는 force-with-lease |
| force push 허용 actor | `github-actions[bot]` | workflow 만 force push 가능 |
| Do not allow bypasses | 체크 해제 (위 actor 예외 위해) | — |
| Restrict creations | 선택사항 | PR merge 경로 차단 시 활성화 |

### 상세 절차

1. **Settings → Branches → Add rule**
2. Branch name pattern: `release`
3. "Restrict who can push to matching branches" 체크 → **Add bypass** → `github-actions[bot]` 검색 후 추가
4. "Allow force pushes" 체크 → "Specify who can force push" 선택 → 위와 동일하게 `github-actions[bot]` 추가
5. **Save changes**

## GITHUB_TOKEN 권한 확인

`release-sync.yml` 의 `permissions: contents: write` 로 충분하다. PAT 별도 등록 불필요.

주의: branch protection 설정 전에 workflow 가 먼저 돌면 `release` 브랜치 push 는 성공한다 (보호 없으므로). 설정 후에도 `github-actions[bot]` 이 허용 actor 에 추가돼 있으면 force push 포함 정상 작동.

## 검증

branch protection 설정 완료 후:

```sh
# 1. 사람 직접 push 차단 확인
git push origin main:release
# → "protected branch" 에러 기대

# 2. workflow 자동 sync 확인
# 아무 PR 을 main 에 merge → Actions 탭에서 release-sync workflow 실행 확인
# release 브랜치 최신 commit 메시지 확인:
git fetch origin
git log origin/release --oneline -1
# → "release sync from main@<sha>" 형태

# 3. 무한 루프 부재 확인
# release push 후 release-sync workflow 가 다시 trigger 되지 않음 (on.push.branches: [main] 만 trigger)
```

## 주의사항

- `release` 위 직접 commit 은 다음 main merge 시 **사라진다**. 긴급 패치도 main 브랜치 PR 경로로 진행할 것.
- release 브랜치는 읽기 전용 배포물이다. 사용자는 이 브랜치를 `git clone --branch release` 또는 plugin source ref 로 참조한다.
