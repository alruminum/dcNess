# PROGRESS

## 현재 상태
- 거버넌스 시스템 부트스트랩 완료 (`DCN-CHG-20260429-01`, PR #1 머지)
- 프로젝트 루트 `CLAUDE.md` + 루트 정책 파일 게이트 분류 추가 (`DCN-CHG-20260429-02`)
- **Phase 1 foundation 진입**: `harness/state_io.py` 신규 + 테스트 32 PASS (`DCN-CHG-20260429-03`, PR #3 머지)
  - R8 5 failure modes (not_found/empty/race/malformed_json/schema_violation) 단일 normalize 검증 완료
  - atomic write (POSIX rename) + path traversal self-check (R1 layer 1) 포함
  - 적용 범위 = 모듈 단독. validator 호출지 / agent docs / hook ALLOW_MATRIX 변환은 후속 Task-ID
- **Plugin 배포 인프라**: `.claude-plugin/{plugin,marketplace}.json` 신규 (`DCN-CHG-20260429-04`)
  - 이름 = `dcness`, 버전 = `0.1.0-alpha`. RWHarness 와 공존 가능 설계 (proposal §12.3.2).
  - governance §2.2 의 `agent` 카테고리에 `^\.claude-plugin/` 패턴 추가하여 plugin manifest 변경도 heavy 카테고리 강제.

## TODO
### Phase 1 — 후속 (validator 단일 agent 완성)
- [ ] `docs/migration-decisions.md` 신규 — `status-json-mutate-pattern.md` §11.2 framework 적용 (RWHarness 모듈 분류)
- [ ] `agents/validator*.md` 복사 + `@OUTPUT_FILE` / `@OUTPUT_SCHEMA` / `@OUTPUT_RULE` 형식 변환 (5 모드 sub-doc)
- [ ] RWHarness `harness/core.py` plan/design/ux validation 함수 복사 + `parse_marker` → `read_status` 치환 (7 호출지)
- [ ] RWHarness `hooks/agent-boundary.py` 복사 + validator ALLOW_MATRIX 에 status path regex 추가
- [ ] `_AGENT_DISALLOWED["validator"]` 에서 `Write` 제거
- [ ] ENV 게이트 `HARNESS_STATUS_JSON_VALIDATOR=1` off 시 회귀 0 검증
- [ ] validator → engineer handoff 를 status JSON `next_actions[]` 로 변환

### 인프라 / CI
- [ ] `.github/workflows/document-sync.yml` 추가 (CI 게이트, 별도 Task-ID)
- [ ] CLAUDE.md §6 환경변수 — `HARNESS_STATUS_JSON_VALIDATOR` 등 도입 시 갱신

## Blockers
- 없음
