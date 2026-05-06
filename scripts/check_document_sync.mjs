#!/usr/bin/env node
/**
 * dcNess Document Sync gate
 * 규칙 정의: docs/internal/governance.md §2.5 / §2.6 (SSOT)
 *
 * 사용:
 *   node scripts/check_document_sync.mjs                 # 로컬 (staged + unstaged)
 *   node scripts/check_document_sync.mjs <base> <head>   # CI (commit range)
 *
 * exit 0: 통과
 * exit 1: 위반 (수정 필요)
 */
import { execSync } from 'node:child_process';

// === Change-Type 분류 (governance §2.2) ===
// 분류 우선순위: 위에서 아래로. 한 파일이 여러 패턴에 매칭되면 *상위* 토큰 채택.
const CATEGORY_RULES = [
  { token: 'spec',      patterns: [/^docs\/spec\//, /^docs\/proposals\//, /^prd\.md$/, /^trd\.md$/] },
  { token: 'agent',     patterns: [/^agents\//, /^\.claude\/agent-config\//, /^\.claude-plugin\//, /^CLAUDE\.md$/, /^AGENTS\.md$/, /^docs\/epic-index\.md$/] },
  { token: 'harness',   patterns: [/^harness\//, /^src\//] },
  { token: 'hooks',     patterns: [/^hooks\//, /^\.claude\/hooks\//] },
  { token: 'ci',        patterns: [/^\.github\/workflows\//, /^scripts\//] },
  { token: 'test',      patterns: [/^tests\//, /\.test\./, /_test\./] },
  { token: 'docs-only', patterns: [/^docs\//] },
];

function classify(file) {
  for (const { token, patterns } of CATEGORY_RULES) {
    if (patterns.some(p => p.test(file))) return token;
  }
  return null; // 분류 불가 (예: 루트 README, .gitignore) — 게이트 비대상
}

// === git diff 추출 ===
function git(cmd) {
  try {
    return execSync(cmd, { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] });
  } catch (e) {
    return ''; // not a git repo / no HEAD / unknown option (예: 빈 저장소) — 빈 결과로 처리
  }
}

function isGitRepo() {
  try {
    execSync('git rev-parse --is-inside-work-tree', { stdio: ['ignore', 'pipe', 'pipe'] });
    return true;
  } catch {
    return false;
  }
}

function getChangedFiles(args) {
  if (args.length === 2) {
    const [base, head] = args;
    return git(`git diff --name-only ${base} ${head}`).split('\n').filter(Boolean);
  }
  // 로컬: staged + unstaged 합집합 (이미 commit 한 변경은 staged 로 잡힘)
  const staged   = git('git diff --cached --name-only').split('\n').filter(Boolean);
  const unstaged = git('git diff --name-only HEAD').split('\n').filter(Boolean);
  return [...new Set([...staged, ...unstaged])];
}

// === diff 의 추가 라인에서 Document-Exception 추출 (governance §2.4) ===
// 과거 누적 엔트리(이미 commit 된 옛 Exception)는 무효 — 추가 라인(`+`)만 검사.
function getExceptionFromAddedLines(args) {
  let raw = '';
  if (args.length === 2) {
    raw = git(`git diff ${args[0]} ${args[1]}`);
  } else {
    raw = git('git diff --cached HEAD') + '\n' + git('git diff HEAD');
  }
  for (const line of raw.split('\n')) {
    if (!line.startsWith('+') || line.startsWith('+++')) continue;
    const m = line.match(/Document-Exception:\s*(.+)$/);
    if (m) return m[1].trim();
  }
  // commit 메시지에서도 검사 (CI mode 의 head commit message)
  if (args.length === 2) {
    const msg = git(`git log -1 --format=%B ${args[1]}`);
    const m = msg.match(/Document-Exception:\s*(.+)$/m);
    if (m) return m[1].trim();
  }
  return null;
}

// === 메인 ===
const args = process.argv.slice(2);

if (!isGitRepo()) {
  console.log('[doc-sync] not a git repo — skip (run `git init` to enable)');
  process.exit(0);
}

const files = getChangedFiles(args);

if (files.length === 0) {
  console.log('[doc-sync] no changed files — skip');
  process.exit(0);
}

const fileTokens = new Map(files.map(f => [f, classify(f)]));
const tokens = new Set([...fileTokens.values()].filter(Boolean));

if (tokens.size === 0) {
  console.log('[doc-sync] no governed categories — skip');
  console.log(`  files: ${files.join(', ')}`);
  process.exit(0);
}

const violations = [];

// (a) 모든 변경: WHAT 로그 필수
const RECORD = 'docs/internal/document_update_record.md';
if (!files.includes(RECORD)) {
  violations.push(`missing: ${RECORD} (any governed change requires WHAT log)`);
}

// (b) heavy 카테고리: WHY 로그 필수
const HEAVY = ['spec', 'agent', 'harness', 'hooks', 'ci'];
const RATIONALE = 'docs/internal/change_rationale_history.md';
if (HEAVY.some(t => tokens.has(t)) && !files.includes(RATIONALE)) {
  violations.push(`missing: ${RATIONALE} (heavy categories require WHY log)`);
}

// (c) progress 카테고리: PROGRESS.md 필수
const PROGRESS_REQ = ['harness', 'hooks', 'ci'];
const PROGRESS = 'PROGRESS.md';
if (PROGRESS_REQ.some(t => tokens.has(t)) && !files.includes(PROGRESS)) {
  violations.push(`missing: ${PROGRESS} (code/build categories require status update)`);
}

// (d) 카테고리별 deliverable
const matchesAny = (regexes) => files.some(f => regexes.some(r => r.test(f)));
if (tokens.has('spec') && !matchesAny([/^docs\/spec\//, /^docs\/proposals\//])) {
  violations.push(`spec change requires docs/spec/** or docs/proposals/** deliverable (or Document-Exception)`);
}
if (tokens.has('harness') && !matchesAny([/^tests\//, /^docs\/impl\//])) {
  violations.push(`harness change requires tests/** or docs/impl/** companion (or Document-Exception)`);
}

// === Document-Exception 처리 ===
if (violations.length > 0) {
  const exc = getExceptionFromAddedLines(args);
  if (exc) {
    console.log(`[doc-sync] Document-Exception detected — bypassing checks`);
    console.log(`  reason: ${exc}`);
    console.log(`  waived: ${violations.length} violation(s)`);
    violations.forEach(v => console.log(`    - ${v}`));
    process.exit(0);
  }
  console.error('[doc-sync] FAIL — violations:');
  violations.forEach(v => console.error(`  - ${v}`));
  console.error('');
  console.error('규칙: docs/internal/governance.md §2.6');
  console.error('예외: 현재 diff 추가 라인 또는 commit 메시지에 `Document-Exception: <사유>` 기재');
  process.exit(1);
}

console.log('[doc-sync] PASS');
console.log(`  files: ${files.length}`);
console.log(`  categories: ${[...tokens].join(', ')}`);
