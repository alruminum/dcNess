"""test_signal_io — prose-only pattern foundation 검증.

Coverage matrix:
    write_prose       : happy / atomic / unicode / mode 분기 / type error
    read_prose        : happy / not_found / empty
    signal_path       : path traversal / agent/mode 화이트리스트
    interpret_signal  : 휴리스틱 (1 hit / 0 hit / 다중 hit / tie ambiguous)
                        + interpreter 주입 (DI 검증, allowed 외 값 거부)
    clear_run_state   : 다중 파일 제거 / run_id 화이트리스트 / 미존재 디렉토리
    MissingSignal     : reason enum 강제

대 원칙 정합:
    - 형식 강제 0: schema/required 키 검증 안 함 (prose 자유)
    - 작업 순서 / 접근 영역만: path 화이트리스트 + traversal 차단 (catastrophic-prevention)
"""
from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from harness.signal_io import (
    MissingSignal,
    clear_run_state,
    interpret_signal,
    read_prose,
    signal_path,
    write_prose,
)


class WriteReadProseTests(unittest.TestCase):
    def setUp(self) -> None:
        self._td = TemporaryDirectory()
        self.base = Path(self._td.name)

    def tearDown(self) -> None:
        self._td.cleanup()

    def test_write_then_read_round_trip(self) -> None:
        prose = "## 검증 결과\n\n전체 통과.\n\n## 결론\n\nPASS\n"
        path = write_prose(
            "validator", "run_001", prose, mode="CODE_VALIDATION", base_dir=self.base
        )
        self.assertTrue(path.exists())
        self.assertEqual(path.suffix, ".md")
        self.assertIn("validator-CODE_VALIDATION.md", path.name)

        result = read_prose(
            "validator", "run_001", mode="CODE_VALIDATION", base_dir=self.base
        )
        self.assertEqual(result, prose)

    def test_write_creates_parent_dir(self) -> None:
        write_prose(
            "architect", "deep-run", "stub", mode=None, base_dir=self.base
        )
        self.assertTrue((self.base / "deep-run" / "architect.md").exists())

    def test_write_unicode(self) -> None:
        prose = "한글 결론\n\nPLAN_VALIDATION_PASS\n"
        write_prose(
            "validator", "r", prose, mode="PLAN_VALIDATION", base_dir=self.base
        )
        out = read_prose(
            "validator", "r", mode="PLAN_VALIDATION", base_dir=self.base
        )
        self.assertEqual(out, prose)

    def test_write_rejects_non_string(self) -> None:
        with self.assertRaises(TypeError):
            write_prose("validator", "r", 123, base_dir=self.base)  # type: ignore[arg-type]

    def test_read_not_found(self) -> None:
        with self.assertRaises(MissingSignal) as cm:
            read_prose("validator", "missing", base_dir=self.base)
        self.assertEqual(cm.exception.reason, "not_found")

    def test_read_empty_file(self) -> None:
        path = write_prose(
            "validator", "r", "    \n\t\n", base_dir=self.base
        )
        with self.assertRaises(MissingSignal) as cm:
            read_prose("validator", "r", base_dir=self.base)
        self.assertEqual(cm.exception.reason, "empty")
        self.assertIn(str(path), cm.exception.detail)

    def test_atomic_write_no_tmp_residue(self) -> None:
        write_prose("validator", "r", "x", base_dir=self.base)
        # tmp 잔여물 없어야 함
        residue = list((self.base / "r").glob("*.tmp"))
        self.assertEqual(residue, [])

    def test_overwrite(self) -> None:
        write_prose("validator", "r", "first", base_dir=self.base)
        write_prose("validator", "r", "second", base_dir=self.base)
        out = read_prose("validator", "r", base_dir=self.base)
        self.assertEqual(out, "second")


class SignalPathValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self._td = TemporaryDirectory()
        self.base = Path(self._td.name)

    def tearDown(self) -> None:
        self._td.cleanup()

    def test_invalid_agent_name(self) -> None:
        for bad in ["Validator", "vali_dator", "../etc", "", "1abc"]:
            with self.assertRaises(ValueError, msg=f"agent={bad!r}"):
                signal_path(bad, "run", base_dir=self.base)

    def test_invalid_mode_name(self) -> None:
        for bad in ["plan", "Plan", "PLAN-A", "1MODE"]:
            with self.assertRaises(ValueError, msg=f"mode={bad!r}"):
                signal_path("validator", "run", mode=bad, base_dir=self.base)

    def test_invalid_run_id_traversal(self) -> None:
        with self.assertRaises(ValueError):
            signal_path("validator", "../escape", base_dir=self.base)

    def test_invalid_run_id_slash(self) -> None:
        with self.assertRaises(ValueError):
            signal_path("validator", "a/b", base_dir=self.base)

    def test_path_format(self) -> None:
        path = signal_path("validator", "r1", mode="CODE_VALIDATION", base_dir=self.base)
        self.assertEqual(path.name, "validator-CODE_VALIDATION.md")

    def test_no_mode_path(self) -> None:
        path = signal_path("architect", "r1", base_dir=self.base)
        self.assertEqual(path.name, "architect.md")


class InterpretSignalTests(unittest.TestCase):
    def test_single_enum_in_tail_returns_it(self) -> None:
        prose = "여러 항목 검토 완료.\n\n## 결론\n\nPASS\n"
        self.assertEqual(
            interpret_signal(prose, ["PASS", "FAIL", "SPEC_MISSING"]), "PASS"
        )

    def test_last_enum_wins_when_multiple(self) -> None:
        # 본문에 PASS 언급이 있어도 마지막 단락의 FAIL 채택
        prose = (
            "초기 분석에서는 PASS 가능해 보였으나 추가 검증 후…\n"
            "최종적으로 회귀 발견.\n\n## 결론\n\nFAIL\n"
        )
        self.assertEqual(
            interpret_signal(prose, ["PASS", "FAIL"]), "FAIL"
        )

    def test_no_enum_raises_ambiguous(self) -> None:
        prose = "결론 모호한 prose 입니다.\n"
        with self.assertRaises(MissingSignal) as cm:
            interpret_signal(prose, ["PASS", "FAIL"])
        self.assertEqual(cm.exception.reason, "ambiguous")

    def test_tie_at_same_position_raises_ambiguous(self) -> None:
        # 동일 위치에서 매칭되는 enum 이 2개일 수 있는 인공 케이스
        # — 휴리스틱은 단어 경계 기반이므로 정상적으로는 occur 거의 없음.
        # 테스트는 interpreter DI 로 강제 시뮬레이션.
        def fake(prose: str, allowed: list[str]) -> str:
            raise MissingSignal("ambiguous", "tie")

        with self.assertRaises(MissingSignal):
            interpret_signal("...", ["PASS", "FAIL"], interpreter=fake)

    def test_interpreter_di_used(self) -> None:
        called = {}

        def custom(prose: str, allowed: list[str]) -> str:
            called["prose"] = prose
            called["allowed"] = list(allowed)
            return "FAIL"

        result = interpret_signal(
            "anything", ["PASS", "FAIL"], interpreter=custom
        )
        self.assertEqual(result, "FAIL")
        self.assertEqual(called["allowed"], ["PASS", "FAIL"])

    def test_interpreter_returning_invalid_value_raises(self) -> None:
        def bad(prose: str, allowed: list[str]) -> str:
            return "MAYBE"

        with self.assertRaises(ValueError):
            interpret_signal("x", ["PASS", "FAIL"], interpreter=bad)

    def test_empty_allowed_raises(self) -> None:
        with self.assertRaises(ValueError):
            interpret_signal("PASS", [])

    def test_case_insensitive_match(self) -> None:
        prose = "최종: pass\n"
        self.assertEqual(interpret_signal(prose, ["PASS", "FAIL"]), "PASS")

    def test_word_boundary_no_substring_match(self) -> None:
        # "BUGFIX_PASS" 안에 "PASS" 가 substring 으로 들어있어도
        # 단어경계 기준으로 BUGFIX_PASS 가 매칭되어야 한다 (BUGFIX_PASS 가 우선).
        prose = "결론: BUGFIX_PASS\n"
        self.assertEqual(
            interpret_signal(prose, ["BUGFIX_PASS", "BUGFIX_FAIL"]),
            "BUGFIX_PASS",
        )

    def test_non_str_prose_rejected(self) -> None:
        with self.assertRaises(TypeError):
            interpret_signal(123, ["PASS"])  # type: ignore[arg-type]


class ClearRunStateTests(unittest.TestCase):
    def setUp(self) -> None:
        self._td = TemporaryDirectory()
        self.base = Path(self._td.name)

    def tearDown(self) -> None:
        self._td.cleanup()

    def test_clear_removes_md_files(self) -> None:
        write_prose("validator", "r", "x", base_dir=self.base)
        write_prose("architect", "r", "y", base_dir=self.base)
        count = clear_run_state("r", base_dir=self.base)
        self.assertEqual(count, 2)

    def test_clear_missing_dir_returns_zero(self) -> None:
        self.assertEqual(clear_run_state("absent-run", base_dir=self.base), 0)

    def test_clear_rejects_traversal(self) -> None:
        with self.assertRaises(ValueError):
            clear_run_state("../escape", base_dir=self.base)


class MissingSignalEnumTests(unittest.TestCase):
    def test_known_reasons_accepted(self) -> None:
        for reason in ("not_found", "empty", "ambiguous"):
            err = MissingSignal(reason, "x")
            self.assertEqual(err.reason, reason)

    def test_unknown_reason_rejected(self) -> None:
        with self.assertRaises(ValueError):
            MissingSignal("schema_violation", "x")  # 폐기된 reason


if __name__ == "__main__":
    unittest.main()
