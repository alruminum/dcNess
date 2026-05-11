#!/usr/bin/env node
/**
 * enum 시스템 ROI 실측 분석 — 이슈 #277.
 *
 * 외부 활성화 프로젝트의 .metrics/heuristic-calls.jsonl 들을 모아
 * agent 별 outcome 비율 + handoff-matrix.md §1 drift 검출.
 *
 * 사용:
 *   node scripts/research/enum_roi_baseline.mjs [path1] [path2] ...
 *
 * 인자 미지정 시 기본 경로 (jajang 4 + dcTest 1) 시도.
 *
 * 산출물: docs/internal/enum-roi-baseline.md (수동 작성용 raw stats).
 *
 * agent 분류는 allowed enum 셋 시그니처 기반 (record 에 agent name 부재).
 * 매트릭스와 drift 가 있으면 "unclassified:..." 로 표시 — 그 자체가 발견.
 */
import { readFileSync, existsSync } from 'node:fs';

const DEFAULT_FILES = [
  '/Users/dc.kim/project/jajang/.metrics/heuristic-calls.jsonl',
  '/Users/dc.kim/project/jajang/apps/api/.metrics/heuristic-calls.jsonl',
  '/Users/dc.kim/project/jajang/apps/mobile/.metrics/heuristic-calls.jsonl',
  '/Users/dc.kim/project/jajang/packages/mobile-qa-tour/.metrics/heuristic-calls.jsonl',
  '/Users/dc.kim/project/dcTest/.metrics/heuristic-calls.jsonl',
];

const FILES = process.argv.slice(2).length > 0 ? process.argv.slice(2) : DEFAULT_FILES;

function classify(allowed) {
  const s = new Set(allowed);
  const has = (...xs) => xs.every(x => s.has(x));
  if (has('PRODUCT_PLAN_READY', 'CLARITY_INSUFFICIENT')) return 'product-planner';
  if (has('PLAN_REVIEW_PASS', 'PLAN_REVIEW_FAIL')) return 'plan-reviewer';
  if (has('UX_FLOW_READY', 'UX_FLOW_PATCHED', 'UX_REFINE_READY')) return 'ux-architect';
  if (has('SPEC_GAP_RESOLVED', 'PRODUCT_PLANNER_ESCALATION_NEEDED')) return 'architect.spec-gap';
  if (has('DOCS_SYNCED', 'SPEC_GAP_FOUND', 'TECH_CONSTRAINT_CONFLICT')) return 'architect.docs-sync';
  if (has('SYSTEM_DESIGN_READY') && allowed.length === 1) return 'architect.system-design/tech-epic';
  if (has('READY_FOR_IMPL') && allowed.length === 1) return 'architect.module-plan';
  if (has('LIGHT_PLAN_READY') && allowed.length === 1) return 'architect.light-plan';
  if (has('IMPL_DONE', 'IMPL_PARTIAL', 'SPEC_GAP_FOUND', 'TESTS_FAIL')) return 'engineer';
  if (has('POLISH_DONE') && allowed.length === 1) return 'engineer.polish';
  if (has('TESTS_WRITTEN')) return 'test-engineer';
  if (has('DESIGN_READY_FOR_REVIEW', 'DESIGN_LOOP_ESCALATE')) return 'designer';
  if (has('VARIANTS_APPROVED', 'VARIANTS_ALL_REJECTED')) return 'design-critic';
  // validator 단순화 후 — 두 검증 에이전트 모두 PASS/FAIL/ESCALATE 통일.
  // legacy enum (SPEC_MISSING, DESIGN_REVIEW_*) 도 호환 매칭.
  if (has('PASS', 'FAIL', 'ESCALATE')) return 'validator';
  if (has('PASS', 'FAIL', 'SPEC_MISSING')) return 'validator.legacy-code';
  if (has('DESIGN_REVIEW_PASS', 'DESIGN_REVIEW_FAIL')) return 'validator.legacy-design';
  if (has('PASS', 'FAIL') && allowed.length === 2) return 'validator.legacy-ux-or-bugfix';
  if (has('LGTM', 'CHANGES_REQUESTED')) return 'pr-reviewer';
  if (has('FUNCTIONAL_BUG', 'CLEANUP', 'DESIGN_ISSUE', 'KNOWN_ISSUE', 'SCOPE_ESCALATE')) return 'qa';
  if (has('SECURE', 'VULNERABILITIES_FOUND')) return 'security-reviewer';
  return `unclassified:${allowed.join(',')}`;
}

const events = [];
for (const f of FILES) {
  if (!existsSync(f)) {
    console.error(`[skip] ${f} (not found)`);
    continue;
  }
  for (const line of readFileSync(f, 'utf-8').split('\n')) {
    const t = line.trim();
    if (!t) continue;
    try { events.push({ ...JSON.parse(t), _file: f }); } catch {}
  }
}

console.log(`총 records: ${events.length}`);
if (events.length === 0) {
  console.log('데이터 없음 — 활성화 프로젝트의 .metrics/ 경로 확인.');
  process.exit(0);
}
console.log(`기간: ${events[0]?.ts} ~ ${events[events.length - 1]?.ts}`);
console.log('');

const oc = new Map();
for (const e of events) {
  const k = e.outcome || 'unknown';
  oc.set(k, (oc.get(k) || 0) + 1);
}
console.log('=== 전체 Outcome 분포 ===');
const total = events.length;
for (const [k, v] of [...oc.entries()].sort((a, b) => b[1] - a[1])) {
  console.log(`  ${k.padEnd(30)} ${String(v).padStart(4)} (${(v / total * 100).toFixed(1)}%)`);
}

const byAgent = new Map();
for (const e of events) {
  const ag = classify(e.allowed || []);
  if (!byAgent.has(ag)) byAgent.set(ag, { total: 0, hit: 0, ambiguous: 0, not_found: 0, empty: 0, samples: [] });
  const b = byAgent.get(ag);
  b.total++;
  const oo = e.outcome || '';
  if (oo === 'heuristic_hit') b.hit++;
  else if (oo === 'heuristic_ambiguous') b.ambiguous++;
  else if (oo === 'heuristic_not_found') b.not_found++;
  else if (oo === 'heuristic_empty') b.empty++;
  if (oo !== 'heuristic_hit' && b.samples.length < 3) {
    b.samples.push({ ts: e.ts, outcome: oo, detail: (e.detail || '').substring(0, 140), allowed: e.allowed });
  }
}

console.log('');
console.log('=== Agent 별 분포 (drift 발견 시 unclassified:... 표시) ===');
console.log('  agent                            total  hit%   amb%   nf%   empty%');
const rows = [...byAgent.entries()].sort((a, b) => b[1].total - a[1].total);
for (const [ag, b] of rows) {
  const failRate = (b.total - b.hit) / b.total * 100;
  console.log(`  ${ag.padEnd(34)} ${String(b.total).padStart(4)}  ${(b.hit / b.total * 100).toFixed(1).padStart(5)}  ${(b.ambiguous / b.total * 100).toFixed(1).padStart(5)}  ${(b.not_found / b.total * 100).toFixed(1).padStart(4)}  ${(b.empty / b.total * 100).toFixed(1).padStart(5)}  [실패률 ${failRate.toFixed(1)}%]`);
}

console.log('');
console.log('=== 비-hit 샘플 (각 agent 최대 3건) ===');
for (const [ag, b] of rows) {
  if (b.samples.length === 0) continue;
  console.log(`\n[${ag}]`);
  for (const s of b.samples) {
    console.log(`  ${s.ts}  ${s.outcome}`);
    console.log(`    allowed=[${s.allowed.join(',')}]`);
    console.log(`    detail=${s.detail}`);
  }
}
