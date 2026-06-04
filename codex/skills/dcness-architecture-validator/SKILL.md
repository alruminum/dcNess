# dcness-architecture-validator

## 언제 쓰나

dcNess가 `architecture-validator`를 Codex 교차 검토로 route할 때 사용한다. 구현 착수 전 또는 architecture PR merge 전에 system/module 설계 산출물이 구현 가능한 계약으로 이어지는지 읽기 전용으로 검토한다.

## 목적

Claude-side validator를 복제하지 않는다. 같은 결론 vocabulary를 쓰되, 별도 시각으로 설계 drift, 숨은 결합, 검증 불가능한 acceptance criteria를 찾는다.

## 입력

- architecture 또는 epic 디렉터리 경로
- PRD, story, ADR, architecture, domain-model, implementation task 경로
- 첫 architecture validation인지, module 산출 이후 final validation인지에 대한 호출 맥락
- 필요하면 이전 finding과 재검토 맥락

## 먼저 볼 기준

- 원 요구사항: PRD, story, acceptance criteria
- 현재 설계 산출물: architecture, ADR, domain-model, implementation tasks
- 모듈 설계 원칙: `docs/plugin/module-design-principles.md`
- Claude-side validator와 공유하는 routing vocabulary: `SYSTEM_BOUNDARY`, `CONTRACT_PROPAGATION`, `TASK_LOCAL`

## 판단 축

- 요구사항 출처 충실도: PRD Must와 story intent가 architecture 결정과 impl REQ에서 다른 의미로 변하지 않았는가.
- 설계 표준: 모듈 설계 원칙, 의존 방향, public surface, DI 판단이 문서 evidence로 남았는가.
- 계약과 인터페이스: producer/consumer, public API, state transition, data contract가 같은 의미를 공유하는가.
- 구현 가능성: engineer가 impl 문서만 cold-read해도 정책을 새로 발명하지 않고 구현할 수 있는가.
- drift와 scope: 상위 설계 자체가 틀렸는지, 맞는 결정의 stale copy만 남았는지 구분되는가.
- 표현 수준: impl task가 contract/interface altitude를 지키고 private helper, loop body, forced test name 같은 구현 세부를 선점하지 않는가.

## 작업 흐름

1. 실제로 존재하는 입력 문서만 읽고, 없거나 서로 모순되는 source는 `ESCALATE` 후보로 둔다.
2. 판단 축을 따라 evidence를 찾되, 축별 체크박스를 채우려고 finding을 만들지 않는다.
3. Must finding마다 파일 경로, 라인, 구체적 사실, 영향, 권장 다음 행동을 쓴다.
4. Must finding은 다음 중 하나로 분류한다.
   - `SYSTEM_BOUNDARY`: 상위 boundary, ownership, domain invariant가 틀려 system architecture 재검토가 필요하다.
   - `CONTRACT_PROPAGATION`: 결정은 맞지만 architecture/domain/ADR/impl 문서 사본이 stale해 targeted sync가 필요하다.
   - `TASK_LOCAL`: 단일 implementation task 문서만 잘못되어 해당 task 수정으로 충분하다.
5. 예시에 없는 문제라도 설계 실패 가능성이 evidence로 보이면 finding으로 남긴다.

## 완료 기준

- PASS이면 system-architect 또는 module-architect 재진입이 필요 없는 이유가 설명된다.
- FAIL이면 모든 Must finding에 path:line evidence, 분류 token, 다음 행동이 있다.
- ESCALATE이면 어떤 source 문서나 호출 맥락이 없어 검증이 불가능한지 명확하다.

## 권한 경계

- 읽기 전용이다.
- 파일 생성, 수정, 삭제, commit, push, PR 생성, mutation command 실행을 하지 않는다.
- repo evidence 없이 이름만 보고 함수, field, contract 존재를 추측하지 않는다.
- taste나 문체 선호를 architecture blocker로 올리지 않는다.

## 결론과 보고

간결한 prose로 verdict summary, severity순 finding, 검토한 evidence, 권장 다음 행동을 쓴다. 마지막 단락에는 `PASS`, `FAIL`, `ESCALATE` 중 결론 단어 하나만 명시한다.
