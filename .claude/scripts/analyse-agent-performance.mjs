#!/usr/bin/env node
// .claude/scripts/analyse-agent-performance.mjs
import { readFileSync, readdirSync, writeFileSync, mkdirSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const AGENTS_DIR = join(__dirname, '..', 'agents');
const REPORTS_DIR = join(__dirname, '..', 'reports');
const REPORT_FILE = join(REPORTS_DIR, 'agent-performance.json');

const PREFERRED_MODELS = ['claude-haiku-4-5', 'claude-sonnet-4-5'];
const PREMIUM_MODELS   = ['claude-opus-4-5', 'claude-opus-4-6'];
// bodyScore: any 3+ level-2 headings in the body = full score (content is structured)

const WEIGHTS = { name: 0.20, description: 0.25, model: 0.20, maxTurns: 0.15, body: 0.20 };
const THRESHOLD = 0.7;

const COLORS = {
  reset: '\x1b[0m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  cyan: '\x1b[36m',
  bold: '\x1b[1m',
};

function c(text, ...styles) {
  return styles.map(s => COLORS[s]).join('') + text + COLORS.reset;
}

// Reuse the same frontmatter parser pattern from validate-agents.mjs
function parseFrontmatter(content) {
  const match = content.match(/^---\r?\n([\s\S]*?)\r?\n---/);
  if (!match) return { fields: {} };

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
      const parts = [];
      i++;
      while (i < lines.length && (lines[i].startsWith('  ') || lines[i] === '')) {
        parts.push(lines[i].trim());
        i++;
      }
      fields[key] = parts.filter(Boolean).join(' ').trim();
    } else if (value === '|') {
      const parts = [];
      i++;
      while (i < lines.length && (lines[i].startsWith('  ') || lines[i] === '')) {
        parts.push(lines[i].startsWith('  ') ? lines[i].slice(2) : '');
        i++;
      }
      fields[key] = parts.join('\n').trim();
    } else if (value === '') {
      const items = [];
      i++;
      while (i < lines.length && /^\s+-\s+/.test(lines[i])) {
        items.push(lines[i].replace(/^\s+-\s+/, '').trim());
        i++;
      }
      fields[key] = items.length > 0 ? items : null;
    } else {
      fields[key] = value.replace(/^['"]|['"]$/g, '');
      i++;
    }
  }

  return { fields };
}

function scoreAgent(fileName, content) {
  const { fields } = parseFrontmatter(content);

  // nameScore
  const nameScore = (fields.name && fields.name.trim()) ? 1.0 : 0;

  // descriptionScore
  const desc = fields.description;
  let descriptionScore = 0;
  if (desc && typeof desc === 'string' && desc.trim()) {
    descriptionScore = desc.trim().startsWith('Delegate to this agent when:') ? 1.0 : 0.5;
  }

  // modelScore: preferred = 1.0, premium (opus) = 1.0, unknown = 0.5
  const model = fields.model;
  let modelScore = 0;
  if (model && model.trim()) {
    if (PREFERRED_MODELS.includes(model.trim())) modelScore = 1.0;
    else if (PREMIUM_MODELS.includes(model.trim())) modelScore = 1.0;
    else modelScore = 0.5;
  }

  // maxTurnsScore: 3-30 is acceptable (complex orchestrators need up to 30 turns)
  const mt = fields.maxTurns !== undefined ? Number(fields.maxTurns) : NaN;
  let maxTurnsScore = 0;
  if (!isNaN(mt)) {
    maxTurnsScore = (mt >= 3 && mt <= 30) ? 1.0 : 0.5;
  }

  // bodyScore: count ## headings in the body — 3+ = full score, 1-2 = partial
  const bodyContent = content.replace(/^---[\s\S]*?---/, '');
  const sectionsFound = (bodyContent.match(/^## .+/gm) || []).length;
  const bodyScore = sectionsFound >= 3 ? 1.0 : sectionsFound >= 1 ? 0.5 : 0;

  const overallScore =
    WEIGHTS.name        * nameScore +
    WEIGHTS.description * descriptionScore +
    WEIGHTS.model       * modelScore +
    WEIGHTS.maxTurns    * maxTurnsScore +
    WEIGHTS.body        * bodyScore;

  return {
    file: fileName,
    name: fields.name || null,
    model: model || null,
    maxTurns: isNaN(mt) ? null : mt,
    scores: {
      nameScore: round(nameScore),
      descriptionScore: round(descriptionScore),
      modelScore: round(modelScore),
      maxTurnsScore: round(maxTurnsScore),
      bodyScore: round(bodyScore),
      overallScore: round(overallScore),
    },
    sectionsFound,
    belowThreshold: overallScore < THRESHOLD,
  };
}

function round(n) {
  return Math.round(n * 1000) / 1000;
}

// ─── Main ────────────────────────────────────────────────────────────────────

let files;
try {
  files = readdirSync(AGENTS_DIR)
    .filter(f => f.endsWith('.md') && f.toLowerCase() !== 'readme.md')
    .sort();
} catch (err) {
  console.error(c(`❌ Cannot read agents directory: ${AGENTS_DIR}`, 'red'));
  process.exit(1);
}

console.log(c(`\n📊 Agent Performance Analyser`, 'bold', 'cyan'));
console.log(c(`   Analysing ${files.length} agents in .claude/agents/\n`, 'cyan'));

const results = files.map(fileName => {
  const filePath = join(AGENTS_DIR, fileName);
  const content = readFileSync(filePath, 'utf8');
  return scoreAgent(fileName, content);
});

// ─── Aggregates ──────────────────────────────────────────────────────────────

const avgScore = round(results.reduce((s, r) => s + r.scores.overallScore, 0) / results.length);

const modelBreakdown = {};
for (const r of results) {
  const key = r.model || 'missing';
  modelBreakdown[key] = (modelBreakdown[key] || 0) + 1;
}

const belowThreshold = results.filter(r => r.belowThreshold);
const sorted = [...results].sort((a, b) => b.scores.overallScore - a.scores.overallScore);
const topPerformer = sorted[0];
const worstPerformer = sorted[sorted.length - 1];

// ─── Console Output ───────────────────────────────────────────────────────────

for (const r of results) {
  const score = r.scores.overallScore;
  const bar = '█'.repeat(Math.round(score * 10)).padEnd(10, '░');
  const color = score >= THRESHOLD ? 'green' : score >= 0.5 ? 'yellow' : 'red';
  const flag = r.belowThreshold ? c(' ⚠ below threshold', 'yellow') : '';
  console.log(`  ${c(r.file.padEnd(38), 'bold')} ${c(`[${bar}]`, color)} ${c(score.toFixed(3), color)}${flag}`);
}

console.log('');
console.log(c('─'.repeat(60), 'bold'));
console.log(c(`  Total agents:        ${results.length}`, 'bold'));
console.log(c(`  Average score:       ${avgScore.toFixed(3)}`, avgScore >= THRESHOLD ? 'green' : 'red'));
console.log(`  Below threshold:     ${belowThreshold.length} agent(s) < ${THRESHOLD}`);
console.log(`  Top performer:       ${c(topPerformer.file, 'green')} (${topPerformer.scores.overallScore.toFixed(3)})`);
console.log(`  Worst performer:     ${c(worstPerformer.file, 'red')} (${worstPerformer.scores.overallScore.toFixed(3)})`);
console.log('');
console.log('  Model breakdown:');
for (const [model, count] of Object.entries(modelBreakdown).sort()) {
  console.log(`    ${model.padEnd(30)} ${count} agent(s)`);
}
console.log(c('─'.repeat(60), 'bold'));

if (belowThreshold.length > 0) {
  console.log(c(`\n  ⚠️  Agents below threshold (${THRESHOLD}):`, 'yellow'));
  for (const r of belowThreshold) {
    console.log(c(`    - ${r.file} (${r.scores.overallScore.toFixed(3)})`, 'yellow'));
  }
}

// ─── JSON Report ─────────────────────────────────────────────────────────────

mkdirSync(REPORTS_DIR, { recursive: true });

const report = {
  generatedAt: new Date().toISOString(),
  summary: {
    totalAgents: results.length,
    averageScore: avgScore,
    threshold: THRESHOLD,
    passedThreshold: avgScore >= THRESHOLD,
    agentsBelowThreshold: belowThreshold.length,
    topPerformer: { file: topPerformer.file, score: topPerformer.scores.overallScore },
    worstPerformer: { file: worstPerformer.file, score: worstPerformer.scores.overallScore },
    modelBreakdown,
  },
  weights: WEIGHTS,
  agents: results,
};

writeFileSync(REPORT_FILE, JSON.stringify(report, null, 2), 'utf8');
console.log(c(`\n  ✅ Report saved to .claude/reports/agent-performance.json\n`, 'green'));

process.exit(avgScore >= THRESHOLD ? 0 : 1);
