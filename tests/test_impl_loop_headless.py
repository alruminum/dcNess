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
    """build_invocation — 슬래시 직호출 + system prompt 의무 (#431)."""

    def test_first_attempt_slash_with_mandate(self):
        """첫 시도: prompt = `/dcness:impl <path>`, extra_args 에 의무 system prompt."""
        extra_args, prompt = ilh.build_invocation(
            "docs/impl/01-foo.md",
            issue_nums={"task": 272},
        )
        self.assertEqual(prompt, "/dcness:impl docs/impl/01-foo.md")
        # system prompt 의무 박힘
        self.assertEqual(extra_args[0], "--append-system-prompt")
        mandate = extra_args[1]
        # 의무 4 항목
        self.assertIn("begin-run impl --issue-num 272", mandate)
        self.assertIn("end-run", mandate)
        self.assertIn("test-engineer", mandate)
        self.assertIn("engineer", mandate)
        self.assertIn("code-validator", mandate)
        self.assertIn("pr-reviewer", mandate)
        # enum 의무
        self.assertIn("PASS:", mandate)
        self.assertIn("FAIL:", mandate)
        self.assertIn("ESCALATE:", mandate)

    def test_no_issue_num_omits_arg(self):
        """task 이슈 번호 부재 시 begin-run impl (no --issue-num)."""
        extra_args, _ = ilh.build_invocation(
            "docs/impl/01-foo.md",
            issue_nums={"task": None},
        )
        mandate = extra_args[1]
        self.assertIn("begin-run impl)", mandate)
        self.assertNotIn("begin-run impl --issue-num", mandate)

    def test_retry_prepends_prev_error(self):
        """retry: 이전 에러가 의무 앞에 prepend."""
        extra_args, _ = ilh.build_invocation(
            "docs/impl/01-foo.md",
            issue_nums={"task": 100},
            retry_attempt=1,
            prev_error="exit 1\npytest 실패",
        )
        mandate = extra_args[1]
        self.assertIn("이전 시도 실패 (attempt 1)", mandate)
        self.assertIn("pytest 실패", mandate)
        # 의무 본문 여전히 박힘
        self.assertIn("begin-run impl", mandate)

    def test_retry_attempt_zero_no_prev_error_prepend(self):
        """attempt 0 + prev_error 있어도 retry 머리말 inject 안 함 (첫 시도)."""
        extra_args, _ = ilh.build_invocation(
            "docs/impl/01-foo.md",
            issue_nums={},
            retry_attempt=0,
            prev_error="should be ignored",
        )
        self.assertNotIn("이전 시도 실패", extra_args[1])


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
    """spawn_child stream-json 파서 + 간결 progress 검증 (#431 follow-up).

    fake claude CLI 가 stream-json 형식으로 4-step + result event emit.
    parent 가 파싱 → Task tool_use marker + result 만 progress line 으로 echo.
    """

    def setUp(self):
        self._tmp = tempfile.mkdtemp()
        # fake claude — stream-json events (assistant tool_use × 4 + result)
        fake_claude = Path(self._tmp) / "claude"
        fake_claude.write_text(
            "#!/usr/bin/env python3\n"
            "import json, sys, time\n"
            "def emit(ev):\n"
            "    sys.stdout.write(json.dumps(ev) + '\\n')\n"
            "    sys.stdout.flush()\n"
            "for agent, desc in [\n"
            "    ('test-engineer', '테스트 작성'),\n"
            "    ('engineer', '구현'),\n"
            "    ('code-validator', '검증'),\n"
            "    ('pr-reviewer', '리뷰'),\n"
            "]:\n"
            "    emit({'type': 'assistant', 'message': {'content': [\n"
            "        {'type': 'tool_use', 'name': 'Task', 'input': {\n"
            "            'subagent_type': agent, 'description': desc,\n"
            "        }}\n"
            "    ]}})\n"
            "    time.sleep(0.02)\n"
            "emit({'type': 'assistant', 'message': {'content': [\n"
            "    {'type': 'text', 'text': 'PASS: 머지 완료'}\n"
            "]}})\n"
            "emit({'type': 'result', 'result': 'PASS: 머지 완료'})\n"
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

    def test_progress_emits_subagent_markers(self):
        """stream_to 가 sub-agent 호출 marker 를 간결 progress 로 받는지."""
        import io
        sink = io.StringIO()
        exit_code, stdout, _ = ilh.spawn_child(
            "/x", cwd=self._tmp, timeout=10, stream_to=sink,
        )
        self.assertEqual(exit_code, 0)
        sink_content = sink.getvalue()
        # 4 sub-agent marker 모두 progress line 으로 emit
        self.assertIn("ㄴ test-engineer — 테스트 작성", sink_content)
        self.assertIn("ㄴ engineer — 구현", sink_content)
        self.assertIn("ㄴ code-validator — 검증", sink_content)
        self.assertIn("ㄴ pr-reviewer — 리뷰", sink_content)
        # result line 도 emit
        self.assertIn("[result] PASS: 머지 완료", sink_content)

    def test_aggregated_text_for_parse_result(self):
        """aggregated_text 에 subagent_type keyword + assistant text 누적."""
        exit_code, stdout, _ = ilh.spawn_child(
            "/x", cwd=self._tmp, timeout=10, stream_to=None,
        )
        self.assertEqual(exit_code, 0)
        # 4-step 검사용 keyword
        self.assertIn("code-validator", stdout)
        self.assertIn("pr-reviewer", stdout)
        # parse_result 용 enum text
        self.assertIn("PASS: 머지 완료", stdout)


class FalseCleanDowngradeTests(unittest.TestCase):
    """process_task — #422 false-clean 강등 검증."""

    # stdout fixture — inner 4-step 전부 완료 흔적 (enum 미포함). #431 검사 통과용.
    _4STEP_ECHO = (
        "[b1.test-engineer] echo TESTS_WRITTEN\n"
        "[b2.engineer:IMPL] echo IMPL_DONE\n"
        "[b3.code-validator] echo PASS\n"
        "[b4.pr-reviewer] echo LGTM\n"
    )

    def test_pass_prose_but_issue_open_downgrades_to_blocked(self):
        """PASS prose + 4-step 전부 + task 이슈 OPEN → blocked 강등 (#422)."""
        with tempfile.TemporaryDirectory() as tmp:
            task_path = Path(tmp) / "01-foo.md"
            task_path.write_text(
                "# 01-foo\n\n**GitHub Issue:** [#999]\n", encoding="utf-8",
            )

            with mock.patch.object(
                ilh, "spawn_child",
                return_value=(0, self._4STEP_ECHO + "PASS: 머지 완료\n", ""),
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
                return_value=(0, self._4STEP_ECHO + "사용자 위임 enum 없음\n", ""),
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
        """PASS prose + 4-step + task 이슈 CLOSED → 정상 clean (회귀 방지)."""
        with tempfile.TemporaryDirectory() as tmp:
            task_path = Path(tmp) / "01-foo.md"
            task_path.write_text(
                "# 01-foo\n\n**GitHub Issue:** [#777]\n", encoding="utf-8",
            )

            with mock.patch.object(
                ilh, "spawn_child",
                return_value=(0, self._4STEP_ECHO + "PASS: 정상 머지\n", ""),
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

    def test_inner_4step_partial_call_downgrades_to_blocked(self):
        """#431: test-engineer + engineer 만 호출하고 PASS 박는 안티패턴 차단."""
        with tempfile.TemporaryDirectory() as tmp:
            task_path = Path(tmp) / "01-foo.md"
            task_path.write_text(
                "# 01-foo\n\n**GitHub Issue:** [#555]\n", encoding="utf-8",
            )

            # 4-step 중 test-engineer + engineer 만 호출 (#431 사단 재현)
            partial_stdout = (
                "[b1.test-engineer] echo TESTS_WRITTEN\n"
                "[b2.engineer:IMPL] echo IMPL_DONE\n"
                "PASS: 구현 완료\n"
            )
            with mock.patch.object(
                ilh, "spawn_child", return_value=(0, partial_stdout, ""),
            ):
                r = ilh.process_task(
                    str(task_path),
                    cwd=tmp,
                    retry_limit=0,
                    escalate_signals={"blocked"},
                    timeout=10,
                )
                self.assertEqual(r["enum"], "blocked")
                self.assertIn("inner 4-step", r["message"])
                self.assertIn("code-validator", r["message"])
                self.assertIn("pr-reviewer", r["message"])
                self.assertIn("#431", r["message"])

    def test_inner_4step_only_validator_missing(self):
        """#431: pr-reviewer 호출은 있는데 code-validator 만 누락 — 그래도 blocked."""
        with tempfile.TemporaryDirectory() as tmp:
            task_path = Path(tmp) / "01-foo.md"
            task_path.write_text(
                "# 01-foo\n\n**GitHub Issue:** [#556]\n", encoding="utf-8",
            )

            partial_stdout = (
                "[b1.test-engineer] echo TESTS_WRITTEN\n"
                "[b2.engineer:IMPL] echo IMPL_DONE\n"
                "[b4.pr-reviewer] echo LGTM\n"  # code-validator skip
                "PASS: 머지 완료\n"
            )
            with mock.patch.object(
                ilh, "spawn_child", return_value=(0, partial_stdout, ""),
            ):
                r = ilh.process_task(
                    str(task_path),
                    cwd=tmp,
                    retry_limit=0,
                    escalate_signals={"blocked"},
                    timeout=10,
                )
                self.assertEqual(r["enum"], "blocked")
                self.assertIn("code-validator", r["message"])

    def test_no_issue_num_with_uncommitted_files_downgrades(self):
        """task 이슈 번호 부재 + cwd uncommitted files → blocked 강등."""
        with tempfile.TemporaryDirectory() as tmp:
            task_path = Path(tmp) / "01-foo.md"
            task_path.write_text("# 01-foo\n\nno issue ref\n", encoding="utf-8")

            with mock.patch.object(
                ilh, "spawn_child",
                return_value=(0, self._4STEP_ECHO + "PASS: 완료\n", ""),
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
                return_value=(0, self._4STEP_ECHO + "PASS: 완료\n", ""),
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
