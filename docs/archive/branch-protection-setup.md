# Branch Protection 설정 가이드

> ⚠️ **현재 상태 (DCN-CHG-20260501-06 이후): OFF**. 본 가이드는 *옵션 도구* — 필요 시 재활성용 보존.
> 비활성 사유: governance.md §2.8 참조. doc-sync 만 실질 강제하면 충분 + paths 필터 폐기 트레이드오프 회피.
>
> 규칙 정의: [`governance.md`](governance.md) §2.8 (SSOT — 본 가이드는 *적용 도구*).
> Origin: `DCN-CHG-20260429-21` (proposal §5 Phase 3 "Gate 5 → branch protection required reviewers" 외부화).

## 0. 목적

`main` 브랜치에 대한 다음 4 항목을 GitHub Repository Settings 로 외부화:

1. **필수 status checks** — 4 게이트(`document-sync`, `python-tests`, `plugin-manifest`, `task-id-validation`) 모두 PASS 강제
2. **LGTM 게이트** — 1명 이상 approving review (proposal §5 Phase 3 `Gate 5` 외부화)
3. **force-push / 삭제 차단** — 히스토리 무결성
4. **conversation resolution 강제** — 리뷰 코멘트 미해결 머지 차단

RWHarness 의 in-process LGTM flag 는 dcNess 에선 *자연 폐기* (migration-decisions §2.2 — `class Flag` DISCARD). GitHub branch protection 이 동일 역할을 *기계적* 으로 강제.

## 1. 자동 적용 (admin 권한 필요)

```sh
# 1) gh CLI 인증 확인 (admin 권한 필수)
gh auth status

# 2) 페이로드 미리보기 (실제 호출 X)
node scripts/setup_branch_protection.mjs --dry-run

# 3) 실제 적용 (멱등 — 같은 페이로드 반복 안전)
node scripts/setup_branch_protection.mjs
```

성공 시 출력:

```
[branch-protection] PASS — 브랜치 보호 적용 완료
  required_status_checks.strict: true
  required_approving_review_count: 1
  allow_force_pushes: false
```

실패(403 등) 시: 아래 §2 수동 적용으로 전환.

## 2. 수동 적용 (GitHub UI)

1. 저장소 → **Settings → Branches → Branch protection rules → Add rule**
2. **Branch name pattern**: `main`
3. 다음 옵션 체크:

| 옵션 | 값 |
|---|---|
| Require a pull request before merging | ✅ |
| └ Require approvals | ✅ — count `1` |
| └ Dismiss stale pull request approvals when new commits are pushed | ✅ |
| Require status checks to pass before merging | ✅ |
| └ Require branches to be up to date before merging | ✅ |
| └ Status checks (검색 + 추가) | `Document Sync gate`, `unittest discover`, `validate manifest`, `Task-ID format gate` |
| Require conversation resolution before merging | ✅ |
| Require linear history | ✅ |
| Do not allow bypassing the above settings | (운영자 판단 — 본 저장소는 미설정) |
| Allow force pushes | ❌ |
| Allow deletions | ❌ |

4. **Create / Save**

## 3. 검증 — 보호가 실제로 동작하는지

```sh
# 적용 직후 확인 (admin 권한)
gh api repos/alruminum/dcNess/branches/main/protection \
  --jq '{
    required_status_checks: .required_status_checks.contexts,
    strict: .required_status_checks.strict,
    required_reviewers: .required_pull_request_reviews.required_approving_review_count,
    force_push: .allow_force_pushes.enabled,
    linear: .required_linear_history.enabled
  }'
```

기대 출력:

```json
{
  "required_status_checks": [
    "Document Sync gate",
    "unittest discover",
    "validate manifest",
    "Task-ID format gate"
  ],
  "strict": true,
  "required_reviewers": 1,
  "force_push": false,
  "linear": true
}
```

비-admin 은 `404 Not Found` 반환(보호 정보 비공개). 정상.

## 4. 회귀 시나리오 — 의도적 차단 검증

설정 후 다음 시나리오로 차단 동작 확인:

| 시나리오 | 기대 결과 |
|---|---|
| `git push origin main` (브랜치 우회) | `protected branch hook declined` |
| `gh pr merge --squash <PR>` 게이트 1개 FAIL 상태 | "Required check ... is failing" |
| `gh pr merge --squash <PR>` 리뷰 0 상태 | "At least 1 approving review is required" |
| `git push --force origin main` | "Cannot force-push to a protected branch" |

## 5. 운영 룰

- **CI 게이트 추가/제거 시** 본 가이드 + `setup_branch_protection.mjs` 의 `REQUIRED_CHECKS` 동시 갱신.
- **검증 이름 변경 시** 워크플로우 `jobs.<id>.name` 과 protection rule 의 status check 이름이 *문자열 일치* 해야 함. mismatch 시 머지 영구 블록.
- **새 게이트 도입 직후 1회는 "Require ... pass" 체크 박스 미선택** — 첫 PR 이 자기 자신을 통과시켜야 history 가 생김. 이후 활성화.

## 6. proposal 정합

| proposal §5 Phase 3 항목 | dcNess 외부화 위치 |
|---|---|
| Gate 1 (gh issue/tracker mutate) | dcNess 미도입 (migration-decisions §2.2 — commit-gate.py DISCARD). 필요 시 `permissions.issues=read` workflow 정책으로 추가 |
| Gate 4 (doc-sync) | `.github/workflows/document-sync.yml` (`DCN-CHG-20260429-08`) |
| Gate 5 (LGTM flag) | **본 가이드 — branch protection required reviewers** (`DCN-CHG-20260429-21`) |
| Task-ID 형식 검증 | `.github/workflows/task-id-validation.yml` (`DCN-CHG-20260429-20`) |

## 7. 참조

- [`governance.md`](governance.md) — SSOT
- [`scripts/setup_branch_protection.mjs`](../../scripts/setup_branch_protection.mjs) — 자동화 스크립트
- [`docs/archive/status-json-mutate-pattern.md`](../archive/status-json-mutate-pattern.md) §5 Phase 3 — 외부화 발상 출처 (역사 자료)
- [`docs/archive/migration-decisions.md`](../archive/migration-decisions.md) §2.2 — RWHarness commit-gate.py / class Flag DISCARD 분류
- [GitHub Docs — Branch protection rules](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/defining-the-mergeability-of-pull-requests/about-protected-branches)
