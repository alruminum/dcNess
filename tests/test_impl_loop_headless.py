"""scripts/impl_loop_headless.py 단위 테스트.

검증 범위:
- build_command() — [A]~[E] 5 묶음 inline 포함
- parse_result() — prose enum 매치 (PASS / FAIL / ESCALATE)
- extract_issue_nums() — task 본문 + 부모 stories.md 매치
- main() — glob 매치 0 → exit 1
"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import impl_loop_headless as ilh  # noqa: E402


class BuildCommandTests(unittest.TestCase):
    """build_command — [A]~[E] inline 포함 검증."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._impl_path = Path(self._tmp.name) / "01-foo.md"
        self._impl_path.write_text("# 01-foo\n\n본문 내용.\n", encoding="utf-8")

    def tearDown(self):
        self._tmp.cleanup()

    def test_all_sections_present(self):
        prompt = ilh.build_command(
            str(self._impl_path),
            issue_nums={"epic": 100, "story": 101, "task": 102},
        )
        self.assertIn("## [A] 이번 task impl 본문", prompt)
        self.assertIn("# 01-foo", prompt)  # 본문 inline
        self.assertIn("## [B] 부모 이슈", prompt)
        self.assertIn("#102", prompt)
        self.assertIn("gh issue view 102", prompt)
        self.assertIn("## [C] 사전 read 의무", prompt)
        self.assertIn("docs/architecture.md", prompt)
        self.assertIn("docs/adr.md", prompt)
        self.assertIn("## [D] 종료 신호 규칙", prompt)
        self.assertIn("PASS:", prompt)
        self.assertIn("FAIL:", prompt)
        self.assertIn("ESCALATE:", prompt)
        self.assertIn("## [E] 작업 시작", prompt)

    def test_e_section_includes_conveyor_cycle_commands(self):
        """#422: [E] 가 begin-run / begin-step / end-step / end-run 명시 호출 박음."""
        prompt = ilh.build_command(
            str(self._impl_path),
            issue_nums={"epic": None, "story": None, "task": 102},
        )
        self.assertIn("begin-run impl --issue-num 102", prompt)
        self.assertIn("begin-step <agent>", prompt)
        self.assertIn("end-step <agent>", prompt)
        self.assertIn("end-run", prompt)

    def test_e_section_conveyor_without_issue_num(self):
        """#422: task 이슈 번호 부재 시 begin-run impl (--issue-num 없음)."""
        prompt = ilh.build_command(
            str(self._impl_path),
            issue_nums={"epic": None, "story": None, "task": None},
        )
        self.assertIn('"$HELPER" begin-run impl)', prompt)
        self.assertNotIn("begin-run impl --issue-num", prompt)

    def test_no_issue_nums(self):
        prompt = ilh.build_command(
            str(self._impl_path),
            issue_nums={"epic": None, "story": None, "task": None},
        )
        self.assertIn("매칭된 이슈 번호 없음", prompt)

    def test_retry_attempt_prepends_prev_error(self):
        prompt = ilh.build_command(
            str(self._impl_path),
            issue_nums={"epic": None, "story": None, "task": 1},
            retry_attempt=1,
            prev_error="some build error",
        )
        self.assertIn("⚠ 이전 시도 실패 (attempt 1)", prompt)
        self.assertIn("some build error", prompt)


class ParseResultTests(unittest.TestCase):
    """parse_result — prose enum 매치."""

    def test_pass(self):
        stdout = "...\n로그 줄들\nPASS: 모든 테스트 통과\n"
        enum, msg = ilh.parse_result(stdout, exit_code=0)
        self.assertEqual(enum, "clean")
        self.assertEqual(msg, "모든 테스트 통과")

    def test_fail(self):
        stdout = "...\nFAIL: pytest exit 1 — 2 failures\n"
        enum, msg = ilh.parse_result(stdout, exit_code=1)
        self.assertEqual(enum, "error")
        self.assertIn("pytest exit 1", msg)

    def test_escalate_overrides_other_enums(self):
        # ESCALATE 가 다른 enum 보다 우선
        stdout = "PASS: 일부\nESCALATE: API 키 필요\n"
        enum, msg = ilh.parse_result(stdout, exit_code=0)
        self.assertEqual(enum, "blocked")
        self.assertIn("API 키 필요", msg)

    def test_no_enum_exit_zero_fallback_clean(self):
        stdout = "그냥 평범한 출력 enum 없음\n"
        enum, msg = ilh.parse_result(stdout, exit_code=0)
        self.assertEqual(enum, "clean")
        self.assertIn("prose enum 미박힘", msg)

    def test_no_enum_exit_nonzero_fallback_error(self):
        stdout = "그냥 평범한 출력 enum 없음\n"
        enum, msg = ilh.parse_result(stdout, exit_code=2)
        self.assertEqual(enum, "error")
        self.assertIn("exit 2", msg)


class ExtractIssueNumsTests(unittest.TestCase):
    """extract_issue_nums — task 본문 + 부모 stories.md."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        # 구조: <tmp>/epic-01-foo/impl/01-bar.md  +  <tmp>/epic-01-foo/stories.md
        self._epic_dir = Path(self._tmp.name) / "epic-01-foo"
        self._impl_dir = self._epic_dir / "impl"
        self._impl_dir.mkdir(parents=True)
        self._task_path = self._impl_dir / "01-bar.md"
        self._stories_path = self._epic_dir / "stories.md"

    def tearDown(self):
        self._tmp.cleanup()

    def test_task_body_github_issue_pattern(self):
        self._task_path.write_text(
            "# 01-bar\n\n**GitHub Issue:** [#345]\n", encoding="utf-8",
        )
        nums = ilh.extract_issue_nums(str(self._task_path))
        self.assertEqual(nums["task"], 345)

    def test_task_body_closes_pattern(self):
        self._task_path.write_text(
            "# 01-bar\n\nFixes #777 in this task.\n", encoding="utf-8",
        )
        nums = ilh.extract_issue_nums(str(self._task_path))
        self.assertEqual(nums["task"], 777)

    def test_parent_stories_epic_issue(self):
        self._task_path.write_text("# 01-bar\n\n", encoding="utf-8")
        self._stories_path.write_text(
            "# Story Backlog\n\n**GitHub Epic Issue:** [#42]\n", encoding="utf-8",
        )
        nums = ilh.extract_issue_nums(str(self._task_path))
        self.assertEqual(nums["epic"], 42)

    def test_no_match_returns_nones(self):
        self._task_path.write_text("# 01-bar\n\nno issue ref\n", encoding="utf-8")
        nums = ilh.extract_issue_nums(str(self._task_path))
        self.assertIsNone(nums["task"])
        self.assertIsNone(nums["epic"])


class MainNoMatchTests(unittest.TestCase):
    """main() — glob 매치 0 → exit 1."""

    def test_no_files_matched(self):
        with tempfile.TemporaryDirectory() as tmp:
            empty_glob = str(Path(tmp) / "no-such-pattern-*.md")
            exit_code = ilh.main([empty_glob])
            self.assertEqual(exit_code, 1)


class EscalateSetTests(unittest.TestCase):
    """process_task — escalate 신호 set 정합 (claude -p 호출은 mock)."""

    def test_blocked_signal_stops_immediately(self):
        with tempfile.TemporaryDirectory() as tmp:
            task_path = Path(tmp) / "01-foo.md"
            task_path.write_text("# 01-foo\n\nbody\n", encoding="utf-8")

            with mock.patch.object(
                ilh, "spawn_child",
                return_value=(0, "ESCALATE: 외부 API 키 필요\n", ""),
            ):
                r = ilh.process_task(
                    str(task_path),
                    cwd=tmp,
                    retry_limit=3,
                    escalate_signals={"blocked"},
                    timeout=10,
                )
                self.assertEqual(r["enum"], "blocked")
                self.assertIn("외부 API 키 필요", r["message"])

    def test_error_retries_then_gives_up(self):
        with tempfile.TemporaryDirectory() as tmp:
            task_path = Path(tmp) / "01-foo.md"
            task_path.write_text("# 01-foo\n\nbody\n", encoding="utf-8")

            with mock.patch.object(
                ilh, "spawn_child",
                return_value=(1, "FAIL: 빌드 실패\n", "stderr tail"),
            ):
                r = ilh.process_task(
                    str(task_path),
                    cwd=tmp,
                    retry_limit=2,  # 3회 시도 (0, 1, 2)
                    escalate_signals={"blocked"},
                    timeout=10,
                )
                self.assertEqual(r["enum"], "error")
                self.assertIn("retry 한도", r["message"])


class FalseCleanDowngradeTests(unittest.TestCase):
    """process_task — #422 false-clean 강등 검증."""

    def test_pass_prose_but_issue_open_downgrades_to_blocked(self):
        """PASS prose + task 이슈 OPEN → clean 아닌 blocked 강등."""
        with tempfile.TemporaryDirectory() as tmp:
            task_path = Path(tmp) / "01-foo.md"
            task_path.write_text(
                "# 01-foo\n\n**GitHub Issue:** [#999]\n", encoding="utf-8",
            )

            with mock.patch.object(
                ilh, "spawn_child",
                return_value=(0, "...\nPASS: 머지 완료\n", ""),
            ), mock.patch.object(
                ilh, "confirm_issue_closed", return_value=False,
            ):
                r = ilh.process_task(
                    str(task_path),
                    cwd=tmp,
                    retry_limit=0,
                    escalate_signals={"blocked"},
                    timeout=10,
                )
                self.assertEqual(r["enum"], "blocked")
                self.assertIn("false-clean", r["message"])
                self.assertIn("#999", r["message"])

    def test_exit_zero_fallback_with_open_issue_downgrades(self):
        """enum 누락 + exit 0 fallback clean + 이슈 OPEN → blocked 강등 (NS2 케이스)."""
        with tempfile.TemporaryDirectory() as tmp:
            task_path = Path(tmp) / "01-foo.md"
            task_path.write_text(
                "# 01-foo\n\n**GitHub Issue:** [#888]\n", encoding="utf-8",
            )

            with mock.patch.object(
                ilh, "spawn_child",
                return_value=(0, "사용자에게 위임합니다 enum 없음\n", ""),
            ), mock.patch.object(
                ilh, "confirm_issue_closed", return_value=False,
            ):
                r = ilh.process_task(
                    str(task_path),
                    cwd=tmp,
                    retry_limit=0,
                    escalate_signals={"blocked"},
                    timeout=10,
                )
                self.assertEqual(r["enum"], "blocked")
                self.assertIn("#888", r["message"])

    def test_pass_with_closed_issue_stays_clean(self):
        """PASS prose + task 이슈 CLOSED → 정상 clean (회귀 방지)."""
        with tempfile.TemporaryDirectory() as tmp:
            task_path = Path(tmp) / "01-foo.md"
            task_path.write_text(
                "# 01-foo\n\n**GitHub Issue:** [#777]\n", encoding="utf-8",
            )

            with mock.patch.object(
                ilh, "spawn_child",
                return_value=(0, "PASS: 정상 머지\n", ""),
            ), mock.patch.object(
                ilh, "confirm_issue_closed", return_value=True,
            ):
                r = ilh.process_task(
                    str(task_path),
                    cwd=tmp,
                    retry_limit=0,
                    escalate_signals={"blocked"},
                    timeout=10,
                )
                self.assertEqual(r["enum"], "clean")

    def test_no_issue_num_with_uncommitted_files_downgrades(self):
        """task 이슈 번호 부재 + cwd uncommitted files → blocked 강등."""
        with tempfile.TemporaryDirectory() as tmp:
            task_path = Path(tmp) / "01-foo.md"
            task_path.write_text("# 01-foo\n\nno issue ref\n", encoding="utf-8")

            with mock.patch.object(
                ilh, "spawn_child",
                return_value=(0, "PASS: 완료\n", ""),
            ), mock.patch.object(
                ilh.subprocess, "run",
                return_value=mock.Mock(stdout=" M some_file.py\n"),
            ):
                r = ilh.process_task(
                    str(task_path),
                    cwd=tmp,
                    retry_limit=0,
                    escalate_signals={"blocked"},
                    timeout=10,
                )
                self.assertEqual(r["enum"], "blocked")
                self.assertIn("uncommitted", r["message"])

    def test_no_issue_num_clean_cwd_stays_clean(self):
        """task 이슈 번호 부재 + cwd clean → 정상 clean (회귀 방지)."""
        with tempfile.TemporaryDirectory() as tmp:
            task_path = Path(tmp) / "01-foo.md"
            task_path.write_text("# 01-foo\n\nno issue ref\n", encoding="utf-8")

            with mock.patch.object(
                ilh, "spawn_child",
                return_value=(0, "PASS: 완료\n", ""),
            ), mock.patch.object(
                ilh.subprocess, "run",
                return_value=mock.Mock(stdout=""),
            ):
                r = ilh.process_task(
                    str(task_path),
                    cwd=tmp,
                    retry_limit=0,
                    escalate_signals={"blocked"},
                    timeout=10,
                )
                self.assertEqual(r["enum"], "clean")


if __name__ == "__main__":
    unittest.main()
