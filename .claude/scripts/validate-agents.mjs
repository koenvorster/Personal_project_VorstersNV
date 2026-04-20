#!/usr/bin/env node
/**
 * validate-agents.mjs — VorstersNV
 *
 * Valideert alle .claude/agents/*.md bestanden op correcte Claude Code frontmatter.
 * Controleert: verplichte velden aanwezig, ongeldige velden afwezig, waarden geldig.
 *
 * Gebruik:
 *   node .claude/scripts/validate-agents.mjs
 *   node .claude/scripts/validate-agents.mjs --fix    # Toont suggesties
 *   node .claude/scripts/validate-agents.mjs --quiet  # Alleen fouten
 */

import { readdirSync, readFileSync } from 'fs'
import { join, relative } from 'path'

const args = process.argv.slice(2)
const FIX_MODE = args.includes('--fix')
const QUIET = args.includes('--quiet')

// Claude Code spec — alleen deze velden zijn geldig in frontmatter
const VALID_FIELDS = new Set(['name', 'description', 'model', 'permissionMode', 'maxTurns', 'memory', 'tools', 'isolation'])

// Velden die vroeger gebruikt werden maar nu ongeldig zijn
const INVALID_FIELDS = new Set(['type', 'version', 'audience', 'role', 'language', 'user_invocable', 'capability', 'platforms', 'risk', 'category'])

const VALID_MODELS = ['haiku', 'sonnet', 'opus', 'claude-haiku-4-5', 'claude-sonnet-4-5', 'claude-opus-4-5']
const VALID_PERMISSION_MODES = ['auto', 'plan', 'default']
const VALID_MEMORY = ['project', 'none']
const VALID_ISOLATION = ['worktree', 'none']

const AGENTS_DIR = join(process.cwd(), '.claude', 'agents')
const ROOT = process.cwd()

let files
try {
  files = readdirSync(AGENTS_DIR).filter(f => f.endsWith('.md'))
} catch {
  console.error(`❌ Map niet gevonden: ${AGENTS_DIR}`)
  process.exit(1)
}

let totalErrors = 0
let totalWarnings = 0
const results = []

for (const file of files) {
  const filePath = join(AGENTS_DIR, file)
  const relPath = relative(ROOT, filePath)
  const content = readFileSync(filePath, 'utf8')
  const errors = []
  const warnings = []

  // Normalize line endings (Windows CRLF → LF)
  const normalizedContent = content.replace(/\r\n/g, '\n')

  // Parse frontmatter
  const fmMatch = normalizedContent.match(/^---\n([\s\S]*?)\n---/)
  if (!fmMatch) {
    errors.push('Geen frontmatter gevonden (verwacht: --- ... ---)')
    results.push({ file: relPath, errors, warnings, hasFrontmatter: false })
    totalErrors++
    continue
  }

  const fmRaw = fmMatch[1]
  const fields = {}

  // Simpele YAML-parser voor key: value (geen nested objects voor validatie)
  for (const line of fmRaw.split('\n')) {
    const m = line.match(/^(\w+)\s*:\s*(.*)$/)
    if (m) fields[m[1].trim()] = m[2].trim()
  }

  // Controleer ongeldige velden
  for (const key of Object.keys(fields)) {
    if (INVALID_FIELDS.has(key)) {
      errors.push(`Ongeldig veld: '${key}' — niet ondersteund door Claude Code spec`)
    } else if (!VALID_FIELDS.has(key)) {
      warnings.push(`Onbekend veld: '${key}' — controleer de Claude Code spec`)
    }
  }

  // Verplicht: name
  if (!fields.name) {
    errors.push("Verplicht veld ontbreekt: 'name'")
  }

  // Verplicht: description (moet "Use when:" of "Delegate" bevatten)
  if (!fields.description) {
    errors.push("Verplicht veld ontbreekt: 'description'")
  } else {
    const descBlock = fmRaw.match(/description:\s*>([\s\S]*?)(?=\n\w|\n---)/)?.[1] || fields.description
    if (!descBlock.toLowerCase().includes('use when') && !descBlock.toLowerCase().includes('delegate')) {
      warnings.push("'description' zou een 'Use when:' of 'Delegate to this agent when:' clausule moeten bevatten")
    }
  }

  // Verplicht: model
  if (!fields.model) {
    warnings.push("'model' ontbreekt — Claude zal standaard model gebruiken")
  } else if (!VALID_MODELS.some(m => fields.model.includes(m))) {
    warnings.push(`Onbekend model: '${fields.model}' — geldig: ${VALID_MODELS.join(', ')}`)
  }

  // permissionMode
  if (fields.permissionMode && !VALID_PERMISSION_MODES.includes(fields.permissionMode)) {
    errors.push(`Ongeldige permissionMode: '${fields.permissionMode}' — geldig: ${VALID_PERMISSION_MODES.join(', ')}`)
  }

  // maxTurns
  if (!fields.maxTurns) {
    warnings.push("'maxTurns' ontbreekt — zonder limiet kan agent oneindig lopen")
  } else if (isNaN(Number(fields.maxTurns)) || Number(fields.maxTurns) < 1 || Number(fields.maxTurns) > 100) {
    warnings.push(`'maxTurns: ${fields.maxTurns}' — verwacht getal tussen 1-100`)
  }

  // memory
  if (fields.memory && !VALID_MEMORY.includes(fields.memory)) {
    warnings.push(`Onbekende memory waarde: '${fields.memory}' — geldig: ${VALID_MEMORY.join(', ')}`)
  }

  // isolation
  if (fields.isolation && !VALID_ISOLATION.includes(fields.isolation)) {
    errors.push(`Ongeldige isolation waarde: '${fields.isolation}' — geldig: ${VALID_ISOLATION.join(', ')}`)
  }

  results.push({ file: relPath, fields, errors, warnings, hasFrontmatter: true })
  totalErrors += errors.length
  totalWarnings += warnings.length
}

// Output
console.log(`\n🔍 Agent Validatie — VorstersNV\n${'─'.repeat(50)}`)
console.log(`   Bestanden gevonden: ${files.length}`)
console.log(`   Fouten: ${totalErrors}  Waarschuwingen: ${totalWarnings}\n`)

let passCount = 0
let failCount = 0

for (const { file, errors, warnings } of results) {
  const ok = errors.length === 0
  if (ok) passCount++
  else failCount++

  if (QUIET && ok) continue

  const icon = ok ? '✅' : '❌'
  const warnIcon = warnings.length > 0 ? ` ⚠️ ${warnings.length}` : ''
  console.log(`${icon} ${file}${warnIcon}`)

  for (const err of errors) {
    console.log(`     🔴 ${err}`)
  }

  if (!QUIET || errors.length > 0) {
    for (const warn of warnings) {
      console.log(`     🟡 ${warn}`)
    }
  }

  if (FIX_MODE && errors.length > 0) {
    console.log(`\n     💡 Suggestie — correcte frontmatter:`)
    console.log(`     ---`)
    console.log(`     name: ${file.replace('.claude/agents/', '').replace('.md', '')}`)
    console.log(`     description: >`)
    console.log(`       Use when: [beschrijf hier wanneer deze agent te gebruiken]`)
    console.log(`     model: sonnet`)
    console.log(`     permissionMode: plan`)
    console.log(`     maxTurns: 20`)
    console.log(`     ---\n`)
  }
}

console.log(`\n${'─'.repeat(50)}`)
console.log(`   ✅ ${passCount} geslaagd  |  ❌ ${failCount} gefaald  |  ⚠️ ${totalWarnings} waarschuwingen`)

if (totalErrors > 0) {
  console.log(`\n   ℹ️  Gebruik --fix voor herstelsugesties`)
  console.log(`   ℹ️  Claude Code spec: https://docs.anthropic.com/claude-code/agents\n`)
  process.exit(1)
} else {
  console.log(`\n   🎉 Alle agents zijn valide!\n`)
}
