#!/usr/bin/env node
/**
 * i18n Key Check Script
 * Checks for missing keys between Chinese and English translation files
 */

import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

// Paths to translation files
const ZH_PATH = path.join(__dirname, '../src/locales/zh/translation.json')
const EN_PATH = path.join(__dirname, '../src/locales/en/translation.json')

console.log('🔍 Checking i18n translation keys...\n')

try {
  // Read and parse translation files
  const zhData = JSON.parse(fs.readFileSync(ZH_PATH, 'utf-8'))
  const enData = JSON.parse(fs.readFileSync(EN_PATH, 'utf-8'))

  // Collect all keys with their paths
  const zhKeys = new Set()
  const enKeys = new Set()
  const zhKeyPaths = {}
  const enKeyPaths = {}

  function collectKeys(obj, prefix = '', keySet, keyPaths) {
    for (const [key, value] of Object.entries(obj)) {
      const fullKey = prefix ? `${prefix}.${key}` : key
      if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
        collectKeys(value, fullKey, keySet, keyPaths)
      } else {
        keySet.add(fullKey)
        keyPaths[fullKey] = value
      }
    }
  }

  collectKeys(zhData, '', zhKeys, zhKeyPaths)
  collectKeys(enData, '', enKeys, enKeyPaths)

  console.log(`📊 Statistics:`)
  console.log(`   Chinese keys: ${zhKeys.size}`)
  console.log(`   English keys: ${enKeys.size}`)
  console.log()

  // Find missing keys
  const missingInEn = [...zhKeys].filter(k => !enKeys.has(k))
  const missingInZh = [...enKeys].filter(k => !zhKeys.has(k))

  let hasErrors = false

  if (missingInEn.length > 0) {
    console.log('❌ Keys missing in English translation:')
    missingInEn.forEach(key => {
      console.log(`   - ${key}`)
      console.log(`     Current Chinese: "${zhKeyPaths[key]}"`)
    })
    console.log()
    hasErrors = true
  }

  if (missingInZh.length > 0) {
    console.log('❌ Keys missing in Chinese translation:')
    missingInZh.forEach(key => {
      console.log(`   - ${key}`)
      console.log(`     Current English: "${enKeyPaths[key]}"`)
    })
    console.log()
    hasErrors = true
  }

  if (!hasErrors) {
    console.log('✅ All keys are present in both translations!')
    process.exit(0)
  } else {
    process.exit(1)
  }

} catch (error) {
  console.error('❌ Error:', error.message)
  process.exit(1)
}
