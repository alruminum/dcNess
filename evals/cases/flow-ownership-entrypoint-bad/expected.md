# 정답표 — 계약 수준

검수 보고를 채점할 때 아래 기대만 본다. 어떤 검수자가 어떤 문구로 말했는지, 결함이 몇 개인지는 채점하지 않는다.

- [E1][MUST] 보고가 새 화면 또는 panel 흐름이 기존 entrypoint 에 helper/render/state append 로 흡수되어 다음 변경 대상이 불명확해진다는 취지의 결함을 지적한다.
- [E2][MUST] 보고가 state owner 또는 validation path 가 별도 owner module 근처에 남지 않고 entrypoint/session state 에 흩어진다는 취지의 결함을 지적한다.
- [E3][MUST] 최종 결론이 통과(PASS)가 아니다.
