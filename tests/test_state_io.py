"""test_state_io.py — harness/state_io 모듈 검증.

검증 범위:
- R8 (status-json-mutate-pattern §8): 5 failure modes 단일 normalize
- 화이트리스트 + path traversal (R1 layer 1)
- atomic write (write_status 가 부분 작성 노출 안 함)
- clear_run_state 의 path 안전성

실행:
    python3 -m unittest tests.test_state_io -v
    python3 tests/test_state_io.py            # 직접 실행도 OK
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path

# repo root 를 sys.path 에 추가 (tests/ 는 자동 포함 안 됨)
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from harness.state_io import (  # noqa: E402
    MissingStatus,
    clear_run_state,
    read_status,
    state_path,
    write_status,
)


class _Base(unittest.TestCase):
    """공통 fixture — 임시 base_dir 에서 실행."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)
        self.run_id = "run_test_001"
        self.agent = "validator"
        self.mode = "PLAN_VALIDATION"

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _force_old_mtime(self, path: Path) -> None:
        """race window 밖으로 mtime 강제 (empty vs race 분리 검증용)."""
        old = time.time() - 5.0
        os.utime(path, (old, old))


# ═════════════════════════════════════════════════════════════════════════
# Round trip + atomic write
# ═════════════════════════════════════════════════════════════════════════

class TestRoundTrip(_Base):
    def test_write_then_read_returns_payload(self) -> None:
        payload = {
            "status": "PASS",
            "fail_items": [],
            "non_obvious_patterns": ["validator 가 spec gap 발견"],
        }
        path = write_status(
            self.agent, self.run_id, payload,
            mode=self.mode, base_dir=self.base,
        )
        self.assertTrue(path.exists())

        data = read_status(
            self.agent, self.run_id,
            mode=self.mode, base_dir=self.base,
        )
        self.assertEqual(data["status"], "PASS")
        self.assertEqual(
            data["non_obvious_patterns"],
            ["validator 가 spec gap 발견"],
        )

    def test_write_without_mode(self) -> None:
        path = write_status(
            "architect", self.run_id, {"status": "READY"},
            base_dir=self.base,
        )
        self.assertTrue(path.name.endswith("architect.json"))
        data = read_status("architect", self.run_id, base_dir=self.base)
        self.assertEqual(data["status"], "READY")

    def test_overwrite_replaces_payload(self) -> None:
        write_status(
            self.agent, self.run_id, {"status": "FAIL"},
            mode=self.mode, base_dir=self.base,
        )
        write_status(
            self.agent, self.run_id, {"status": "PASS", "note": "재검증 통과"},
            mode=self.mode, base_dir=self.base,
        )
        data = read_status(
            self.agent, self.run_id,
            mode=self.mode, base_dir=self.base,
        )
        self.assertEqual(data["status"], "PASS")
        self.assertEqual(data["note"], "재검증 통과")

    def test_atomic_write_no_tmp_residue(self) -> None:
        write_status(
            self.agent, self.run_id, {"status": "PASS"},
            mode=self.mode, base_dir=self.base,
        )
        run_dir = self.base / self.run_id
        tmp_files = list(run_dir.glob("*.tmp"))
        self.assertEqual(tmp_files, [], "tmp 파일이 남으면 atomic 실패")

    def test_unicode_payload(self) -> None:
        write_status(
            self.agent, self.run_id,
            {"status": "PASS", "msg": "한글 + 이모지 ✓"},
            mode=self.mode, base_dir=self.base,
        )
        data = read_status(
            self.agent, self.run_id,
            mode=self.mode, base_dir=self.base,
        )
        self.assertEqual(data["msg"], "한글 + 이모지 ✓")


# ═════════════════════════════════════════════════════════════════════════
# R8: 5 failure modes 단일 normalize
# ═════════════════════════════════════════════════════════════════════════

class TestFailureNotFound(_Base):
    def test_not_found(self) -> None:
        with self.assertRaises(MissingStatus) as ctx:
            read_status(
                self.agent, self.run_id,
                mode=self.mode, base_dir=self.base,
            )
        self.assertEqual(ctx.exception.reason, "not_found")
        self.assertIn(self.agent, ctx.exception.detail)


class TestFailureEmpty(_Base):
    def test_empty_with_old_mtime(self) -> None:
        path = state_path(self.agent, self.run_id, self.mode, self.base)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("")
        self._force_old_mtime(path)

        with self.assertRaises(MissingStatus) as ctx:
            read_status(
                self.agent, self.run_id,
                mode=self.mode, base_dir=self.base,
            )
        self.assertEqual(ctx.exception.reason, "empty")

    def test_whitespace_only_treated_as_empty(self) -> None:
        path = state_path(self.agent, self.run_id, self.mode, self.base)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("   \n\t  \n")
        self._force_old_mtime(path)

        with self.assertRaises(MissingStatus) as ctx:
            read_status(
                self.agent, self.run_id,
                mode=self.mode, base_dir=self.base,
            )
        self.assertEqual(ctx.exception.reason, "empty")


class TestFailureRace(_Base):
    def test_empty_with_recent_mtime_is_race(self) -> None:
        path = state_path(self.agent, self.run_id, self.mode, self.base)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("")
        # mtime = now (default) → race window 안

        with self.assertRaises(MissingStatus) as ctx:
            read_status(
                self.agent, self.run_id,
                mode=self.mode, base_dir=self.base,
            )
        self.assertEqual(ctx.exception.reason, "race")


class TestFailureMalformedJson(_Base):
    def test_malformed_json(self) -> None:
        path = state_path(self.agent, self.run_id, self.mode, self.base)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{not: valid, json")

        with self.assertRaises(MissingStatus) as ctx:
            read_status(
                self.agent, self.run_id,
                mode=self.mode, base_dir=self.base,
            )
        self.assertEqual(ctx.exception.reason, "malformed_json")

    def test_partial_json_truncated_during_write(self) -> None:
        path = state_path(self.agent, self.run_id, self.mode, self.base)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('{"status": "PA')  # truncated

        with self.assertRaises(MissingStatus) as ctx:
            read_status(
                self.agent, self.run_id,
                mode=self.mode, base_dir=self.base,
            )
        self.assertEqual(ctx.exception.reason, "malformed_json")


class TestFailureSchemaViolation(_Base):
    def test_missing_status_key(self) -> None:
        path = state_path(self.agent, self.run_id, self.mode, self.base)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"fail_items": ["x"]}))

        with self.assertRaises(MissingStatus) as ctx:
            read_status(
                self.agent, self.run_id,
                mode=self.mode, base_dir=self.base,
            )
        self.assertEqual(ctx.exception.reason, "schema_violation")
        self.assertIn("status", ctx.exception.detail)

    def test_status_not_string(self) -> None:
        path = state_path(self.agent, self.run_id, self.mode, self.base)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"status": 42}))

        with self.assertRaises(MissingStatus) as ctx:
            read_status(
                self.agent, self.run_id,
                mode=self.mode, base_dir=self.base,
            )
        self.assertEqual(ctx.exception.reason, "schema_violation")

    def test_root_not_object(self) -> None:
        path = state_path(self.agent, self.run_id, self.mode, self.base)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(["status", "PASS"]))

        with self.assertRaises(MissingStatus) as ctx:
            read_status(
                self.agent, self.run_id,
                mode=self.mode, base_dir=self.base,
            )
        self.assertEqual(ctx.exception.reason, "schema_violation")

    def test_status_outside_allowed_set(self) -> None:
        write_status(
            self.agent, self.run_id, {"status": "WEIRD"},
            mode=self.mode, base_dir=self.base,
        )
        with self.assertRaises(MissingStatus) as ctx:
            read_status(
                self.agent, self.run_id,
                mode=self.mode, base_dir=self.base,
                allowed_status={"PASS", "FAIL"},
            )
        self.assertEqual(ctx.exception.reason, "schema_violation")
        self.assertIn("WEIRD", ctx.exception.detail)

    def test_allowed_status_passthrough(self) -> None:
        write_status(
            self.agent, self.run_id, {"status": "PASS"},
            mode=self.mode, base_dir=self.base,
        )
        data = read_status(
            self.agent, self.run_id,
            mode=self.mode, base_dir=self.base,
            allowed_status={"PASS", "FAIL"},
        )
        self.assertEqual(data["status"], "PASS")


class TestMissingStatusContract(unittest.TestCase):
    """MissingStatus 계약 — 다른 exception 누수 0."""

    def test_only_known_reasons(self) -> None:
        with self.assertRaises(ValueError):
            MissingStatus("UNEXPECTED", "x")

    def test_reasons_constant(self) -> None:
        self.assertEqual(
            set(MissingStatus.REASONS),
            {"not_found", "empty", "race", "malformed_json", "schema_violation"},
        )

    def test_message_includes_reason_and_detail(self) -> None:
        e = MissingStatus("not_found", "/tmp/foo.json")
        self.assertEqual(e.reason, "not_found")
        self.assertIn("not_found", str(e))
        self.assertIn("/tmp/foo.json", str(e))


# ═════════════════════════════════════════════════════════════════════════
# 화이트리스트 + path traversal (R1 layer 1)
# ═════════════════════════════════════════════════════════════════════════

class TestPathSafety(_Base):
    def test_invalid_agent_traversal(self) -> None:
        with self.assertRaises(ValueError):
            write_status(
                "../etc", self.run_id, {"status": "PASS"},
                base_dir=self.base,
            )

    def test_invalid_agent_uppercase(self) -> None:
        with self.assertRaises(ValueError):
            write_status(
                "Validator", self.run_id, {"status": "PASS"},
                base_dir=self.base,
            )

    def test_invalid_mode_lowercase(self) -> None:
        with self.assertRaises(ValueError):
            write_status(
                self.agent, self.run_id, {"status": "PASS"},
                mode="lower-case", base_dir=self.base,
            )

    def test_run_id_dotdot_rejected(self) -> None:
        with self.assertRaises(ValueError):
            write_status(
                self.agent, "..", {"status": "PASS"},
                base_dir=self.base,
            )

    def test_run_id_slash_rejected(self) -> None:
        with self.assertRaises(ValueError):
            write_status(
                self.agent, "a/b", {"status": "PASS"},
                base_dir=self.base,
            )

    def test_payload_must_be_dict(self) -> None:
        with self.assertRaises(TypeError):
            write_status(
                self.agent, self.run_id, ["PASS"],  # type: ignore[arg-type]
                base_dir=self.base,
            )

    def test_payload_must_have_status(self) -> None:
        with self.assertRaises(ValueError):
            write_status(
                self.agent, self.run_id, {"foo": "bar"},
                base_dir=self.base,
            )

    def test_payload_status_must_be_string(self) -> None:
        with self.assertRaises(ValueError):
            write_status(
                self.agent, self.run_id, {"status": 1},
                base_dir=self.base,
            )

    def test_state_path_is_under_base(self) -> None:
        p = state_path(self.agent, self.run_id, self.mode, self.base)
        # base 의 resolve 와 비교 (TemporaryDirectory 가 symlink 일 수 있음)
        self.assertTrue(str(p).startswith(str(self.base.resolve())))


# ═════════════════════════════════════════════════════════════════════════
# clear_run_state
# ═════════════════════════════════════════════════════════════════════════

class TestClearRunState(_Base):
    def test_clear_removes_all_status_jsons(self) -> None:
        write_status(
            self.agent, self.run_id, {"status": "PASS"},
            mode="PLAN_VALIDATION", base_dir=self.base,
        )
        write_status(
            self.agent, self.run_id, {"status": "FAIL"},
            mode="CODE_VALIDATION", base_dir=self.base,
        )
        n = clear_run_state(self.run_id, base_dir=self.base)
        self.assertEqual(n, 2)

        with self.assertRaises(MissingStatus):
            read_status(
                self.agent, self.run_id,
                mode="PLAN_VALIDATION", base_dir=self.base,
            )

    def test_clear_missing_run_returns_zero(self) -> None:
        n = clear_run_state("nonexistent_run_xyz", base_dir=self.base)
        self.assertEqual(n, 0)

    def test_clear_path_traversal_rejected(self) -> None:
        with self.assertRaises(ValueError):
            clear_run_state("..", base_dir=self.base)

    def test_clear_preserves_non_json_files(self) -> None:
        # status JSON 외 파일은 보존
        write_status(
            self.agent, self.run_id, {"status": "PASS"},
            mode="PLAN_VALIDATION", base_dir=self.base,
        )
        run_dir = self.base / self.run_id
        sentinel = run_dir / "preserve.txt"
        sentinel.write_text("non-json artifact")

        clear_run_state(self.run_id, base_dir=self.base)
        self.assertTrue(sentinel.exists(), "비-JSON 파일은 보존돼야 함")


if __name__ == "__main__":
    unittest.main(verbosity=2)
