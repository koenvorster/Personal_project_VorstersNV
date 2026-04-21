#!/usr/bin/env node
// .claude/scripts/validate-agents.mjs
import { readFileSync, readdirSync, writeFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const AGENTS_DIR = join(__dirname, '..', 'agents');

const VALID_MODELS = [
  'claude-haiku-4-5', 'claude-sonnet-4-5', 'claude-opus-4-5',
  'claude-haiku-4-6', 'claude-sonnet-4-6', 'claude-opus-4-6',
  'claude-haiku-4', 'claude-sonnet-4',
];

const POSSIBLY_OUTDATED = ['claude-haiku-4', 'claude-sonnet-4'];

const REQUIRED_FIELDS = ['name', 'description', 'model', 'permissionMode'];
// 'allow' = full tool access (code-writing agents), 'default' = read/plan agents, 'restricted' = safest
const VALID_PERMISSION_MODES = ['default', 'restricted', 'allow'];

const COLORS = {
  reset: '\x1b[0m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  bold: '\x1b[1m',
};

const quiet = process.argv.includes('--quiet');
const fix = process.argv.includes('--fix');

function colorize(text, color) {
  return `${COLORS[color]}${text}${COLORS.reset}`;
}

/**
 * Parses YAML frontmatter from markdown content.
 * Handles: simple key:value, folded scalars (>), literal blocks (|), block lists.
 * No external dependencies — stdlib only.
 */
function parseFrontmatter(content) {
  const match = content.match(/^---\r?\n([\s\S]*?)\r?\n---/);
  if (!match) return { raw: null, fields: {} };

  const raw = match[1];
  const fields = {};
  const lines = raw.split(/\r?\n/);
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];
    const keyMatch = line.match(/^([\w][\w-]*)\s*:\s*(.*)/);
    if (!keyMatch) { i++; continue; }

    const key = keyMatch[1];
    const value = keyMatch[2].trim();

    if (value === '>') {
      // Folded scalar: join continuation lines with spaces
      const parts = [];
      i++;
      while (i < lines.length && (lines[i].startsWith('  ') || lines[i] === '')) {
        parts.push(lines[i].trim());
        i++;
      }
      fields[key] = parts.filter(Boolean).join(' ').trim();
    } else if (value === '|') {
      // Literal block scalar
      const parts = [];
      i++;
      while (i < lines.length && (lines[i].startsWith('  ') || lines[i] === '')) {
        parts.push(lines[i].startsWith('  ') ? lines[i].slice(2) : '');
        i++;
      }
      fields[key] = parts.join('\n').trim();
    } else if (value === '') {
      // Possible block sequence (list with leading - )
      const items = [];
      i++;
      while (i < lines.length && /^\s+-\s+/.test(lines[i])) {
        items.push(lines[i].replace(/^\s+-\s+/, '').trim());
        i++;
      }
      fields[key] = items.length > 0 ? items : null;
    } else {
      // Plain or quoted scalar
      fields[key] = value.replace(/^['"]|['"]$/g, '');
      i++;
    }
  }

  return { raw, fields };
}

/** Validates one agent file. Returns { errors, warnings, fields, content }. */
function validateAgent(filePath) {
  const content = readFileSync(filePath, 'utf8');
  const { raw, fields } = parseFrontmatter(content);

  const errors = [];
  const warnings = [];

  if (raw === null) {
    errors.push('No frontmatter found (missing --- delimiters)');
    return { errors, warnings, fields, content };
  }

  // Required fields
  for (const field of REQUIRED_FIELDS) {
    const val = fields[field];
    if (val === undefined || val === null || val === '') {
      errors.push(`Missing required field: ${field}`);
    }
  }

  // Valid model
  const model = fields.model;
  if (model !== undefined && model !== null && model !== '') {
    if (!VALID_MODELS.includes(model)) {
      errors.push(`Invalid model: '${model}'. Valid models: ${VALID_MODELS.join(', ')}`);
    } else if (POSSIBLY_OUTDATED.includes(model)) {
      warnings.push(`model '${model}' may be outdated`);
    }
  }

  // Description prefix
  const desc = fields.description;
  if (desc && typeof desc === 'string' && !desc.startsWith('Delegate to this agent when:')) {
    errors.push('description must start with "Delegate to this agent when:"');
  }

  // Valid permissionMode
  const pm = fields.permissionMode;
  if (pm !== undefined && pm !== null && pm !== '') {
    if (!VALID_PERMISSION_MODES.includes(pm)) {
      errors.push(`Invalid permissionMode: '${pm}'. Valid values: ${VALID_PERMISSION_MODES.join(', ')}`);
    }
  }

  return { errors, warnings, fields, content };
}

/** Applies --fix: corrects invalid values and adds missing required fields. */
function fixAgent(filePath, fileName, fields, content) {
  const { raw } = parseFrontmatter(content);
  const baseName = fileName.replace(/\.md$/, '');

  if (raw === null) {
    const fm = buildMinimalFrontmatter(baseName);
    writeFileSync(filePath, `---\n${fm}\n---\n\n${content}`, 'utf8');
    return;
  }

  let updated = raw;

  // Replace invalid model value
  if (fields.model !== undefined && fields.model !== null && fields.model !== '' &&
      !VALID_MODELS.includes(fields.model)) {
    updated = updated.replace(/^model:.*$/m, 'model: claude-haiku-4-5');
  }

  // Replace invalid permissionMode value
  if (fields.permissionMode !== undefined && fields.permissionMode !== null &&
      fields.permissionMode !== '' && !VALID_PERMISSION_MODES.includes(fields.permissionMode)) {
    updated = updated.replace(/^permissionMode:.*$/m, 'permissionMode: default');
  }

  // Add missing fields
  if (!fields.name || fields.name === '') {
    updated += `\nname: ${baseName}`;
  }
  if (!fields.description || fields.description === '') {
    updated += `\ndescription: 'Delegate to this agent when: [TODO - add description]'`;
  }
  if (!fields.model || fields.model === '') {
    if (!/^model:/m.test(updated)) updated += `\nmodel: claude-haiku-4-5`;
  }
  if (!fields.permissionMode || fields.permissionMode === '') {
    if (!/^permissionMode:/m.test(updated)) updated += `\npermissionMode: default`;
  }

  const newContent = content.replace(/^---\r?\n[\s\S]*?\r?\n---/, `---\n${updated}\n---`);
  writeFileSync(filePath, newContent, 'utf8');
}

function buildMinimalFrontmatter(name) {
  return [
    `name: ${name}`,
    `description: 'Delegate to this agent when: [TODO - add description]'`,
    `model: claude-haiku-4-5`,
    `permissionMode: default`,
  ].join('\n');
}

// ─── Main ────────────────────────────────────────────────────────────────────

let files;
try {
  files = readdirSync(AGENTS_DIR).filter(f => f.endsWith('.md') && f.toLowerCase() !== 'readme.md').sort();
} catch (err) {
  console.error(colorize(`❌ Cannot read agents directory: ${AGENTS_DIR}`, 'red'));
  process.exit(1);
}

if (!quiet) {
  console.log(`\nValidating ${files.length} agents in .claude/agents/\n`);
}

let totalOk = 0;
let totalErrors = 0;
let totalWarnings = 0;

for (const fileName of files) {
  const filePath = join(AGENTS_DIR, fileName);
  const { errors, warnings, fields, content } = validateAgent(filePath);

  if (errors.length === 0 && warnings.length === 0) {
    totalOk++;
    if (!quiet) {
      const model = fields.model || 'unknown';
      console.log(colorize(`✅ ${fileName} — OK (${model})`, 'green'));
    }
  } else if (errors.length > 0) {
    totalErrors++;
    console.log(colorize(`❌ ${fileName} — ERRORS:`, 'red'));
    for (const err of errors) {
      console.log(colorize(`   - ${err}`, 'red'));
    }
    for (const warn of warnings) {
      console.log(colorize(`   ⚠️  ${warn}`, 'yellow'));
    }
    if (fix) {
      fixAgent(filePath, fileName, fields, content);
      console.log(colorize(`   → Fixed`, 'green'));
    }
  } else {
    // Warnings only, no errors
    totalWarnings++;
    if (!quiet) {
      console.log(colorize(`⚠️  ${fileName} — WARNINGS:`, 'yellow'));
      for (const warn of warnings) {
        console.log(colorize(`   - ${warn}`, 'yellow'));
      }
    }
  }
}

const errWord = totalErrors !== 1 ? 'errors' : 'error';
const warnWord = totalWarnings !== 1 ? 'warnings' : 'warning';
const summary = `Summary: ${totalOk} OK, ${totalErrors} ${errWord}, ${totalWarnings} ${warnWord}`;
console.log(`\n${colorize(summary, 'bold')}\n`);

process.exit(totalErrors > 0 ? 1 : 0);
