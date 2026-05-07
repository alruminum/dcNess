# 릴리즈 노트

> 버전별 변경 요약. 상세 커밋은 `git log {prev_tag}..{tag}` 참조.

---

## v0.2.3 (2026-05-07)

**커밋 범위**: `bfd500d..0fb69df`  
**핵심 변경**: `claude plugin update` 버그 수정

- `marketplace.json` `plugins[].source` 를 github object → `"./"` 로 복구
- 신규 install 은 두 포맷 모두 동작했으나, update 는 `"./"` 만 동작함을 확인 (`e68a440` 에서 잘못 변경된 것)
- git 태그 관리 시작 (이 버전부터 `v{버전}` 태그 병행)

---

## v0.2.2 (2026-05-07)

**커밋 범위**: `ff3ae5b..bfd500d`  
**핵심 변경**: 내부 문서 구조 정리 + dcness-rules 전면 재편

- `dcness-rules.md` 전면 재편 — 대원칙 신설, 루프 구조화, prose-only 통합 (issue-223)
- `main-claude-rules.md`, `self-guidelines.md`, `governance.md`, `branch-protection-setup.md` 삭제 — 역할 흡수 또는 중복 제거
- `CLAUDE.md §3` lazy 표 누락 파일 보완

---

## v0.2.1 (2026-05-07)

**커밋**: `ff3ae5bcdbd62c8f2240ca94f31d593133634101` (release branch HEAD)  
**핵심 변경**: marketplace 배포 경로 정비 + 로컬 게이트 강화

- release 브랜치에서 `marketplace.json` 제거 (sync_local_plugin.sh 폐기, issue-221)
- `dcness-rules.md` 로 rename + 정제 (issue-217)
- cc-pre-commit.sh 브랜치명·PR 제목 로컬 게이트 추가 (issue-171)
- run_review false positive 수정 (issue-171)
