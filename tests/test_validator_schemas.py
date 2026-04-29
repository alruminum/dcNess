"""test_validator_schemas.py — agents/validator/*.md 의 status JSON 예시
가 state_io.read_status 와 round-trip 통과하는지 검증.

이 테스트는 *agent docs 의 schema 정합성* 을 자동 강제한다:
1. agents/validator/<mode>.md 의 ```json ... ``` 코드 블록 추출
2. 임시 파일에 write_status 후 read_status(allowed_status=mode_enum) 호출
3. 모든 예시가 모드별 enum 안에 있는지 검증

향후 docs 변경 시 status enum / required 필드가 어긋나면 본 테스트가 즉시 fail.

실행:
    python3 -m unittest tests.test_validator_schemas -v
"""
from __future__ import annotations

import json
import re
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Set

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from harness.state_io import (  # noqa: E402
    MissingStatus,
    read_status,
    write_status,
)


# ─────────────────────────────────────────────────────────────────────────
# Mode → status enum (agents/validator.md 마스터의 매트릭스 정합)
# ─────────────────────────────────────────────────────────────────────────
MODE_ENUM = {
    "PLAN_VALIDATION": {
        "PLAN_VALIDATION_PASS",
        "PLAN_VALIDATION_FAIL",
        "PLAN_VALIDATION_ESCALATE",
    },
    "CODE_VALIDATION": {"PASS", "FAIL", "SPEC_MISSING"},
    "DESIGN_VALIDATION": {
        "DESIGN_REVIEW_PASS",
        "DESIGN_REVIEW_FAIL",
        "DESIGN_REVIEW_ESCALATE",
    },
    "BUGFIX_VALIDATION": {"BUGFIX_PASS", "BUGFIX_FAIL"},
    "UX_VALIDATION": {
        "UX_REVIEW_PASS",
        "UX_REVIEW_FAIL",
        "UX_REVIEW_ESCALATE",
    },
}

MODE_TO_FILE = {
    "PLAN_VALIDATION": "plan-validation.md",
    "CODE_VALIDATION": "code-validation.md",
    "DESIGN_VALIDATION": "design-validation.md",
    "BUGFIX_VALIDATION": "bugfix-validation.md",
    "UX_VALIDATION": "ux-validation.md",
}

VALIDATOR_DIR = REPO_ROOT / "agents" / "validator"

# ```json ... ``` 코드 블록 추출 (multiline)
JSON_BLOCK_RE = re.compile(r"```json\n(.*?)```", re.DOTALL)


def extract_json_blocks(md_path: Path) -> list[dict]:
    """sub-doc 의 ```json ... ``` 코드 블록을 모두 파싱해 dict 리스트로 반환."""
    text = md_path.read_text(encoding="utf-8")
    blocks: list[dict] = []
    for match in JSON_BLOCK_RE.finditer(text):
        raw = match.group(1).strip()
        # 예시 안에 // 주석이 있으면 json.loads 가 실패 — 주석 라인 제거
        cleaned = "\n".join(
            line for line in raw.splitlines()
            if not line.lstrip().startswith("//")
        )
        # 주석이 라인 끝에 붙어 있을 수도 있음 — 보수적으로 // 부터 라인 끝까지 제거
        cleaned = re.sub(r"\s*//[^\n]*", "", cleaned)
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as e:
            raise AssertionError(
                f"{md_path.name}: ```json``` block parse error: {e}\nblock:\n{raw}"
            ) from e
        if isinstance(data, dict):
            blocks.append(data)
    return blocks


class TestValidatorSchemas(unittest.TestCase):
    """각 모드의 ```json``` 예시가 state_io 와 round-trip 통과."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory()
        cls.base = Path(cls._tmp.name)
        cls.run_id = "test_validator_schemas"

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    def _check_mode(self, mode: str) -> None:
        md = VALIDATOR_DIR / MODE_TO_FILE[mode]
        self.assertTrue(md.exists(), f"agent docs 부재: {md}")

        blocks = extract_json_blocks(md)
        self.assertGreaterEqual(
            len(blocks), 2,
            f"{md.name}: 예시 블록이 2개 미만 (PASS/FAIL 최소 1개씩 기대)",
        )

        allowed: Set[str] = MODE_ENUM[mode]

        for idx, payload in enumerate(blocks):
            with self.subTest(mode=mode, block_idx=idx):
                # write_status: status 키 + str 강제
                self.assertIn("status", payload, f"block {idx}: 'status' 누락")
                self.assertIsInstance(payload["status"], str)

                # status enum 정합
                self.assertIn(
                    payload["status"], allowed,
                    f"block {idx}: status={payload['status']!r} not in {sorted(allowed)}",
                )

                # round-trip
                write_status(
                    "validator", self.run_id, payload,
                    mode=mode, base_dir=self.base,
                )
                got = read_status(
                    "validator", self.run_id,
                    mode=mode, base_dir=self.base,
                    allowed_status=allowed,
                )
                self.assertEqual(got["status"], payload["status"])

                # FAIL/ESCALATE 시 fail_items 필수 (마스터 schema 룰)
                if (
                    payload["status"].endswith("FAIL")
                    or payload["status"].endswith("ESCALATE")
                ):
                    self.assertIn(
                        "fail_items", payload,
                        f"block {idx}: FAIL/ESCALATE 인데 fail_items 부재",
                    )
                    self.assertIsInstance(payload["fail_items"], list)

    def test_plan_validation(self) -> None:
        self._check_mode("PLAN_VALIDATION")

    def test_code_validation(self) -> None:
        self._check_mode("CODE_VALIDATION")

    def test_design_validation(self) -> None:
        self._check_mode("DESIGN_VALIDATION")

    def test_bugfix_validation(self) -> None:
        self._check_mode("BUGFIX_VALIDATION")

    def test_ux_validation(self) -> None:
        self._check_mode("UX_VALIDATION")


class TestMasterMatrix(unittest.TestCase):
    """agents/validator.md 마스터의 모드 매트릭스가 sub-doc 과 정합."""

    def test_master_lists_all_five_modes(self) -> None:
        master = (REPO_ROOT / "agents" / "validator.md").read_text(encoding="utf-8")
        for mode in MODE_ENUM:
            self.assertIn(
                f"@MODE:VALIDATOR:{mode}", master,
                f"마스터에 {mode} 매트릭스 entry 부재",
            )

    def test_master_references_all_sub_docs(self) -> None:
        master = (REPO_ROOT / "agents" / "validator.md").read_text(encoding="utf-8")
        for filename in MODE_TO_FILE.values():
            self.assertIn(
                f"validator/{filename}", master,
                f"마스터가 sub-doc {filename} 참조 안 함",
            )

    def test_master_no_legacy_marker_convention(self) -> None:
        """폐기 컨벤션 (---MARKER:X---) 이 결정 원천으로 박혀있지 않은지."""
        master = (REPO_ROOT / "agents" / "validator.md").read_text(encoding="utf-8")
        # "폐기된 컨벤션" 섹션 안의 언급은 허용 — *결정 원천* 으로 박혀있는지만 검사.
        # "@OUTPUT_FILE" 이 마스터에 명시 + "---MARKER:" 가 *결정 룰* 로 명시되지 않으면 OK.
        self.assertIn("@OUTPUT_FILE", master)
        self.assertIn("status JSON", master)

    def test_master_has_no_preamble_dependency(self) -> None:
        """preamble.md 자동 주입 의존이 명시되지 않은지."""
        master = (REPO_ROOT / "agents" / "validator.md").read_text(encoding="utf-8")
        # "preamble.md 에서 자동 주입" 같은 의존 표현이 *결정 룰* 로 박혀있지 않은지
        self.assertNotIn("preamble.md에서 자동 주입", master)
        self.assertNotIn("preamble.md 에서 자동 주입", master)


if __name__ == "__main__":
    unittest.main(verbosity=2)
