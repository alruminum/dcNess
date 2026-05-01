"""test_redo_log — DCN-CHG-20260501-11.

Coverage matrix:
    append:
        - 기본 roundtrip (write → read_all 일치)
        - ts 자동 추가
        - ts 명시 시 보존
        - entry 가 dict 아님 → TypeError
        - 다중 append 라인 순서 보존
        - 파일 권한 0o600

    read_all:
        - 비존재 파일 → []
        - 빈 파일 → []
        - 빈 라인 skip
        - malformed line skip
        - 정상 라인만 추출

    tail:
        - n=0 → []
        - n>len → 전체
        - n<len → 마지막 n
        - n 음수 → []
"""
from __future__ import annotations

import json
import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from harness.redo_log import REDO_LOG_NAME, append, read_all, tail
from harness.session_state import generate_run_id, run_dir


SID = "test-redo-log-sid"


class RedoLogAppendTests(unittest.TestCase):
    def test_roundtrip_basic(self):
        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            rid = generate_run_id()
            entry = {"sub": "engineer", "decision": "PASS"}
            append(SID, rid, entry, base_dir=base)
            entries = read_all(SID, rid, base_dir=base)
            self.assertEqual(len(entries), 1)
            self.assertEqual(entries[0]["sub"], "engineer")
            self.assertEqual(entries[0]["decision"], "PASS")
            self.assertIn("ts", entries[0])

    def test_ts_auto_added(self):
        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            rid = generate_run_id()
            append(SID, rid, {"foo": "bar"}, base_dir=base)
            entries = read_all(SID, rid, base_dir=base)
            self.assertIn("ts", entries[0])
            self.assertTrue(entries[0]["ts"].endswith("Z"))

    def test_ts_preserved_when_specified(self):
        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            rid = generate_run_id()
            append(SID, rid, {"ts": "2020-01-01T00:00:00Z", "x": 1}, base_dir=base)
            entries = read_all(SID, rid, base_dir=base)
            self.assertEqual(entries[0]["ts"], "2020-01-01T00:00:00Z")

    def test_entry_not_dict_raises(self):
        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            rid = generate_run_id()
            with self.assertRaises(TypeError):
                append(SID, rid, "not a dict", base_dir=base)  # type: ignore[arg-type]
            with self.assertRaises(TypeError):
                append(SID, rid, ["list"], base_dir=base)  # type: ignore[arg-type]

    def test_multiple_appends_preserve_order(self):
        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            rid = generate_run_id()
            for i in range(5):
                append(SID, rid, {"i": i}, base_dir=base)
            entries = read_all(SID, rid, base_dir=base)
            self.assertEqual([e["i"] for e in entries], [0, 1, 2, 3, 4])

    def test_file_permission_0o600(self):
        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            rid = generate_run_id()
            append(SID, rid, {"x": 1}, base_dir=base)
            target = run_dir(SID, rid, base_dir=base) / REDO_LOG_NAME
            mode = target.stat().st_mode & 0o777
            self.assertEqual(mode, 0o600)


class RedoLogReadAllTests(unittest.TestCase):
    def test_nonexistent_returns_empty(self):
        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            rid = generate_run_id()
            self.assertEqual(read_all(SID, rid, base_dir=base), [])

    def test_empty_file_returns_empty(self):
        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            rid = generate_run_id()
            target = run_dir(SID, rid, base_dir=base, create=True) / REDO_LOG_NAME
            target.touch()
            self.assertEqual(read_all(SID, rid, base_dir=base), [])

    def test_blank_lines_skipped(self):
        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            rid = generate_run_id()
            target = run_dir(SID, rid, base_dir=base, create=True) / REDO_LOG_NAME
            target.write_text(
                json.dumps({"a": 1}) + "\n\n" + json.dumps({"a": 2}) + "\n"
            )
            entries = read_all(SID, rid, base_dir=base)
            self.assertEqual(len(entries), 2)

    def test_malformed_line_skipped(self):
        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            rid = generate_run_id()
            target = run_dir(SID, rid, base_dir=base, create=True) / REDO_LOG_NAME
            target.write_text(
                json.dumps({"a": 1}) + "\n"
                + "not json line\n"
                + json.dumps({"a": 2}) + "\n"
            )
            entries = read_all(SID, rid, base_dir=base)
            self.assertEqual([e["a"] for e in entries], [1, 2])


class RedoLogTailTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.base = Path(self.tmp.name)
        self.rid = generate_run_id()
        for i in range(5):
            append(SID, self.rid, {"i": i}, base_dir=self.base)

    def tearDown(self):
        self.tmp.cleanup()

    def test_tail_n_zero(self):
        self.assertEqual(tail(SID, self.rid, 0, base_dir=self.base), [])

    def test_tail_n_negative(self):
        self.assertEqual(tail(SID, self.rid, -1, base_dir=self.base), [])

    def test_tail_n_smaller_than_len(self):
        result = tail(SID, self.rid, 2, base_dir=self.base)
        self.assertEqual([e["i"] for e in result], [3, 4])

    def test_tail_n_equal_to_len(self):
        result = tail(SID, self.rid, 5, base_dir=self.base)
        self.assertEqual([e["i"] for e in result], [0, 1, 2, 3, 4])

    def test_tail_n_larger_than_len(self):
        result = tail(SID, self.rid, 100, base_dir=self.base)
        self.assertEqual([e["i"] for e in result], [0, 1, 2, 3, 4])


if __name__ == "__main__":
    unittest.main()
