# release 브랜치 보호 정책

> **결론**: 클래식 Branch Protection Rules 로는 `github-actions[bot]` 만 허용하는 actor-level 제어가 불가능하다. release 브랜치는 **관례 기반 읽기 전용**으로 운영한다.

## 배경

`sync_release.sh` 는 main 기반 force-reset 방식이다 — release 위 직접 commit 은 다음 sync 에서 덮어써진다.

GitHub 클래식 Branch Protection Rules 에서 실제 사용 가능한 옵션:
- **Lock branch** — 완전 읽기 전용이지만 workflow GITHUB_TOKEN 도 차단됨
- **Allow force pushes** — push 권한 있는 모든 사람에게 허용 (선택적 허용 불가)
- actor 별 허용/차단은 별도 GitHub Rulesets (Settings → Rules → Rulesets) 에서만 가능

workflow 자동 sync 를 유지하면서 사람만 차단하려면 PAT 등록 또는 Rulesets 가 필요해 복잡도가 올라간다. 소규모 프로젝트에서 ROI 없음.

## 운영 정책

**branch protection rule 미적용. 관례로 강제한다.**

- `release` 브랜치는 **`release-sync.yml` workflow 전용**이다.
- 사람이 직접 push 하거나 PR 을 merge 해선 안 된다.
- 긴급 패치도 반드시 `main` 브랜치 PR 경로로 진행한다. 다음 main push 시 release 에 자동 반영된다.

## 검증 (workflow 동작 확인)

```sh
# PR merge 후 release 자동 sync 확인
git fetch origin
git log origin/release --oneline -1
# → "release sync from main@<sha>" 형태
```

Actions 탭에서 `release sync` workflow 실행 기록도 확인 가능.
