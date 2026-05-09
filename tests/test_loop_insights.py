"""test_loop_insights — loop_insights 모듈 단위 테스트 (DCN-CHG-20260502-02).

Coverage:
    insights_path:
        - mode 있음 / 없음 파일명 규칙

    read:
        - 파일 없음 → ""
        - 파일 있음 → 전체 내용 반환

    append_findings:
        - 신규 파일 생성 + 헤더 + 섹션 구조
        - 기존 파일에 bads append
        - 기존 파일에 goods append
        - 중복 항목 스킵
        - bads/goods 모두 빈 리스트 → 파일 미생성

    append_from_run:
        - redo-log REDO_* 항목 → bads 누적
        - PASS 항목 스킵
        - redo reason 없는 항목 스킵
        - 빈 redo-log + 빈 steps → 수정 파일 없음
"""
import json
import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from harness.loop_insights import (
    insights_path,
    read,
    append_findings,
    append_from_run,
)


class TestInsightsPath(unittest.TestCase):
    def test_no_mode(self):
        p = insights_path("engineer", cwd=Path("/tmp"))
        self.assertEqual(p.name, "engineer.md")

    def test_with_mode(self):
        p = insights_path("engineer", "IMPL", cwd=Path("/tmp"))
        self.assertEqual(p.name, "engineer-IMPL.md")

    def test_dir_structure(self):
        p = insights_path("validator", "CODE_VALIDATION", cwd=Path("/tmp"))
        self.assertIn(".claude/loop-insights", str(p))


class TestRead(unittest.TestCase):
    def test_missing_file_returns_empty(self):
        with tempfile.TemporaryDirectory() as td:
            result = read("engineer", "IMPL", cwd=Path(td))
            self.assertEqual(result, "")

    def test_existing_file_returns_content(self):
        with tempfile.TemporaryDirectory() as td:
            p = insights_path("engineer", "IMPL", cwd=Path(td))
            p.parent.mkdir(parents=True)
            p.write_text("# Loop Insights\ncontent", encoding="utf-8")
            result = read("engineer", "IMPL", cwd=Path(td))
            self.assertIn("content", result)


class TestAppendFindings(unittest.TestCase):
    def test_creates_new_file_with_header(self):
        with tempfile.TemporaryDirectory() as td:
            append_findings("engineer", "IMPL", ["bad thing"], [], cwd=Path(td))
            p = insights_path("engineer", "IMPL", cwd=Path(td))
            self.assertTrue(p.exists())
            content = p.read_text()
            self.assertIn("# Loop Insights: engineer / IMPL", content)
            self.assertIn("bad thing", content)
            self.assertIn("하지 말 것", content)

    def test_creates_new_file_no_mode(self):
        with tempfile.TemporaryDirectory() as td:
            append_findings("test-engineer", None, ["bad"], [], cwd=Path(td))
            p = insights_path("test-engineer", None, cwd=Path(td))
            content = p.read_text()
            self.assertIn("# Loop Insights: test-engineer", content)
            self.assertNotIn("# Loop Insights: test-engineer /", content)

    def test_appends_to_existing(self):
        with tempfile.TemporaryDirectory() as td:
            append_findings("engineer", "IMPL", ["first bad"], [], cwd=Path(td))
            append_findings("engineer", "IMPL", ["second bad"], [], cwd=Path(td))
            content = insights_path("engineer", "IMPL", cwd=Path(td)).read_text()
            self.assertIn("first bad", content)
            self.assertIn("second bad", content)

    def test_appends_goods(self):
        with tempfile.TemporaryDirectory() as td:
            append_findings("engineer", "IMPL", [], ["good thing"], cwd=Path(td))
            content = insights_path("engineer", "IMPL", cwd=Path(td)).read_text()
            self.assertIn("잘 됐던 것", content)
            self.assertIn("good thing", content)

    def test_skips_duplicate(self):
        with tempfile.TemporaryDirectory() as td:
            append_findings("engineer", "IMPL", ["same bad"], [], cwd=Path(td))
            append_findings("engineer", "IMPL", ["same bad"], [], cwd=Path(td))
            content = insights_path("engineer", "IMPL", cwd=Path(td)).read_text()
            self.assertEqual(content.count("same bad"), 1)

    def test_noop_when_empty(self):
        with tempfile.TemporaryDirectory() as td:
            append_findings("engineer", "IMPL", [], [], cwd=Path(td))
            p = insights_path("engineer", "IMPL", cwd=Path(td))
            self.assertFalse(p.exists())


class TestAppendFromRun(unittest.TestCase):
    def _make_redo_entry(self, sub, mode, decision, reason):
        return {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "sub": sub,
            "mode": mode,
            "decision": decision,
            "reason": reason,
        }

    def test_redo_entries_accumulated(self):
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)

            fake_entries = [
                self._make_redo_entry("engineer", "IMPL", "REDO_SAME", "pytest 실패 무시"),
                self._make_redo_entry("engineer", "IMPL", "PASS", "정상"),
            ]

            with patch("harness.loop_insights.redo_log") as mock_rl, \
                 patch("harness.loop_insights.rv") as mock_rv, \
                 patch("harness.loop_insights.get_run_dir") as mock_rd:

                mock_rd.return_value = td_path
                mock_rl.read_all.return_value = fake_entries
                mock_rv.parse_steps.return_value = []
                mock_rv.detect_wastes.return_value = []
                mock_rv.detect_goods.return_value = []

                modified = append_from_run("sid1", "rid1", cwd=td_path)

            self.assertTrue(len(modified) > 0)
            content = insights_path("engineer", "IMPL", cwd=td_path).read_text()
            self.assertIn("pytest 실패 무시", content)
            self.assertIn("REDO_SAME", content)

    def test_pass_entries_skipped(self):
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)

            fake_entries = [
                self._make_redo_entry("engineer", "IMPL", "PASS", "정상 완료"),
            ]

            with patch("harness.loop_insights.redo_log") as mock_rl, \
                 patch("harness.loop_insights.rv") as mock_rv, \
                 patch("harness.loop_insights.get_run_dir") as mock_rd:

                mock_rd.return_value = td_path
                mock_rl.read_all.return_value = fake_entries
                mock_rv.parse_steps.return_value = []
                mock_rv.detect_wastes.return_value = []
                mock_rv.detect_goods.return_value = []

                modified = append_from_run("sid1", "rid1", cwd=td_path)

            self.assertEqual(modified, [])

    def test_empty_reason_skipped(self):
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)

            fake_entries = [
                self._make_redo_entry("engineer", "IMPL", "REDO_SAME", ""),
            ]

            with patch("harness.loop_insights.redo_log") as mock_rl, \
                 patch("harness.loop_insights.rv") as mock_rv, \
                 patch("harness.loop_insights.get_run_dir") as mock_rd:

                mock_rd.return_value = td_path
                mock_rl.read_all.return_value = fake_entries
                mock_rv.parse_steps.return_value = []
                mock_rv.detect_wastes.return_value = []
                mock_rv.detect_goods.return_value = []

                modified = append_from_run("sid1", "rid1", cwd=td_path)

            self.assertEqual(modified, [])

    def test_empty_log_returns_empty(self):
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)

            with patch("harness.loop_insights.redo_log") as mock_rl, \
                 patch("harness.loop_insights.rv") as mock_rv, \
                 patch("harness.loop_insights.get_run_dir") as mock_rd:

                mock_rd.return_value = td_path
                mock_rl.read_all.return_value = []
                mock_rv.parse_steps.return_value = []
                mock_rv.detect_wastes.return_value = []
                mock_rv.detect_goods.return_value = []

                modified = append_from_run("sid1", "rid1", cwd=td_path)

            self.assertEqual(modified, [])


class TestWorktreeNormalization(unittest.TestCase):
    """worktree 안 cwd → main repo root 정규화 (#306 개선점 5).

    worktree 진입 후에도 loop-insights 가 main repo root 에 저장돼야 함.
    ExitWorktree(remove) 시 누적분 손실 회피.
    """

    def test_insights_path_normalizes_worktree_to_main_root(self):
        with tempfile.TemporaryDirectory() as td:
            main_root = Path(td) / "main"
            worktree = main_root / ".claude" / "worktrees" / "wt1"
            main_root.mkdir(parents=True)
            worktree.mkdir(parents=True)

            with patch(
                "harness.loop_insights._resolve_project_root",
                return_value=main_root,
            ):
                p = insights_path("engineer", "IMPL", cwd=worktree)

            self.assertTrue(
                str(p).startswith(str(main_root.resolve()) + os.sep),
                f"insights_path={p} 가 main_root={main_root} 안이 아님",
            )
            self.assertIn(".claude/loop-insights", str(p))
            self.assertNotIn("worktrees/wt1", str(p))

    def test_append_findings_writes_to_main_root_not_worktree(self):
        """append_findings 가 worktree cwd 받아도 main repo root 에 저장."""
        with tempfile.TemporaryDirectory() as td:
            main_root = Path(td) / "main"
            worktree = main_root / ".claude" / "worktrees" / "wt1"
            main_root.mkdir(parents=True)
            worktree.mkdir(parents=True)

            with patch(
                "harness.loop_insights._resolve_project_root",
                return_value=main_root,
            ):
                append_findings(
                    "engineer", "IMPL",
                    ["worktree path leak detected"], [],
                    cwd=worktree,
                )

            worktree_path = worktree / ".claude" / "loop-insights" / "engineer-IMPL.md"
            self.assertFalse(worktree_path.exists())

            main_path = main_root / ".claude" / "loop-insights" / "engineer-IMPL.md"
            self.assertTrue(main_path.exists())
            self.assertIn("worktree path leak detected", main_path.read_text())

    def test_read_resolves_from_main_root_after_worktree_remove(self):
        """worktree 안에서 호출돼도 main_root 에서 read — ExitWorktree(remove) 후 영속성."""
        with tempfile.TemporaryDirectory() as td:
            main_root = Path(td) / "main"
            worktree = main_root / ".claude" / "worktrees" / "wt1"
            main_root.mkdir(parents=True)
            worktree.mkdir(parents=True)

            main_path = main_root / ".claude" / "loop-insights" / "architect.md"
            main_path.parent.mkdir(parents=True)
            main_path.write_text("# Loop Insights\ncontent X", encoding="utf-8")

            with patch(
                "harness.loop_insights._resolve_project_root",
                return_value=main_root,
            ):
                result = read("architect", cwd=worktree)

            self.assertIn("content X", result)


if __name__ == "__main__":
    unittest.main()
