#!/usr/bin/env node
/**
 * dcness pre-commit TDD gate (commit-msg hook 본체)
 *
 * 룰 (v0.2.13):
 *   1. staged 안에 *src 변경* 있고 *test 변경 0건* (staged 또는 branch diff) → BLOCK
 *   2. test 변경 1+ 있음 → 그 test 들 실행. 1건이라도 FAIL → BLOCK
 *   3. commit message 안 `[skip-test: <사유>]` marker → 우회 (PASS)
 *   4. 비-코드 변경만 (md / json / yml / toml 등) → PASS
 *   5. 옵트인 마커 `.dcness/tdd-gate-enabled` 부재 → silent PASS (사용자가 init-dcness 에서 Y 선택해야 발화)
 *
 * 호출 시점: git commit-msg hook chain (git-naming 후)
 *   인자 $1 = commit message 파일 경로
 *
 * 실증 검증 (3-commit 구조):
 *   commit1 (docs): staged_src 0 → PASS
 *   commit2 (tests): staged_src 0 (test 만) → PASS
 *   commit3 (src): staged_src 있음 + branch test 있음 → PASS + 실행
 *   위반: staged_src 있음 + test 0 → BLOCK
 */

import { execSync, spawnSync } from "node:child_process";
import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";

const OPTIN_MARKER = ".dcness/tdd-gate-enabled";

// test 매처 — 4 언어 universal
const TEST_PATTERNS = [
  /\.test\.(js|jsx|ts|tsx|mjs|cjs)$/,
  /\.spec\.(js|jsx|ts|tsx|mjs|cjs)$/,
  /(^|\/)__tests__\//,
  /(^|\/)tests?\//,           // tests/ 또는 test/
  /(^|\/)test_[^/]+\.py$/,
  /_test\.py$/,
  /_test\.go$/,
];
// src 매처 — 코드 확장자 (test 제외)
const SRC_EXTENSIONS = /\.(js|jsx|ts|tsx|mjs|cjs|py|rs|go|java|kt|swift)$/;

function isTest(p) { return TEST_PATTERNS.some((re) => re.test(p)); }
function isSrc(p) { return SRC_EXTENSIONS.test(p) && !isTest(p); }

function run(cmd) {
  try {
    return execSync(cmd, { encoding: "utf8" }).trim();
  } catch {
    return "";
  }
}

function log(msg) { console.error(`[tdd-gate] ${msg}`); }
function fail(msg) { console.error(`[tdd-gate] BLOCKED — ${msg}`); process.exit(1); }

// ── 1. 옵트인 마커 검사 ───────────────────────────────────────────
const projectRoot = run("git rev-parse --show-toplevel");
if (!projectRoot) process.exit(0);  // git repo 아님 — silent pass

if (!existsSync(resolve(projectRoot, OPTIN_MARKER))) {
  process.exit(0);  // 옵트인 X — silent pass (다른 프로젝트 영향 회피)
}

// ── 2. skip marker 검사 ──────────────────────────────────────────
const commitMsgFile = process.argv[2];
if (commitMsgFile && existsSync(commitMsgFile)) {
  const msg = readFileSync(commitMsgFile, "utf8");
  const skipMatch = msg.match(/\[skip-test:\s*([^\]]+)\]/);
  if (skipMatch) {
    log(`[skip-test: ${skipMatch[1].trim()}] marker — 우회 PASS`);
    process.exit(0);
  }
}

// ── 3. staged + branch diff 분석 ─────────────────────────────────
const staged = run("git diff --cached --name-only").split("\n").filter(Boolean);
const stagedSrc = staged.filter(isSrc);
const stagedTest = staged.filter(isTest);

// branch diff — origin/main 과 비교. 없으면 HEAD 만.
let branchTest = [];
const branchDiff = run("git diff --name-only origin/main...HEAD 2>/dev/null");
if (branchDiff) {
  branchTest = branchDiff.split("\n").filter(Boolean).filter(isTest);
}

const allTest = [...new Set([...stagedTest, ...branchTest])];

// ── 4. 분기 ──────────────────────────────────────────────────────
if (stagedSrc.length === 0) {
  process.exit(0);  // src 변경 0 = PASS (docs/config 변경 등)
}

if (allTest.length === 0) {
  const srcList = stagedSrc.slice(0, 5).map((p) => "  " + p).join("\n");
  const more = stagedSrc.length > 5 ? `\n  ... (외 ${stagedSrc.length - 5}개)` : "";
  fail(`staged 안 src 변경 (${stagedSrc.length}개) 있는데 test 변경 0건.

src 변경:
${srcList}${more}

다음 중 하나:
1. test 추가 후 함께 commit (TDD: 테스트 먼저)
2. commit message 에 [skip-test: <사유>] marker 박기
   (단순 typo / 문서 변경 / refactor 무영향 등 정당 사유)
3. test-engineer 가 별도 commit 한 후 src commit 진행 (impl-task-loop 의 3-commit 구조)`);
}

// ── 5. test 실행 — staged + branch 안 test 만 ────────────────────
log(`staged src ${stagedSrc.length}개 + 인지된 test ${allTest.length}개 → 실행`);

// 언어별 분류
const nodeTests = allTest.filter((t) => /\.(test|spec)\.|\/__tests__\//.test(t));
const pyTests = allTest.filter((t) => /\.py$/.test(t));
const goTests = allTest.filter((t) => /_test\.go$/.test(t));
const rsTests = allTest.filter((t) => /(^|\/)tests\/.*\.rs$/.test(t));

// node — jest / vitest 자동 검출
if (nodeTests.length > 0) {
  log(`node tests (${nodeTests.length}): 실행`);
  const pkgPath = resolve(projectRoot, "package.json");
  if (!existsSync(pkgPath)) fail("package.json 부재인데 node test 검출됨");
  const pkg = JSON.parse(readFileSync(pkgPath, "utf8"));
  const deps = { ...pkg.dependencies, ...pkg.devDependencies };
  let cmd, args;
  if (deps.vitest) { cmd = "npx"; args = ["vitest", "run", ...nodeTests]; }
  else if (deps.jest) { cmd = "npx"; args = ["jest", ...nodeTests]; }
  else {
    // 폴백 — npm test (test runner 미상)
    cmd = "npm"; args = ["test", "--", ...nodeTests];
  }
  const r = spawnSync(cmd, args, { stdio: "inherit", cwd: projectRoot });
  if (r.status !== 0) fail(`node tests FAIL (${cmd} ${args.slice(0, 2).join(" ")} ...)`);
}

if (pyTests.length > 0) {
  log(`python tests (${pyTests.length}): 실행`);
  const r = spawnSync("pytest", pyTests, { stdio: "inherit", cwd: projectRoot });
  if (r.status !== 0) fail("python tests FAIL");
}

if (goTests.length > 0) {
  // go test 는 파일 단위 X — 디렉토리 단위. 유니크 dir.
  const dirs = [...new Set(goTests.map((t) => {
    const i = t.lastIndexOf("/");
    return i < 0 ? "." : t.slice(0, i);
  }))];
  log(`go tests (${dirs.length} dir): 실행`);
  for (const d of dirs) {
    const r = spawnSync("go", ["test", `./${d}/...`], { stdio: "inherit", cwd: projectRoot });
    if (r.status !== 0) fail(`go tests FAIL (./${d}/...)`);
  }
}

if (rsTests.length > 0) {
  // rust — integration test 파일 단위 가능. 단순화: cargo test 만.
  log(`rust tests (${rsTests.length}): cargo test 실행`);
  const r = spawnSync("cargo", ["test"], { stdio: "inherit", cwd: projectRoot });
  if (r.status !== 0) fail("rust tests FAIL");
}

log("PASS — TDD 게이트 통과");
process.exit(0);
