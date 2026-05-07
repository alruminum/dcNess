# 플러그인 릴리즈 절차

## 1. 버전 파일 위치

두 파일을 항상 같은 버전으로 동시에 올린다.

| 파일 | 필드 |
|---|---|
| `.claude-plugin/plugin.json` | `"version"` |
| `.claude-plugin/marketplace.json` | `"metadata.version"` |

## 2. 주의사항 — marketplace.json source 형식

`plugins[].source` 는 반드시 `"./"` 형식이어야 한다.

```json
"source": "./"   ✅
```

GitHub object 형식(`{"source": "github", "repo": "...", "ref": "release"}`)은 `claude plugin install`(신규)은 동작하지만 `claude plugin update`에서 "destination is empty after copy" 오류 발생. (0.2.3에서 수정됨)

## 3. 릴리즈 순서

```sh
# 1. 브랜치 생성
git checkout -b docs/release_{버전}_{설명} main

# 2. 버전 올리기
#    .claude-plugin/plugin.json     "version" 필드
#    .claude-plugin/marketplace.json "metadata.version" 필드

# 3. 커밋
git add .claude-plugin/plugin.json .claude-plugin/marketplace.json
git commit -m "[docs] release {버전} — {설명}"

# 4. PR 생성 → CI PASS → merge
git push -u origin docs/release_{버전}_{설명}
gh pr create --title "[docs] release {버전} — {설명}" ...
gh pr merge {번호} --merge

# 5. main pull 후 태그 박기
git checkout main && git pull
git tag v{버전} && git push origin v{버전}

# 6. 사용자 업데이트 가이드 출력
echo "---"
echo "v{버전} 업데이트 가이드"
echo ""
echo "  claude plugin update dcness@dcness"
echo ""
echo "문제 발생 시:"
echo "  claude plugin uninstall dcness@dcness && claude plugin install dcness@dcness"
echo "---"
```

## 4. 릴리즈 후 사용자 검증 방법

```sh
claude plugin marketplace update dcness
claude plugin uninstall dcness@dcness && claude plugin install dcness@dcness
cat ~/.claude/plugins/installed_plugins.json | python3 -c \
  "import json,sys;d=json.load(sys.stdin);print(d['plugins']['dcness@dcness'][0]['version'])"
```

> `claude plugin update dcness@dcness` 는 현재 정상 동작하나, 문제 발생 시 uninstall → install 로 대체.

## 5. 릴리즈 노트 관리

[`docs/internal/release-notes.md`](release-notes.md) 에 버전별 변경 요약 기록.
