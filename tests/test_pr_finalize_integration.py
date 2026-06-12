"""pr-finalize 통합 브랜치 sub-PR 처리 테스트.

base ≠ default branch 인 sub-PR 에서 (1) CI 체크 0개를 정상으로 처리하고
(2) 머지 후 PR body 의 close 선언 기반 issue close 보정이 와이어링됐는지 확인한다.
(기존 test_pr_finalize_peer_lock.py 와 같은 content-assertion 패턴.)
"""
from __future__ import annotations

import subprocess
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / "scripts" / "pr-finalize.sh"


class PrFinalizeIntegrationBranchTests(unittest.TestCase):
    def setUp(self) -> None:
        self.script = SCRIPT_PATH.read_text(encoding="utf-8")

    def test_script_syntax_valid(self) -> None:
        result = subprocess.run(
            ["bash", "-n", str(SCRIPT_PATH)], capture_output=True, text=True
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_detects_integration_base_via_default_branch_ref(self) -> None:
        self.assertIn("defaultBranchRef", self.script)
        self.assertIn("baseRefName", self.script)
        self.assertIn("INTEGRATION=true", self.script)

    def test_zero_checks_pass_only_in_integration_mode(self) -> None:
        # check-run 0개 재확인은 통합 브랜치 모드 분기 안에서만 일어난다.
        self.assertIn("check-runs", self.script)
        self.assertIn('CHECK_COUNT" = "0"', self.script)
        idx_integration_guard = self.script.index('[ "$INTEGRATION" = "true" ]')
        idx_check_runs = self.script.index("check-runs")
        self.assertLess(idx_integration_guard, idx_check_runs)

    def test_close_compensation_uses_pr_body_declarations(self) -> None:
        # close 보정은 PR body 의 Closes/Fixes/Resolves 선언만 근거로 한다 —
        # Part of 는 매치되지 않아야 한다 (선언 없는 issue 임의 close 금지).
        self.assertIn("gh issue close", self.script)
        self.assertIn("close[sd]?", self.script)
        self.assertIn("resolve[sd]?", self.script)
        self.assertNotIn("Part of", self.script.split("gh issue close")[0].split("CLOSE_NUMS=")[-1])

    def test_close_keyword_extraction_ignores_part_of(self) -> None:
        body = "Closes #219\ntask-index: 3/3\nPart of #220\nFixes #11\n"
        pipeline = (
            "grep -ioE '(close[sd]?|fix(e[sd])?|resolve[sd]?)[[:space:]]+#[0-9]+'"
            " | grep -oE '[0-9]+' | sort -un"
        )
        result = subprocess.run(
            ["bash", "-c", f"printf '%s' \"$1\" | {pipeline}", "_", body],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.stdout.split(), ["11", "219"])

    def test_close_only_when_issue_open(self) -> None:
        self.assertIn('ISSUE_STATE" = "OPEN"', self.script)

    def test_fetches_integration_base_after_merge(self) -> None:
        self.assertIn('git fetch origin "$BASE_REF"', self.script)
        self.assertIn('git fetch origin "$DEFAULT_REF"', self.script)


if __name__ == "__main__":
    unittest.main()
