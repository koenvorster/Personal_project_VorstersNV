/**
 * Setup script – maakt alle benodigde mappen aan voor de Java backend.
 * Gebruik: node scripts/setup_java_dirs.js
 */
const fs = require('fs')
const path = require('path')

const base = path.join(__dirname, '..', 'backend', 'src', 'main')

const dirs = [
  'resources/db/migration',
  'java/dev/koenvorsters/health',
  'java/dev/koenvorsters/category',
  'java/dev/koenvorsters/category/dto',
  'java/dev/koenvorsters/product',
  'java/dev/koenvorsters/product/dto',
  'java/dev/koenvorsters/customer',
  'java/dev/koenvorsters/order',
  'java/dev/koenvorsters/order/dto',
  'java/dev/koenvorsters/inventory',
  'java/dev/koenvorsters/inventory/dto',
  'java/dev/koenvorsters/dashboard',
  'java/dev/koenvorsters/dashboard/dto',
]

let created = 0
for (const dir of dirs) {
  const full = path.join(base, dir)
  if (!fs.existsSync(full)) {
    fs.mkdirSync(full, { recursive: true })
    console.log(`✅ ${dir}`)
    created++
  } else {
    console.log(`⏭  ${dir} (bestaat al)`)
  }
}

console.log(`\n${created} map(pen) aangemaakt.`)
