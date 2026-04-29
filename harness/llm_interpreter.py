"""llm_interpreter.py — Anthropic Claude haiku 기반 prose 결론 해석기.

발상 (status-json-mutate-pattern.md §3):
    "harness 가 stdout 캡처 → 메타 LLM (haiku) 1 호출:
     '다음 prose 의 결론은 PASS/FAIL/SPEC_MISSING 중 무엇? 한 단어.'"

본 모듈은 `harness/signal_io.py` 의 `interpret_signal(prose, allowed, interpreter=)` 의
프로덕션 swap 함수 = `make_haiku_interpreter()` 를 제공한다.

사용:
    from harness.signal_io import interpret_signal
    from harness.llm_interpreter import make_haiku_interpreter

    fn = make_haiku_interpreter()  # ANTHROPIC_API_KEY 환경변수
    result = interpret_signal(prose, ["PASS", "FAIL"], interpreter=fn)

설계 결정:
    1. **휴리스틱 우선** — `signal_io._heuristic_interpret` 가 단어경계 단일 매칭에
       성공하면 LLM 호출 0. haiku 는 *fallback* 으로 ambiguous 케이스만 처리.
       비용 minimization (proposal §3 cycle 당 $0.001 미만 목표).
    2. **Caching 미적용** — 시스템 prompt ~50 토큰. haiku 의 caching 최소(~1024 토큰)
       미달 + 매 호출마다 prose 다름 → cache hit 0. 비용/지연 손익 negative.
    3. **결과 단어 1개 강제** — system prompt 가 "한 단어. allowed 외 출력 시 unknown"
       지시. parse 시 strip + uppercase + allowed 매칭. 매칭 실패 = ambiguous.
    4. **DI 우선** — `make_haiku_interpreter(client=...)` 로 mocked client 주입 가능.
       테스트는 이 경로로 실 SDK 호출 회피.
    5. **모델 ID** — `claude-haiku-4-5-20251001` (시스템 안내 cutoff 정합).

Cost telemetry:
    각 호출의 input_tokens / output_tokens / total_cost_usd 를
    `.metrics/meta-llm-calls.jsonl` 에 append (proposal R8 정합).
    환경변수 `DCNESS_LLM_TELEMETRY=0` 이면 비활성.

비용 모델 (claude-haiku-4-5, 2026-04 기준 추정):
    input: $1 / 1M tokens
    output: $5 / 1M tokens
    평균 호출 = 80 in + 5 out = $0.000105 (~$0.0001/호출)
"""
from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional

from harness.signal_io import MissingSignal

__all__ = [
    "make_haiku_interpreter",
    "DEFAULT_MODEL",
    "MAX_PROSE_TAIL_CHARS",
]

DEFAULT_MODEL = "claude-haiku-4-5-20251001"
MAX_PROSE_TAIL_CHARS = 4000  # ~ 1000 tokens; proposal R2 (마지막 500 토큰만 전달) 정합

_PRICE_PER_M_INPUT_USD = 1.0
_PRICE_PER_M_OUTPUT_USD = 5.0


def _build_system_prompt(allowed: list[str]) -> str:
    """system prompt 단일 책임 — allowed enum + 출력 규약."""
    enum_str = " / ".join(allowed)
    return (
        "You classify a verification report into exactly one of these labels: "
        f"{enum_str}.\n"
        "Rules:\n"
        "- Output ONLY the label, in upper case, no other text.\n"
        "- If the report does not clearly indicate any label, output: UNKNOWN.\n"
        "- Do not explain. Do not apologize. Do not output multiple labels."
    )


def _build_user_prompt(prose: str) -> str:
    tail = prose[-MAX_PROSE_TAIL_CHARS:]
    return (
        "Classify this report's conclusion. Output one label only.\n\n"
        "---\n"
        f"{tail}\n"
        "---"
    )


def _telemetry_path(base_dir: Optional[Path] = None) -> Path:
    base = base_dir or (Path.cwd() / ".metrics")
    return base / "meta-llm-calls.jsonl"


def _record_telemetry(
    event: dict[str, Any],
    *,
    base_dir: Optional[Path] = None,
) -> None:
    if os.environ.get("DCNESS_LLM_TELEMETRY", "1") == "0":
        return
    path = _telemetry_path(base_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


def _estimate_cost_usd(input_tokens: int, output_tokens: int) -> float:
    return (
        input_tokens * _PRICE_PER_M_INPUT_USD / 1_000_000
        + output_tokens * _PRICE_PER_M_OUTPUT_USD / 1_000_000
    )


def make_haiku_interpreter(
    *,
    client: Any = None,
    model: str = DEFAULT_MODEL,
    telemetry_dir: Optional[Path] = None,
) -> Callable[[str, list[str]], str]:
    """Anthropic Claude haiku 호출 interpreter 팩토리.

    Args:
        client: Anthropic SDK client. None 이면 `anthropic.Anthropic()` 자동 생성
                (ANTHROPIC_API_KEY 환경변수 필수). 테스트는 mock 주입.
        model: 모델 ID. 기본 = claude-haiku-4-5-20251001.
        telemetry_dir: 호출 로그 디렉토리. None = `.metrics/`.

    Returns:
        `(prose: str, allowed: list[str]) -> str` 형식 callable.
        signal_io.interpret_signal 의 interpreter= 인자에 그대로 전달.

    Raises:
        ImportError: client=None 인데 anthropic 패키지 미설치.
        RuntimeError: API 호출 실패.
        MissingSignal('ambiguous'): 모델이 UNKNOWN 또는 allowed 외 값 반환.
    """
    if client is None:
        try:
            import anthropic  # noqa: WPS433 — 지연 import 가 의도 (SDK 미설치 환경 허용)
        except ImportError as e:
            raise ImportError(
                "anthropic 패키지 미설치. `pip install anthropic` 후 재시도. "
                "또는 client= 인자로 mock 주입."
            ) from e
        client = anthropic.Anthropic()

    def _call(prose: str, allowed: list[str]) -> str:
        if not allowed:
            raise ValueError("allowed must be non-empty")

        system = _build_system_prompt(allowed)
        user = _build_user_prompt(prose)

        started = time.time()
        try:
            response = client.messages.create(
                model=model,
                max_tokens=10,
                system=system,
                messages=[{"role": "user", "content": user}],
            )
        except Exception as e:
            raise RuntimeError(f"Anthropic API 호출 실패: {e}") from e
        elapsed_ms = int((time.time() - started) * 1000)

        # response.content 는 ContentBlock 리스트. 첫 번째 text block 추출.
        raw_text = ""
        for block in getattr(response, "content", []):
            if getattr(block, "type", None) == "text":
                raw_text = getattr(block, "text", "")
                break
        if not raw_text:
            raise MissingSignal(
                "ambiguous", f"empty model response (model={model})"
            )

        # 첫 단어만 추출 + 정규화
        first_word = raw_text.strip().split()[0] if raw_text.strip() else ""
        normalized = first_word.upper().rstrip(".,;:!?")

        usage = getattr(response, "usage", None)
        input_tokens = getattr(usage, "input_tokens", 0) if usage else 0
        output_tokens = getattr(usage, "output_tokens", 0) if usage else 0
        cost = _estimate_cost_usd(input_tokens, output_tokens)

        _record_telemetry(
            {
                "ts": datetime.now(timezone.utc).isoformat(),
                "model": model,
                "allowed": allowed,
                "raw_response": raw_text[:200],
                "parsed": normalized,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost_usd": round(cost, 6),
                "elapsed_ms": elapsed_ms,
            },
            base_dir=telemetry_dir,
        )

        if normalized == "UNKNOWN" or normalized not in allowed:
            raise MissingSignal(
                "ambiguous",
                f"model returned {normalized!r} not in allowed {allowed}",
            )
        return normalized

    return _call
