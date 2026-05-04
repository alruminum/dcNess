#!/usr/bin/env node
/**
 * dcNess Task-ID 형식 검증 게이트
 * 규칙 정의: docs/process/governance.md §2.1 (SSOT)
 *
 * 사용:
 *   node scripts/check_task_id.mjs                 # 로컬: HEAD 커밋 1개 검사
 *   node scripts/check_task_id.mjs <base> <head>   # CI: base..head 범위 검사
 *
 * 규칙:
 *   - 모든 비-머지 커밋은 메시지(subject 또는 body) 안에 정확히 1개의
 *     DCN-CHG-YYYYMMDD-NN 토큰을 포함해야 한다.
 *   - 토큰 패턴: ^DCN-CHG-\d{8}-\d{2}$ (zero-pad 일별 순번)
 *   - 머지 커밋(2개 이상 parent)은 검사 면제 — squash merge 합본 등 자동 생성 케이스.
 *   - Document-Exception-Task: DCN-CHG-... 도 동일 토큰으로 인정.
 *
 * exit 0: 통과
 * exit 1: 위반 (Task-ID 누락 / 형식 위반 / 다중 ID)
 *
 * proposal §5 Phase 3 — "Task-ID 형식 검증 → workflow regex" 정합.
 * proposal §11 4-pillar #2 — local 우회 가능 영역 CI 최후 차단.
 */
import { execSync } from 'node:child_process';

const TASK_ID_RE = /\bDCN-CHG-\d{8}-\d{2}\b/g;
const TASK_ID_STRICT_RE = /^DCN-CHG-\d{8}-\d{2}$/;

function git(cmd) {
  try {
    return execSync(cmd, { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] });
  } catch {
    return '';
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

function getCommitsInRange(base, head) {
  const raw = git(`git log --format=%H ${base}..${head}`);
  return raw.split('\n').map(s => s.trim()).filter(Boolean);
}

function isMergeCommit(sha) {
  const parents = git(`git log -1 --format=%P ${sha}`).trim().split(/\s+/).filter(Boolean);
  return parents.length >= 2;
}

function getCommitMessage(sha) {
  return git(`git log -1 --format=%B ${sha}`);
}

function getCommitSubject(sha) {
  return git(`git log -1 --format=%s ${sha}`).trim();
}

/**
 * 단일 메시지 검증.
 * @returns {{ok: boolean, error?: string, taskIds: string[]}}
 */
function validateMessage(message) {
  const matches = message.match(TASK_ID_RE) || [];
  const unique = [...new Set(matches)];

  if (unique.length === 0) {
    return { ok: false, error: 'Task-ID 누락 — DCN-CHG-YYYYMMDD-NN 토큰 필요', taskIds: [] };
  }

  // 다중 Task-ID 는 governance §2.1 위반 — "단 하나의 Task-ID"
  if (unique.length > 1) {
    return {
      ok: false,
      error: `다중 Task-ID 발견 (${unique.length}개): ${unique.join(', ')} — governance §2.1 위반`,
      taskIds: unique,
    };
  }

  // 엄격 매칭 검증 (이미 regex 가 보장하지만 방어적으로 재확인)
  for (const id of unique) {
    if (!TASK_ID_STRICT_RE.test(id)) {
      return { ok: false, error: `형식 위반: ${id}`, taskIds: unique };
    }
  }

  return { ok: true, taskIds: unique };
}

// === 메인 ===
const args = process.argv.slice(2);

if (!isGitRepo() && !args.includes('--pr-title')) {
  console.log('[task-id] not a git repo — skip');
  process.exit(0);
}

// commit 범위 모드 (CI)
let commits = [];
if (args.length === 2) {
  const [base, head] = args;
  // 빈 SHA 폴백
  if (!base || base === '0000000000000000000000000000000000000000') {
    console.log('[task-id] base SHA 부재 — initial push, skip');
    process.exit(0);
  }
  commits = getCommitsInRange(base, head);
} else if (args.length === 0) {
  // 로컬: HEAD 1개
  const head = git('git rev-parse HEAD').trim();
  if (head) commits = [head];
} else {
  console.error('[task-id] 사용법:');
  console.error('  node scripts/check_task_id.mjs                 # 로컬 HEAD');
  console.error('  node scripts/check_task_id.mjs <base> <head>   # CI 범위');
  console.error('  node scripts/check_task_id.mjs --pr-title "<title>"');
  process.exit(1);
}

if (commits.length === 0) {
  console.log('[task-id] 검사 대상 커밋 0 — skip');
  process.exit(0);
}

const violations = [];
let passed = 0;
let skippedMerges = 0;

for (const sha of commits) {
  if (isMergeCommit(sha)) {
    skippedMerges++;
    continue;
  }
  const msg = getCommitMessage(sha);
  const subject = getCommitSubject(sha);
  const result = validateMessage(msg);
  if (!result.ok) {
    violations.push({
      sha: sha.substring(0, 7),
      subject,
      error: result.error,
    });
  } else {
    passed++;
  }
}

if (violations.length > 0) {
  console.error('[task-id] FAIL — 위반 커밋:');
  for (const v of violations) {
    console.error(`  ${v.sha} "${v.subject}"`);
    console.error(`    → ${v.error}`);
  }
  console.error('');
  console.error('규칙: docs/process/governance.md §2.1 (Task-ID = DCN-CHG-YYYYMMDD-NN, 커밋당 1개)');
  process.exit(1);
}

console.log(`[task-id] PASS`);
console.log(`  검사: ${commits.length}, 통과: ${passed}, 머지 면제: ${skippedMerges}`);
