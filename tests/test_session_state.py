"""test_session_state — 세션/run 격리 상태 API 검증.

Coverage matrix:
    valid_session_id:
        - valid (영숫자 / 하이픈 / 언더스코어 with leading alphanumeric)
        - invalid (empty / leading underscore / space / dot / non-str / 256+ chars)

    session_id_from_stdin:
        - 3 변형 (sessionId / session_id / sessionid)
        - 빈 dict / 잘못된 타입 / 잘못된 sid 형식
        - data= 전달 시 stdin read 스킵

    current_session_id (env > pointer):
        - env 있음 → env
        - env 빈 + pointer 있음 → pointer
        - 둘 다 빈 → ""
        - env 잘못된 → pointer

    read_session_pointer:
        - 정상 / 미존재 / 잘못된 sid

    write_session_pointer:
        - 작성 + 0o600 권한
        - 잘못된 sid → ValueError

    generate_run_id:
        - 형식 (run-{8 hex})
        - 충돌 없음 (1000회)

    atomic_write:
        - 파일 생성 + 권한 + 내용
        - tmp residue 없음
        - bytes 외 타입 → TypeError

    session_dir / run_dir / live_path:
        - 정상 경로
        - path traversal 차단
        - run_id 형식 검증

    read_live:
        - envelope 자기참조 일치 → 데이터 반환
        - sessionId 불일치 → 빈 dict (leftover 방어)
        - 미존재 / 잘못된 JSON → 빈 dict

    update_live:
        - _meta 항상 갱신
        - session_id 자기참조 박힘
        - 필드 None 시 삭제
        - active_runs 디폴트 빈 dict

    start_run / update_current_step / complete_run:
        - 슬롯 lifecycle
        - 중복 run_id → ValueError
        - 미활성 run_id update → ValueError
        - complete idempotent

    cleanup_stale_runs:
        - completed+ttl 초과 삭제
        - heartbeat ttl 초과 삭제
        - 신선 슬롯 보존
"""
from __future__ import annotations

import json
import os
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from harness.session_state import (
    DEFAULT_RUN_TTL_SEC,
    LIVE_JSON_VERSION,
    SESSION_ID_RE,
    atomic_write,
    cleanup_stale_runs,
    complete_run,
    current_session_id,
    generate_run_id,
    live_path,
    read_live,
    read_session_pointer,
    run_dir,
    session_dir,
    session_id_from_stdin,
    start_run,
    update_current_step,
    update_live,
    valid_session_id,
    write_session_pointer,
)


# ---------------------------------------------------------------------------
# valid_session_id
# ---------------------------------------------------------------------------


class ValidSessionIdTests(unittest.TestCase):
    def test_valid_examples(self) -> None:
        for sid in ["abc-def-123", "A1", "x", "abcDEF_123-xyz", "z" * 256]:
            self.assertTrue(valid_session_id(sid), f"should accept: {sid!r}")

    def test_invalid_examples(self) -> None:
        invalids = [
            "",
            "_starts_underscore",
            "-starts-hyphen",
            "with space",
            "with.dot",
            "../path",
            "x" * 257,
            None,
            42,
            ["list"],
        ]
        for sid in invalids:
            self.assertFalse(valid_session_id(sid), f"should reject: {sid!r}")


# ---------------------------------------------------------------------------
# session_id_from_stdin (data= 인자만 — stdin read 는 별도)
# ---------------------------------------------------------------------------


class SessionIdFromStdinTests(unittest.TestCase):
    def test_session_id_variant(self) -> None:
        self.assertEqual(
            session_id_from_stdin(data={"session_id": "abc-123"}),
            "abc-123",
        )

    def test_sessionId_variant(self) -> None:
        self.assertEqual(
            session_id_from_stdin(data={"sessionId": "abc-123"}),
            "abc-123",
        )

    def test_sessionid_variant(self) -> None:
        self.assertEqual(
            session_id_from_stdin(data={"sessionid": "abc-123"}),
            "abc-123",
        )

    def test_priority_session_id_over_sessionId(self) -> None:
        # session_id 가 첫 우선
        result = session_id_from_stdin(
            data={"session_id": "first", "sessionId": "second"}
        )
        self.assertEqual(result, "first")

    def test_invalid_sid_returns_empty(self) -> None:
        self.assertEqual(
            session_id_from_stdin(data={"session_id": "../bad"}), ""
        )

    def test_empty_dict_returns_empty(self) -> None:
        self.assertEqual(session_id_from_stdin(data={}), "")

    def test_non_dict_data_returns_empty(self) -> None:
        self.assertEqual(session_id_from_stdin(data="string"), "")
        self.assertEqual(session_id_from_stdin(data=[]), "")


# ---------------------------------------------------------------------------
# current_session_id (env > pointer)
# ---------------------------------------------------------------------------


class CurrentSessionIdTests(unittest.TestCase):
    def setUp(self) -> None:
        self._td = TemporaryDirectory()
        self.base = Path(self._td.name)

    def tearDown(self) -> None:
        self._td.cleanup()
        os.environ.pop("DCNESS_SESSION_ID", None)

    def test_env_var_takes_priority(self) -> None:
        os.environ["DCNESS_SESSION_ID"] = "env-sid"
        write_session_pointer("pointer-sid", base_dir=self.base)
        self.assertEqual(
            current_session_id(base_dir=self.base), "env-sid"
        )

    def test_pointer_used_when_env_empty(self) -> None:
        write_session_pointer("pointer-sid", base_dir=self.base)
        self.assertEqual(
            current_session_id(base_dir=self.base), "pointer-sid"
        )

    def test_returns_empty_when_both_missing(self) -> None:
        self.assertEqual(current_session_id(base_dir=self.base), "")

    def test_invalid_env_falls_to_pointer(self) -> None:
        os.environ["DCNESS_SESSION_ID"] = "../bad"
        write_session_pointer("pointer-sid", base_dir=self.base)
        self.assertEqual(
            current_session_id(base_dir=self.base), "pointer-sid"
        )


# ---------------------------------------------------------------------------
# session pointer read/write
# ---------------------------------------------------------------------------


class SessionPointerTests(unittest.TestCase):
    def setUp(self) -> None:
        self._td = TemporaryDirectory()
        self.base = Path(self._td.name)

    def tearDown(self) -> None:
        self._td.cleanup()

    def test_write_then_read(self) -> None:
        write_session_pointer("abc-sid", base_dir=self.base)
        self.assertEqual(read_session_pointer(base_dir=self.base), "abc-sid")

    def test_read_missing_returns_empty(self) -> None:
        self.assertEqual(read_session_pointer(base_dir=self.base), "")

    def test_write_invalid_raises(self) -> None:
        with self.assertRaises(ValueError):
            write_session_pointer("../bad", base_dir=self.base)

    def test_pointer_file_permissions(self) -> None:
        write_session_pointer("abc-sid", base_dir=self.base)
        path = self.base / ".session-id"
        # POSIX 만 — Windows 는 0o600 매핑이 다름
        if os.name == "posix":
            mode = path.stat().st_mode & 0o777
            self.assertEqual(mode, 0o600)


# ---------------------------------------------------------------------------
# generate_run_id
# ---------------------------------------------------------------------------


class GenerateRunIdTests(unittest.TestCase):
    def test_format(self) -> None:
        rid = generate_run_id()
        self.assertTrue(rid.startswith("run-"))
        suffix = rid[4:]
        self.assertEqual(len(suffix), 8)
        # all lowercase hex
        int(suffix, 16)  # would raise if not valid hex
        self.assertEqual(suffix, suffix.lower())

    def test_uniqueness_in_1000_calls(self) -> None:
        ids = {generate_run_id() for _ in range(1000)}
        self.assertEqual(len(ids), 1000)


# ---------------------------------------------------------------------------
# atomic_write
# ---------------------------------------------------------------------------


class AtomicWriteTests(unittest.TestCase):
    def setUp(self) -> None:
        self._td = TemporaryDirectory()
        self.base = Path(self._td.name)

    def tearDown(self) -> None:
        self._td.cleanup()

    def test_creates_file_with_content(self) -> None:
        target = self.base / "x.json"
        atomic_write(target, b'{"a": 1}')
        self.assertEqual(target.read_bytes(), b'{"a": 1}')

    def test_no_tmp_residue(self) -> None:
        target = self.base / "x.json"
        atomic_write(target, b"data")
        residue = list(self.base.glob("*.tmp.*"))
        self.assertEqual(residue, [])

    def test_overwrites_existing(self) -> None:
        target = self.base / "x.json"
        atomic_write(target, b"v1")
        atomic_write(target, b"v2")
        self.assertEqual(target.read_bytes(), b"v2")

    def test_default_permissions_0o600(self) -> None:
        if os.name != "posix":
            self.skipTest("0o600 검증은 POSIX 만")
        target = self.base / "x.json"
        atomic_write(target, b"data")
        mode = target.stat().st_mode & 0o777
        self.assertEqual(mode, 0o600)

    def test_rejects_non_bytes(self) -> None:
        target = self.base / "x.json"
        with self.assertRaises(TypeError):
            atomic_write(target, "string")  # type: ignore[arg-type]

    def test_creates_parent_dir(self) -> None:
        target = self.base / "deep" / "nested" / "x.json"
        atomic_write(target, b"data")
        self.assertTrue(target.exists())


# ---------------------------------------------------------------------------
# session_dir / run_dir / live_path
# ---------------------------------------------------------------------------


class PathHelperTests(unittest.TestCase):
    def setUp(self) -> None:
        self._td = TemporaryDirectory()
        self.base = Path(self._td.name)

    def tearDown(self) -> None:
        self._td.cleanup()

    def test_session_dir_format(self) -> None:
        path = session_dir("abc-sid", base_dir=self.base)
        self.assertEqual(path, (self.base / ".sessions" / "abc-sid").resolve())

    def test_run_dir_format(self) -> None:
        rid = "run-a3f81b29"
        path = run_dir("abc", rid, base_dir=self.base)
        self.assertEqual(
            path,
            (self.base / ".sessions" / "abc" / "runs" / rid).resolve(),
        )

    def test_run_dir_create(self) -> None:
        path = run_dir("abc", "run-12345678", base_dir=self.base, create=True)
        self.assertTrue(path.exists())

    def test_session_dir_invalid_sid_raises(self) -> None:
        with self.assertRaises(ValueError):
            session_dir("../bad", base_dir=self.base)

    def test_run_dir_invalid_run_id_raises(self) -> None:
        with self.assertRaises(ValueError):
            run_dir("abc", "not-a-run-id", base_dir=self.base)

    def test_live_path(self) -> None:
        path = live_path("abc", base_dir=self.base)
        self.assertEqual(path.name, "live.json")
        self.assertEqual(path.parent.name, "abc")


# ---------------------------------------------------------------------------
# read_live / update_live (envelope)
# ---------------------------------------------------------------------------


class LiveJsonTests(unittest.TestCase):
    def setUp(self) -> None:
        self._td = TemporaryDirectory()
        self.base = Path(self._td.name)
        self.sid = "abc-sid"

    def tearDown(self) -> None:
        self._td.cleanup()

    def test_read_missing_returns_empty(self) -> None:
        self.assertEqual(read_live(self.sid, base_dir=self.base), {})

    def test_update_then_read_roundtrip(self) -> None:
        update_live(self.sid, base_dir=self.base, custom_field="hello")
        data = read_live(self.sid, base_dir=self.base)
        self.assertEqual(data["custom_field"], "hello")
        self.assertEqual(data["_meta"]["sessionId"], self.sid)
        self.assertEqual(data["_meta"]["version"], LIVE_JSON_VERSION)
        self.assertIn("writtenAt", data["_meta"])

    def test_active_runs_default_empty_dict(self) -> None:
        update_live(self.sid, base_dir=self.base, foo="bar")
        data = read_live(self.sid, base_dir=self.base)
        self.assertEqual(data["active_runs"], {})

    def test_field_none_deletes(self) -> None:
        update_live(self.sid, base_dir=self.base, x=1, y=2)
        update_live(self.sid, base_dir=self.base, x=None)
        data = read_live(self.sid, base_dir=self.base)
        self.assertNotIn("x", data)
        self.assertEqual(data["y"], 2)

    def test_cross_session_envelope_rejected(self) -> None:
        # 다른 세션이 같은 경로에 leftover 남긴 상황 시뮬
        path = live_path(self.sid, base_dir=self.base)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps({
                "_meta": {"sessionId": "OTHER-SID", "writtenAt": "x", "version": 1},
                "session_id": "OTHER-SID",
                "active_runs": {"run-aaaaaaaa": {"foo": 1}},
            }),
            encoding="utf-8",
        )
        # read_live 가 다른 sid 의 데이터 거부
        self.assertEqual(read_live(self.sid, base_dir=self.base), {})

    def test_invalid_json_returns_empty(self) -> None:
        path = live_path(self.sid, base_dir=self.base)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("not valid json", encoding="utf-8")
        self.assertEqual(read_live(self.sid, base_dir=self.base), {})

    def test_session_id_self_reference(self) -> None:
        update_live(self.sid, base_dir=self.base, x=1)
        data = read_live(self.sid, base_dir=self.base)
        self.assertEqual(data["session_id"], self.sid)


# ---------------------------------------------------------------------------
# active_runs operations
# ---------------------------------------------------------------------------


class ActiveRunsTests(unittest.TestCase):
    def setUp(self) -> None:
        self._td = TemporaryDirectory()
        self.base = Path(self._td.name)
        self.sid = "abc-sid"
        self.run_id = "run-12345678"

    def tearDown(self) -> None:
        self._td.cleanup()

    def test_start_run_adds_slot(self) -> None:
        start_run(
            self.sid, self.run_id, "quick",
            base_dir=self.base, issue_num=42,
        )
        data = read_live(self.sid, base_dir=self.base)
        slot = data["active_runs"][self.run_id]
        self.assertEqual(slot["run_id"], self.run_id)
        self.assertEqual(slot["entry_point"], "quick")
        self.assertEqual(slot["issue_num"], 42)
        self.assertIsNone(slot["completed_at"])
        self.assertIsNone(slot["current_step"])
        self.assertIn("started_at", slot)
        self.assertIn("last_confirmed_at", slot)
        self.assertIn("run_dir", slot)

    def test_start_run_creates_dir(self) -> None:
        start_run(self.sid, self.run_id, "quick", base_dir=self.base)
        rd = run_dir(self.sid, self.run_id, base_dir=self.base)
        self.assertTrue(rd.exists())

    def test_start_run_duplicate_raises(self) -> None:
        start_run(self.sid, self.run_id, "quick", base_dir=self.base)
        with self.assertRaises(ValueError):
            start_run(self.sid, self.run_id, "quick", base_dir=self.base)

    def test_update_current_step(self) -> None:
        start_run(self.sid, self.run_id, "quick", base_dir=self.base)
        update_current_step(
            self.sid, self.run_id, "engineer", "IMPL",
            base_dir=self.base,
        )
        slot = read_live(self.sid, base_dir=self.base)["active_runs"][self.run_id]
        self.assertEqual(slot["current_step"]["agent"], "engineer")
        self.assertEqual(slot["current_step"]["mode"], "IMPL")

    def test_update_step_unknown_run_raises(self) -> None:
        with self.assertRaises(ValueError):
            update_current_step(
                self.sid, self.run_id, "engineer", "IMPL",
                base_dir=self.base,
            )

    def test_complete_run(self) -> None:
        start_run(self.sid, self.run_id, "quick", base_dir=self.base)
        complete_run(self.sid, self.run_id, base_dir=self.base)
        slot = read_live(self.sid, base_dir=self.base)["active_runs"][self.run_id]
        self.assertIsNotNone(slot["completed_at"])
        self.assertIsNone(slot["current_step"])

    def test_complete_run_idempotent_on_missing(self) -> None:
        # raise 안 함 — noop
        complete_run(self.sid, self.run_id, base_dir=self.base)

    def test_multiple_active_runs(self) -> None:
        # 동시 다중 run 지원 검증 (OMC 차용 핵심)
        start_run(self.sid, "run-aaaaaaaa", "quick", base_dir=self.base)
        start_run(self.sid, "run-bbbbbbbb", "product-plan", base_dir=self.base)
        data = read_live(self.sid, base_dir=self.base)
        self.assertEqual(len(data["active_runs"]), 2)


# ---------------------------------------------------------------------------
# cleanup_stale_runs
# ---------------------------------------------------------------------------


class CleanupStaleRunsTests(unittest.TestCase):
    def setUp(self) -> None:
        self._td = TemporaryDirectory()
        self.base = Path(self._td.name)
        self.sid = "abc-sid"

    def tearDown(self) -> None:
        self._td.cleanup()

    def _set_slot(self, run_id: str, **overrides) -> None:
        live = read_live(self.sid, base_dir=self.base) or {}
        active = live.get("active_runs", {}) or {}
        active[run_id] = {
            "run_id": run_id,
            "entry_point": "quick",
            "started_at": "2026-04-29T00:00:00+00:00",
            "last_confirmed_at": "2026-04-29T00:00:00+00:00",
            "completed_at": None,
            "run_dir": "x",
            "current_step": None,
            "issue_num": None,
        }
        active[run_id].update(overrides)
        update_live(self.sid, base_dir=self.base, active_runs=active)

    def test_removes_completed_old_slot(self) -> None:
        # 25h 전 완료된 슬롯
        old = (datetime.now(timezone.utc) - timedelta(hours=25)).isoformat(timespec="seconds")
        self._set_slot("run-aaaaaaaa", completed_at=old, last_confirmed_at=old)
        self._set_slot("run-bbbbbbbb")  # 신선
        removed = cleanup_stale_runs(self.sid, base_dir=self.base)
        self.assertEqual(removed, 1)
        active = read_live(self.sid, base_dir=self.base)["active_runs"]
        self.assertNotIn("run-aaaaaaaa", active)
        self.assertIn("run-bbbbbbbb", active)

    def test_removes_heartbeat_dead_slot(self) -> None:
        # 25h heartbeat 안 갱신된 슬롯 (completed 아닌데 stale)
        old = (datetime.now(timezone.utc) - timedelta(hours=25)).isoformat(timespec="seconds")
        self._set_slot("run-cccccccc", last_confirmed_at=old)
        removed = cleanup_stale_runs(self.sid, base_dir=self.base)
        self.assertEqual(removed, 1)

    def test_keeps_fresh_slot(self) -> None:
        self._set_slot("run-dddddddd")
        removed = cleanup_stale_runs(self.sid, base_dir=self.base)
        self.assertEqual(removed, 0)
        active = read_live(self.sid, base_dir=self.base)["active_runs"]
        self.assertIn("run-dddddddd", active)


if __name__ == "__main__":
    unittest.main()
