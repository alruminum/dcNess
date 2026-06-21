# 02-speaker-split-panel

## 무엇을 만드나

쇼츠 편집 화면에 화자분리 패널을 추가한다.

## Agent Workability

- owner flow/module: src/ui/speaker_split_panel.py
- entrypoint role: dispatch only; no speaker state ownership
- state owner: SpeakerSplitState in src/ui/speaker_split_panel.py
- allowed touch: app.py dispatch line, src/ui/speaker_split_panel.py, tests/ui/test_speaker_split_panel.py
- forbidden touch: app.py helper/render/session_state expansion
- validation path: python -m pytest tests/ui/test_speaker_split_panel.py
- future change scenario: speaker timeline changes start in src/ui/speaker_split_panel.py

## Scope

### 수정 허용

- app.py
- src/ui/speaker_split_panel.py
- tests/ui/test_speaker_split_panel.py

### 수정 금지

- app.py helper/render/session_state expansion outside dispatch wiring

## 수용 기준

| REQ | 내용 | 검증 | 통과 조건 |
|---|---|---|---|
| REQ-001 | 사용자가 화자분리 패널에서 segment 를 편집한다 | python -m pytest tests/ui/test_speaker_split_panel.py | state update 와 render command 가 owner module 에서 검증됨 |
