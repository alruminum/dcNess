"""test_agent_trace — DCN-CHG-20260501-11.

agent-trace.jsonl append/read/tail. redo_log 와 동일 패턴 — Pre/PostToolUse hook
가 sub 행동 사후 추적용으로 append.
"""
from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from harness.agent_trace import TRACE_NAME, append, histogram, last_agent_id, read_all, tail
from harness.session_state import generate_run_id, run_dir


SID = "test-trace-sid"


class AgentTraceAppendTests(unittest.TestCase):
    def test_roundtrip_basic(self):
        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            rid = generate_run_id()
            append(
                SID, rid,
                {"phase": "pre", "agent": "engineer", "tool": "Edit", "input": "src/foo.py"},
                base_dir=base,
            )
            entries = read_all(SID, rid, base_dir=base)
            self.assertEqual(len(entries), 1)
            self.assertEqual(entries[0]["phase"], "pre")
            self.assertEqual(entries[0]["agent"], "engineer")
            self.assertIn("ts", entries[0])

    def test_ts_auto_added(self):
        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            rid = generate_run_id()
            append(SID, rid, {"phase": "pre"}, base_dir=base)
            entries = read_all(SID, rid, base_dir=base)
            self.assertTrue(entries[0]["ts"].endswith("Z"))

    def test_pre_post_order_preserved(self):
        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            rid = generate_run_id()
            append(SID, rid, {"phase": "pre", "tool": "Bash"}, base_dir=base)
            append(SID, rid, {"phase": "post", "tool": "Bash", "exit": 0}, base_dir=base)
            entries = read_all(SID, rid, base_dir=base)
            self.assertEqual(entries[0]["phase"], "pre")
            self.assertEqual(entries[1]["phase"], "post")
            self.assertEqual(entries[1]["exit"], 0)

    def test_entry_not_dict_raises(self):
        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            rid = generate_run_id()
            with self.assertRaises(TypeError):
                append(SID, rid, "x", base_dir=base)  # type: ignore[arg-type]

    def test_file_permission_0o600(self):
        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            rid = generate_run_id()
            append(SID, rid, {"phase": "pre"}, base_dir=base)
            target = run_dir(SID, rid, base_dir=base) / TRACE_NAME
            mode = target.stat().st_mode & 0o777
            self.assertEqual(mode, 0o600)


class AgentTraceReadAllTests(unittest.TestCase):
    def test_nonexistent_returns_empty(self):
        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            rid = generate_run_id()
            self.assertEqual(read_all(SID, rid, base_dir=base), [])

    def test_malformed_skipped(self):
        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            rid = generate_run_id()
            target = run_dir(SID, rid, base_dir=base, create=True) / TRACE_NAME
            target.write_text(
                json.dumps({"phase": "pre"}) + "\n"
                + "garbage\n"
                + json.dumps({"phase": "post"}) + "\n"
            )
            entries = read_all(SID, rid, base_dir=base)
            self.assertEqual([e["phase"] for e in entries], ["pre", "post"])


class AgentTraceTailTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.base = Path(self.tmp.name)
        self.rid = generate_run_id()
        for i in range(4):
            append(SID, self.rid, {"phase": "pre", "i": i}, base_dir=self.base)

    def tearDown(self):
        self.tmp.cleanup()

    def test_tail_n_zero(self):
        self.assertEqual(tail(SID, self.rid, 0, base_dir=self.base), [])

    def test_tail_n_smaller(self):
        result = tail(SID, self.rid, 2, base_dir=self.base)
        self.assertEqual([e["i"] for e in result], [2, 3])

    def test_tail_n_larger(self):
        result = tail(SID, self.rid, 100, base_dir=self.base)
        self.assertEqual(len(result), 4)


class HistogramTests(unittest.TestCase):
    def test_empty_run(self):
        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            rid = generate_run_id()
            self.assertEqual(histogram(SID, rid, base_dir=base), {})

    def test_pre_only_counted(self):
        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            rid = generate_run_id()
            # 같은 도구 호출은 pre + post 짝 — 1회로 셈
            append(SID, rid, {"phase": "pre", "tool": "Read", "agent_id": "a"}, base_dir=base)
            append(SID, rid, {"phase": "post", "tool": "Read", "agent_id": "a"}, base_dir=base)
            append(SID, rid, {"phase": "pre", "tool": "Bash", "agent_id": "a"}, base_dir=base)
            append(SID, rid, {"phase": "post", "tool": "Bash", "agent_id": "a"}, base_dir=base)
            hist = histogram(SID, rid, base_dir=base)
            self.assertEqual(hist, {"Read": 1, "Bash": 1})

    def test_filter_by_agent_id(self):
        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            rid = generate_run_id()
            append(SID, rid, {"phase": "pre", "tool": "Read", "agent_id": "a"}, base_dir=base)
            append(SID, rid, {"phase": "pre", "tool": "Read", "agent_id": "a"}, base_dir=base)
            append(SID, rid, {"phase": "pre", "tool": "Bash", "agent_id": "b"}, base_dir=base)
            self.assertEqual(histogram(SID, rid, agent_id="a", base_dir=base), {"Read": 2})
            self.assertEqual(histogram(SID, rid, agent_id="b", base_dir=base), {"Bash": 1})
            self.assertEqual(histogram(SID, rid, base_dir=base), {"Read": 2, "Bash": 1})


class LastAgentIdTests(unittest.TestCase):
    def test_empty_returns_blank(self):
        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            rid = generate_run_id()
            self.assertEqual(last_agent_id(SID, rid, base_dir=base), "")

    def test_returns_last_non_empty(self):
        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            rid = generate_run_id()
            append(SID, rid, {"phase": "pre", "agent_id": "first"}, base_dir=base)
            append(SID, rid, {"phase": "post", "agent_id": "first"}, base_dir=base)
            append(SID, rid, {"phase": "pre", "agent_id": "last"}, base_dir=base)
            self.assertEqual(last_agent_id(SID, rid, base_dir=base), "last")

    def test_skips_empty_agent_id(self):
        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            rid = generate_run_id()
            append(SID, rid, {"phase": "pre", "agent_id": "real"}, base_dir=base)
            append(SID, rid, {"phase": "post", "agent_id": ""}, base_dir=base)
            self.assertEqual(last_agent_id(SID, rid, base_dir=base), "real")


if __name__ == "__main__":
    unittest.main()
