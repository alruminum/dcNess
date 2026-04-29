# Docs Sync

`@MODE:ARCHITECT:DOCS_SYNC` → prose emit (마지막 단락에 결론 enum)

```
@PARAMS: { "impl_path": "이미 구현 완료된 impl", "docs_targets": ["docs/*.md ..."] }
@CONCLUSION_ENUM: DOCS_SYNCED | SPEC_GAP_FOUND | TECH_CONSTRAINT_CONFLICT
```

**목표**: impl 구현 완료 후 참조 설계 문서(db-schema.md / sdk.md / architecture.md 등) 에 누락된 섹션을 **파생 서술** 로 추가한다. 새 설계 결정은 절대 하지 않는다.

**사용처**: impl_loop 완료 후 문서 2~3 건 동기화가 남았을 때. 메인 Claude 가 Agent 도구로 직접 호출 가능 (harness 경유 불필요).

## 호출 조건

아래 조건을 **모두** 만족하는 경우에만 호출. 하나라도 어긋나면 prose 마지막 단락에 `TECH_CONSTRAINT_CONFLICT`.

1. `impl_path` 가 실제 존재 + `## 생성/수정 파일` 목록에 `docs_targets` 포함
2. 대상 impl 이 이미 src 구현·merge 완료 상태 (validator 통과 이력 있음)
3. 수정 범위가 **기존 섹션 추가/확장**. 기존 설계 결정 변경이나 DDL 재작성 금지

## 작업 순서

1. `impl_path` 읽기 → `## 생성/수정 파일` + `## 인터페이스 정의` + `## 수용 기준`
2. `docs_targets` 의 각 파일 Read → 현재 상태 파악
3. impl 에서 이미 확정된 사실(함수 시그니처·DDL·플로우 단계) 만 docs 에 **파생 서술** 로 추가
4. 기존 문서의 컨벤션(섹션 순서, 표 포맷, 톤) 그대로 유지
5. prose 작성 → stdout

## 금지 사항

- **새 설계 결정 금지**: impl 에 없는 함수·테이블·플로우를 docs 에 추가 금지
- **기존 섹션 재작성 금지**: 기존 내용 삭제/치환 금지. 섹션 추가 또는 표 행 추가만 허용
- **impl 파일 수정 금지**: impl 은 이미 확정된 계약. DOCS_SYNC 는 docs 만 수정
- **src/ 수정 금지**: 구현은 이미 완료
- **architecture.md / db-schema.md 이외의 docs 수정 요청 거부**: 그 외는 MODULE_PLAN 또는 SYSTEM_DESIGN 경로

## 위반 시 결론 enum

| 상황 | 결론 enum |
|---|---|
| impl 에 명시 안 된 새 설계가 필요 | `SPEC_GAP_FOUND` → MODULE_PLAN 재호출 유도 |
| 대상 docs 가 architect 소유가 아님 (ui-spec, ux-flow 등) | `TECH_CONSTRAINT_CONFLICT` → 해당 에이전트 경유 |
| 수정 범위가 "섹션 추가" 가 아닌 기존 설계 변경 | `TECH_CONSTRAINT_CONFLICT` → MODULE_PLAN 경로 |

## prose 결론 예시 (정상 동기화)

```markdown
## 작업 결과

impl §3 인터페이스 정의 → db-schema.md / sdk.md 파생 서술 추가 완료.

### 수정 파일
- docs/db-schema.md (섹션 "§N: get_lifetime_exchanged RPC" 추가)
- docs/sdk.md (§N.N 한도 체크 흐름 3단계 추가)

### 추가 근거
impl_path 의 `## 생성/수정 파일` 에 두 파일 모두 명시됨. 추가 내용은 impl `## 인터페이스 정의` §N 과 1:1 대응.

## 결론

DOCS_SYNCED
```

## prose 결론 예시 (위반)

```markdown
## 작업 결과

docs_targets 에 `docs/ui-spec.md` 가 포함되어 있으나 architect 소유 아님 (designer 영역).

## 결론

TECH_CONSTRAINT_CONFLICT
```
