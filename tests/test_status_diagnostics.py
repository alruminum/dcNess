"""test_status_diagnostics — `dcness-helper status` 진단표 (#520).

Coverage matrix:
    _is_self_repo            : name==dcness / 다른 name / 파일 없음 / 깨진 json
    _installed_plugin_version: 정상 / 파일 없음
    _check_read_permission   : PERM 존재 / 부재 / 파일 없음
    _check_git_hooks         : thin-shim ok / missing / foreign
    _check_ci_workflows      : 존재 / 부재
    collect_status_diagnostics:
        self repo  → 외부 활성 항목 전부 NA
        외부 repo  → whitelist 미등록 시 FAIL + fix 명령
    format_status_report     : badge 출력 / self 헤더 분리 / 요약 카운트

대 원칙 정합:
    - 진단 수집은 deterministic 코드 (추측 누락 차단). 출력 종합/권유는 init-dcness skill.
    - self repo 와 외부 활성 규칙을 섞지 않는다 (#520 AC 5).
"""
from __future__ import annotations

import json
import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from harness.session_state import (
    _check_ci_workflows,
    _check_git_hooks,
    _check_read_permission,
    _installed_plugin_version,
    _is_self_repo,
    collect_status_diagnostics,
    format_status_report,
)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class IsSelfRepoTests(unittest.TestCase):
    def test_name_dcness_is_self(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            _write(root / ".claude-plugin" / "plugin.json", '{"name":"dcness","version":"0.7.1"}')
            self.assertTrue(_is_self_repo(root))

    def test_other_name_not_self(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            _write(root / ".claude-plugin" / "plugin.json", '{"name":"other"}')
            self.assertFalse(_is_self_repo(root))

    def test_missing_file_not_self(self) -> None:
        with TemporaryDirectory() as td:
            self.assertFalse(_is_self_repo(Path(td)))

    def test_broken_json_not_self(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            _write(root / ".claude-plugin" / "plugin.json", "{not json")
            self.assertFalse(_is_self_repo(root))


class InstalledVersionTests(unittest.TestCase):
    def test_reads_version(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            _write(root / ".claude-plugin" / "plugin.json", '{"name":"dcness","version":"9.9.9"}')
            self.assertEqual(_installed_plugin_version(root), "9.9.9")

    def test_missing_returns_none(self) -> None:
        with TemporaryDirectory() as td:
            self.assertIsNone(_installed_plugin_version(Path(td)))


class ReadPermissionTests(unittest.TestCase):
    PERM = "Read(~/.claude/plugins/cache/dcness/**)"

    def test_perm_present(self) -> None:
        with TemporaryDirectory() as td:
            sp = Path(td) / "settings.json"
            _write(sp, json.dumps({"permissions": {"allow": [self.PERM]}}))
            self.assertTrue(_check_read_permission(sp))

    def test_perm_absent(self) -> None:
        with TemporaryDirectory() as td:
            sp = Path(td) / "settings.json"
            _write(sp, json.dumps({"permissions": {"allow": ["Read(/other/**)"]}}))
            self.assertFalse(_check_read_permission(sp))

    def test_missing_file(self) -> None:
        with TemporaryDirectory() as td:
            self.assertFalse(_check_read_permission(Path(td) / "settings.json"))


class GitHooksTests(unittest.TestCase):
    def _hooks_dir(self, root: Path) -> Path:
        d = root / ".git" / "hooks"
        d.mkdir(parents=True, exist_ok=True)
        return d

    def test_thin_shim_ok(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            hd = self._hooks_dir(root)
            for name in ("commit-msg", "post-checkout", "pre-push"):
                _write(hd / name, "#!/bin/sh\n# uses ~/.claude/plugins/cache/dcness/dcness\n")
            result = _check_git_hooks(root)
            self.assertEqual(set(result.values()), {"ok"})

    def test_missing_hook(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            self._hooks_dir(root)
            result = _check_git_hooks(root)
            self.assertEqual(result["commit-msg"], "missing")

    def test_foreign_hook(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            hd = self._hooks_dir(root)
            _write(hd / "commit-msg", "#!/bin/sh\necho hello\n")
            result = _check_git_hooks(root)
            self.assertEqual(result["commit-msg"], "foreign")


class CiWorkflowTests(unittest.TestCase):
    def test_present_and_absent(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            wf = root / ".github" / "workflows"
            wf.mkdir(parents=True, exist_ok=True)
            _write(wf / "git-naming-validation.yml", "name: x\n")
            result = _check_ci_workflows(root)
            self.assertTrue(result["git-naming-validation.yml"])
            self.assertFalse(result["pr-body-validation.yml"])


class CollectSelfRepoTests(unittest.TestCase):
    def test_self_repo_external_items_na(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            _write(root / ".claude-plugin" / "plugin.json", '{"name":"dcness","version":"0.7.1"}')
            diag = collect_status_diagnostics(
                cwd=root, check_gh=False, check_routing=False
            )
            self.assertTrue(diag["self_repo"])
            by_key = {c["key"]: c for c in diag["checks"]}
            for key in ("whitelist", "read_perm", "git_hooks", "ci_workflows"):
                self.assertEqual(by_key[key]["status"], "NA", key)


class CollectExternalRepoTests(unittest.TestCase):
    def setUp(self) -> None:
        self._wl = TemporaryDirectory()
        os.environ["DCNESS_WHITELIST_PATH"] = str(Path(self._wl.name) / "projects.json")

    def tearDown(self) -> None:
        os.environ.pop("DCNESS_WHITELIST_PATH", None)
        self._wl.cleanup()

    def test_external_unregistered_whitelist_fail(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)  # no .claude-plugin → external
            diag = collect_status_diagnostics(
                cwd=root, check_gh=False, check_routing=False
            )
            self.assertFalse(diag["self_repo"])
            by_key = {c["key"]: c for c in diag["checks"]}
            self.assertEqual(by_key["whitelist"]["status"], "FAIL")
            self.assertIn("enable", (by_key["whitelist"]["fix"] or ""))


class FormatReportTests(unittest.TestCase):
    def test_self_header_and_summary(self) -> None:
        diag = {
            "project_root": "/x",
            "self_repo": True,
            "checks": [
                {"key": "a", "label": "A", "status": "INFO", "detail": "d", "fix": None},
                {"key": "b", "label": "B", "status": "NA", "detail": "self", "fix": None},
            ],
            "summary": {"PASS": 0, "WARN": 0, "FAIL": 0},
        }
        out = format_status_report(diag)
        self.assertIn("self repo", out.lower())
        self.assertIn("[NA]", out)

    def test_external_badges_and_counts(self) -> None:
        diag = {
            "project_root": "/x",
            "self_repo": False,
            "checks": [
                {"key": "w", "label": "whitelist", "status": "FAIL", "detail": "no", "fix": "dcness-helper enable"},
                {"key": "g", "label": "gh", "status": "WARN", "detail": "no auth", "fix": "gh auth login"},
                {"key": "p", "label": "perm", "status": "PASS", "detail": "ok", "fix": None},
            ],
            "summary": {"PASS": 1, "WARN": 1, "FAIL": 1},
        }
        out = format_status_report(diag)
        self.assertIn("[FAIL]", out)
        self.assertIn("[WARN]", out)
        self.assertIn("[PASS]", out)
        self.assertIn("dcness-helper enable", out)  # fix 명령 노출
        self.assertIn("1 PASS", out)
        self.assertIn("1 FAIL", out)


if __name__ == "__main__":
    unittest.main()
