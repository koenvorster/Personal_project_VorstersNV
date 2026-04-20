#!/usr/bin/env node
/**
 * check-env.mjs — validate .env against .env.example
 * Run: node .claude/scripts/check-env.mjs
 *
 * Exit code 0 = OK, Exit code 1 = missing variables found
 */

import { readFileSync, existsSync } from "fs"
import { resolve } from "path"

const ROOT = resolve(import.meta.dirname, "../..")

function parseEnvKeys(filePath) {
  if (!existsSync(filePath)) return new Set()
  return new Set(
    readFileSync(filePath, "utf-8")
      .split("\n")
      .filter((line) => line.trim() && !line.startsWith("#") && line.includes("="))
      .map((line) => line.split("=")[0].trim())
  )
}

const examplePath = resolve(ROOT, ".env.example")
const envPath = resolve(ROOT, ".env")

if (!existsSync(examplePath)) {
  console.log("⚠️  No .env.example found — skipping check")
  process.exit(0)
}

const required = parseEnvKeys(examplePath)
const present = parseEnvKeys(envPath)

const missing = [...required].filter((k) => !present.has(k))
const extra = [...present].filter((k) => !required.has(k))

if (missing.length === 0) {
  console.log(`✅ .env is complete (${required.size} variables)`)
} else {
  console.error(`❌ Missing ${missing.length} required environment variable(s):`)
  missing.forEach((k) => console.error(`   • ${k}`))
  console.error(`\n   Copy .env.example to .env and fill in the missing values.`)
}

if (extra.length > 0) {
  console.log(`ℹ️  Extra variables in .env (not in .env.example): ${extra.join(", ")}`)
}

process.exit(missing.length > 0 ? 1 : 0)
