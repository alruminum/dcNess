"""hooks/tdd-guard.sh 단위 테스트 — entry-file false-positive 회피 (#423).

검증 범위:
- 기존 skip 룰 (test/spec 파일 자체 / config / 타입 / Next.js 특수) — 회귀 방지
- entry-file path heuristic (#423): App.{ts,tsx,js,jsx} / _layout.* / apps/*/index.* / src/main.*
- 파일 내용 시그니처 grep (#423): registerRootComponent / AppRegistry.registerComponent
- 일반 src 파일 + 테스트 부재 → deny (기존 동작 보존)
- 매칭 테스트 파일 존재 → allow

호출 메커니즘: hook 은 bash. stdin 으로 JSON payload 받고 stdout 으로 JSON 결정 반환.
"""

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOOK_PATH = ROOT / "hooks" / "tdd-guard.sh"


def run_hook(file_path: str, cwd: str, tool_name: str = "Edit") -> dict:
    """tdd-guard.sh 호출 → 결정 JSON 반환."""
    payload = {
        "tool_name": tool_name,
        "tool_input": {"file_path": file_path},
    }
    result = subprocess.run(
        ["bash", str(HOOK_PATH)],
        input=json.dumps(payload),
        capture_output=True, text=True, cwd=cwd, timeout=10,
    )
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {}


def decision(out: dict) -> str:
    """allow / deny 추출."""
    spec = out.get("hookSpecificOutput", {})
    return spec.get("permissionDecision", "unknown")


class TestEntryFileHeuristic(unittest.TestCase):
    """#423 — entry-file path heuristic skip."""

    def setUp(self):
        self._tmp = tempfile.mkdtemp()
        subprocess.run(["git", "init"], cwd=self._tmp, capture_output=True)

    def tearDown(self):
        shutil.rmtree(self._tmp, ignore_errors=True)

    def _touch(self, rel: str, content: str = "// stub\n") -> str:
        p = Path(self._tmp) / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return str(p)

    def test_app_tsx_skipped(self):
        path = self._touch("apps/mobile/App.tsx")
        self.assertEqual(decision(run_hook(path, self._tmp)), "allow")

    def test_app_js_skipped(self):
        path = self._touch("apps/mobile/App.js")
        self.assertEqual(decision(run_hook(path, self._tmp)), "allow")

    def test_expo_router_layout_skipped(self):
        path = self._touch("apps/mobile/app/_layout.tsx")
        self.assertEqual(decision(run_hook(path, self._tmp)), "allow")

    def test_expo_router_group_layout_skipped(self):
        path = self._touch("apps/mobile/app/(tabs)/_layout.tsx")
        self.assertEqual(decision(run_hook(path, self._tmp)), "allow")

    def test_monorepo_apps_index_js_skipped(self):
        path = self._touch("apps/mobile/index.js")
        self.assertEqual(decision(run_hook(path, self._tmp)), "allow")

    def test_monorepo_apps_index_ts_skipped(self):
        path = self._touch("apps/web/index.ts")
        self.assertEqual(decision(run_hook(path, self._tmp)), "allow")

    def test_vue_vite_main_skipped(self):
        path = self._touch("src/main.ts")
        self.assertEqual(decision(run_hook(path, self._tmp)), "allow")


class TestSignatureGrep(unittest.TestCase):
    """#423 — 파일 내용 시그니처 grep skip."""

    def setUp(self):
        self._tmp = tempfile.mkdtemp()
        subprocess.run(["git", "init"], cwd=self._tmp, capture_output=True)

    def tearDown(self):
        shutil.rmtree(self._tmp, ignore_errors=True)

    def _write(self, rel: str, content: str) -> str:
        p = Path(self._tmp) / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return str(p)

    def test_registerRootComponent_skipped(self):
        """비-컨벤션 path 라도 registerRootComponent 시그니처 → allow."""
        path = self._write(
            "src/some-non-conventional-entry.tsx",
            "import { registerRootComponent } from 'expo';\nregisterRootComponent(App);\n",
        )
        self.assertEqual(decision(run_hook(path, self._tmp)), "allow")

    def test_AppRegistry_registerComponent_skipped(self):
        """Bare RN AppRegistry.registerComponent → allow."""
        path = self._write(
            "src/rn-bare-entry.js",
            "import { AppRegistry } from 'react-native';\nAppRegistry.registerComponent('app', () => App);\n",
        )
        self.assertEqual(decision(run_hook(path, self._tmp)), "allow")


class TestRegressionPreserved(unittest.TestCase):
    """기존 skip 룰 + deny 동작 회귀 방지."""

    def setUp(self):
        self._tmp = tempfile.mkdtemp()
        subprocess.run(["git", "init"], cwd=self._tmp, capture_output=True)

    def tearDown(self):
        shutil.rmtree(self._tmp, ignore_errors=True)

    def _touch(self, rel: str, content: str = "// stub\n") -> str:
        p = Path(self._tmp) / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return str(p)

    def test_test_file_self_skipped(self):
        path = self._touch("src/foo.test.ts")
        self.assertEqual(decision(run_hook(path, self._tmp)), "allow")

    def test_config_skipped(self):
        path = self._touch("babel.config.js")
        self.assertEqual(decision(run_hook(path, self._tmp)), "allow")

    def test_metro_config_skipped(self):
        path = self._touch("metro.config.js")
        self.assertEqual(decision(run_hook(path, self._tmp)), "allow")

    def test_app_config_ts_skipped(self):
        path = self._touch("app.config.ts")
        self.assertEqual(decision(run_hook(path, self._tmp)), "allow")

    def test_types_skipped(self):
        path = self._touch("src/types/foo.ts")
        self.assertEqual(decision(run_hook(path, self._tmp)), "allow")

    def test_non_ts_js_skipped(self):
        path = self._touch("src/foo.py")
        self.assertEqual(decision(run_hook(path, self._tmp)), "allow")

    def test_src_business_logic_without_test_denied(self):
        """일반 비즈니스 로직 + 테스트 부재 → deny (기존 동작 보존)."""
        path = self._touch(
            "src/business-logic.ts",
            "export function calculatePrice(qty, unit) { return qty * unit; }\n",
        )
        self.assertEqual(decision(run_hook(path, self._tmp)), "deny")

    def test_src_business_logic_with_test_allowed(self):
        """일반 비즈니스 로직 + 매칭 테스트 존재 → allow."""
        self._touch(
            "src/biz.ts",
            "export function calc() { return 1; }\n",
        )
        self._touch("src/biz.test.ts", "test('ok', () => {})\n")
        path = str(Path(self._tmp) / "src/biz.ts")
        self.assertEqual(decision(run_hook(path, self._tmp)), "allow")


if __name__ == "__main__":
    unittest.main()
