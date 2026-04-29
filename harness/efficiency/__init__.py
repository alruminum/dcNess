"""harness.efficiency — Claude Code 세션 JSONL 토큰 효율 분석 + 대시보드 생성.

출처 (attribution):
    jha0313/skills_repo `improve-token-efficiency` (MIT 가정 — public repo,
    license 파일 부재). 2026-04-30 dcness 가 fork 흡수 (DCN-CHG-20260430-08).

dcness 통합:
    - 4 script (analyze_sessions / build_dashboard / detect_patterns /
      build_patterns_dashboard) 본 패키지에 보존.
    - skill prompt = `commands/efficiency.md`.
    - wrapper script = `scripts/dcness-efficiency` (PYTHONPATH 자동 + analyze →
      build_dashboard chain).
    - skill 진입 = dcness conveyor 패턴 (begin-run / end-run, finalize-run 미사용
      — read-only 분석 도구라 catastrophic 룰 비대상).

가격 update 시 `analyze_sessions.PRICING` dict 수정.
"""
