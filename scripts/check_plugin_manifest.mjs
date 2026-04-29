#!/usr/bin/env node
/**
 * dcNess plugin manifest validator (CI level).
 *
 * 검증:
 * - .claude-plugin/plugin.json 파싱 가능 + 필수 필드(name, version, description)
 * - .claude-plugin/marketplace.json 파싱 가능 + plugins[] 의 첫 entry name 이 plugin.json.name 과 일치
 *
 * `claude plugin validate` (CLI 의존) 를 도입하지 않은 이유:
 * - GitHub Actions 환경에서 claude CLI 설치/인증 의존성 발생
 * - 본 검증은 *형식 무결성* 만 — 의미 검증은 plugin install 시점에 매니저가 수행
 *
 * 사용:
 *   node scripts/check_plugin_manifest.mjs
 *
 * exit 0: 통과
 * exit 1: 위반
 */
import { readFileSync, existsSync } from 'node:fs';
import { resolve } from 'node:path';

const PLUGIN_PATH = resolve('.claude-plugin/plugin.json');
const MARKETPLACE_PATH = resolve('.claude-plugin/marketplace.json');

const violations = [];

function parseJsonFile(path, label) {
  if (!existsSync(path)) {
    violations.push(`${label}: file not found at ${path}`);
    return null;
  }
  try {
    return JSON.parse(readFileSync(path, 'utf8'));
  } catch (e) {
    violations.push(`${label}: JSON parse error — ${e.message}`);
    return null;
  }
}

const plugin = parseJsonFile(PLUGIN_PATH, 'plugin.json');
const marketplace = parseJsonFile(MARKETPLACE_PATH, 'marketplace.json');

if (plugin) {
  for (const key of ['name', 'version', 'description']) {
    if (!plugin[key] || typeof plugin[key] !== 'string') {
      violations.push(`plugin.json: missing/invalid required field '${key}'`);
    }
  }
  if (plugin.name && !/^[a-z][a-z0-9-]*$/.test(plugin.name)) {
    violations.push(
      `plugin.json: name '${plugin.name}' must match /^[a-z][a-z0-9-]*$/`
    );
  }
}

if (marketplace) {
  if (!Array.isArray(marketplace.plugins) || marketplace.plugins.length === 0) {
    violations.push('marketplace.json: plugins[] must be non-empty array');
  } else {
    const first = marketplace.plugins[0];
    if (!first.name) {
      violations.push('marketplace.json: plugins[0].name missing');
    } else if (plugin && first.name !== plugin.name) {
      violations.push(
        `marketplace.json: plugins[0].name '${first.name}' != plugin.json.name '${plugin.name}'`
      );
    }
    if (!first.source) {
      violations.push('marketplace.json: plugins[0].source missing');
    }
  }
}

if (violations.length > 0) {
  console.error('[plugin-manifest] FAIL');
  violations.forEach((v) => console.error(`  - ${v}`));
  process.exit(1);
}

console.log(
  `[plugin-manifest] PASS — ${plugin.name}@${plugin.version}`
);
