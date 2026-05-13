"""scripts/impl_loop_headless.py 단위 테스트.

검증 범위:
- build_invocation() — 슬래시 직호출 (`/dcness:impl <path>`) + retry → --append-system-prompt
- parse_result() — enum 매치 (PASS / FAIL / ESCALATE)
- extract_issue_nums() — task 본문 + 부모 stories.md 매치
- process_task() — #422 false-clean 강등 안전망
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


class BuildInvocationTests(unittest.TestCase):
    """build_invocation — 슬래시 직호출 + retry context 안전성."""

    def test_first_attempt_slash_only(self):
        """첫 시도: prompt = `/dcness:impl <path>`, extra_args = 빈 리스트."""
        extra_args, prompt = ilh.build_invocation("docs/impl/01-foo.md")
        self.assertEqual(extra_args, [])
        self.assertEqual(prompt, "/dcness:impl docs/impl/01-foo.md")

    def test_retry_appends_system_prompt(self):
        """retry: extra_args 에 --append-system-prompt + 이전 에러 inject."""
        extra_args, prompt = ilh.build_invocation(
            "docs/impl/01-foo.md",
            retry_attempt=1,
            prev_error="exit 1\npytest 실패",
        )
        self.assertEqual(extra_args[0], "--append-system-prompt")
        self.assertIn("이전 시도 실패 (attempt 1)", extra_args[1])
        self.assertIn("pytest 실패", extra_args[1])
        self.assertEqual(prompt, "/dcness:impl docs/impl/01-foo.md")

    def test_retry_attempt_zero_no_extra_args(self):
        """attempt 0 + prev_error 있어도 retry 머리말 inject 안 함 (첫 시도)."""
        extra_args, _ = ilh.build_invocation(
            "docs/impl/01-foo.md",
            retry_attempt=0,
            prev_error="should be ignored",
        )
        self.assertEqual(extra_args, [])


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


class SpawnChildStreamTests(unittest.TestCase):
    """spawn_child line-buffered stream 동작 검증 (#429 follow-up).

    fake claude CLI 를 PATH 첫머리에 박아 실제 claude 호출 없이 검증.
    fake CLI = 3 줄 stdout 출력 + 사이에 sleep → buffer-until-end 아닌
    line-by-line 으로 즉시 stream_to 에 echo 되는지 확인.
    """

    def setUp(self):
        self._tmp = tempfile.mkdtemp()
        # fake claude — 3 라인을 0.1s 간격으로 emit (line-buffered 검증)
        fake_claude = Path(self._tmp) / "claude"
        fake_claude.write_text(
            "#!/usr/bin/env python3\n"
            "import sys, time\n"
            "sys.stdout.write('line1\\n'); sys.stdout.flush(); time.sleep(0.05)\n"
            "sys.stdout.write('line2\\n'); sys.stdout.flush(); time.sleep(0.05)\n"
            "sys.stdout.write('PASS: ok\\n'); sys.stdout.flush()\n"
            "sys.exit(0)\n",
            encoding="utf-8",
        )
        fake_claude.chmod(0o755)
        self._old_path = os.environ.get("PATH", "")
        os.environ["PATH"] = f"{self._tmp}{os.pathsep}{self._old_path}"

    def tearDown(self):
        os.environ["PATH"] = self._old_path
        import shutil
        shutil.rmtree(self._tmp, ignore_errors=True)

    def test_stream_to_receives_lines_with_prefix(self):
        """stream_to 가 자식 stdout line 을 '[child] ' 접두 박아 받는지."""
        import io
        sink = io.StringIO()
        exit_code, stdout, stderr = ilh.spawn_child(
            "/some-prompt", cwd=self._tmp, timeout=10,
            stream_to=sink,
        )
        self.assertEqual(exit_code, 0)
        # captured stdout 정합
        self.assertIn("line1", stdout)
        self.assertIn("line2", stdout)
        self.assertIn("PASS: ok", stdout)
        # stream sink 에 prefix 박힌 line stream 도착
        sink_content = sink.getvalue()
        self.assertIn("[child] line1", sink_content)
        self.assertIn("[child] line2", sink_content)
        self.assertIn("[child] PASS: ok", sink_content)

    def test_stream_to_none_skips_echo(self):
        """stream_to=None 시 echo skip — capture 만."""
        # spawn_child 시그니처상 None 전달 시 default sys.stderr 로 들어감.
        # 따라서 stream skip 검증은 sink=io.StringIO() 빈 결과 확인이 아니라
        # default 동작 회귀만 보장. 본 케이스는 capture 정합만 확인.
        exit_code, stdout, _ = ilh.spawn_child(
            "/x", cwd=self._tmp, timeout=10, stream_to=None,
        )
        self.assertEqual(exit_code, 0)
        self.assertIn("PASS: ok", stdout)


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
