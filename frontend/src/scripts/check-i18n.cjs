/**
 * i18n 翻译 key 完整性检查工具
 *
 * 用法: node frontend/src/scripts/check-i18n.cjs
 *
 * 检查中英文翻译文件之间是否有缺失的 key，并找出代码中使用了但翻译文件里没有定义的 key。
 * 已知的设计差异（中英文站各自独有的 key）会被自动排除。
 */
const fs = require('fs')
const path = require('path')

const ZH_PATH = path.join(__dirname, '../locales/zh/translation.json')
const EN_PATH = path.join(__dirname, '../locales/en/translation.json')
const SRC_DIR = path.join(__dirname, '..')

// 已知的设计差异：这些 key 是中英文站各自独有的，不需要对齐
// 中文站独有：使用 input.* / pricing.* 前缀 + 独立的 comparison 结构
// 英文站独有：使用 home.input.* / home.pricing.* 前缀 + 简化的 comparison 结构 + payment.*
const KNOWN_ZH_ONLY = [
  /^home\.comparison\.(auto_label|auto_result_|auto_step|free_llm|manual|services|tools|traditional)/,
  /^home\.pricing\.(buy_single|choose_semester|choose_yearly)$/,
  /^input\./,          // 中文站用顶层 input.*，英文站用 home.input.*
  /^pricing\./,        // 中文站用顶层 pricing.*，英文站用 home.pricing.*
  /^search_papers\./,  // 中文站 search_papers 页面翻译（结构一致，只是值不同）
]
const KNOWN_EN_ONLY = [
  /^home\.comparison\.(free_ai|autooverview|subtitle)/,
  /^home\.(sources|integrity|stats\.citations|footer\.databases)/,
  /^home\.hero\.(cta_button|cta_hint)$/,
  /^home\.input\.(alert_empty_topic|how_it_works)$/,
  /^payment\./,        // 英文站 Paddle/PayPal 弹窗专用
]

function flattenKeys(obj, prefix = '') {
  const keys = []
  for (const [key, value] of Object.entries(obj)) {
    const fullKey = prefix ? `${prefix}.${key}` : key
    if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
      keys.push(...flattenKeys(value, fullKey))
    } else {
      keys.push(fullKey)
    }
  }
  return keys
}

function loadJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, 'utf-8'))
}

function matchesAny(key, patterns) {
  return patterns.some(p => p.test(key))
}

// 递归扫描目录，找出所有 t() 调用中的 key
function findTKeysInCode(dir) {
  const keys = new Set()
  const tPattern = /\bt\s*\(\s*['"`]([^'"`]+)['"`]/g

  function walk(currentDir) {
    const entries = fs.readdirSync(currentDir, { withFileTypes: true })
    for (const entry of entries) {
      if (entry.name.startsWith('.') || entry.name === 'node_modules' || entry.name === 'scripts') continue
      const fullPath = path.join(currentDir, entry.name)
      if (entry.isDirectory()) {
        walk(fullPath)
      } else if (/\.(tsx?|jsx?)$/.test(entry.name)) {
        const content = fs.readFileSync(fullPath, 'utf-8')
        let match
        while ((match = tPattern.exec(content)) !== null) {
          const key = match[1]
          if (!key.includes('{{') && !key.includes('{')) {
            keys.add(key)
          }
        }
      }
    }
  }

  walk(dir)
  return keys
}

// Main
const zhData = loadJson(ZH_PATH)
const enData = loadJson(EN_PATH)

const zhKeys = new Set(flattenKeys(zhData))
const enKeys = new Set(flattenKeys(enData))

// 1. 中文有英文缺（排除已知差异）
const zhOnly = [...zhKeys]
  .filter(k => !enKeys.has(k))
  .filter(k => !matchesAny(k, KNOWN_ZH_ONLY))
  .sort()

// 2. 英文有中文缺（排除已知差异）
const enOnly = [...enKeys]
  .filter(k => !zhKeys.has(k))
  .filter(k => !matchesAny(k, KNOWN_EN_ONLY))
  .sort()

// 3. 代码中用到但两个翻译文件都没有的 key
const codeKeys = findTKeysInCode(SRC_DIR)
const missingInAll = [...codeKeys]
  .filter(k => !zhKeys.has(k) && !enKeys.has(k))
  .sort()

let hasIssue = false

if (zhOnly.length > 0) {
  hasIssue = true
  console.log('\n🔴 中文有，英文缺 (%d 个):', zhOnly.length)
  zhOnly.forEach(k => console.log(`   ${k}`))
}

if (enOnly.length > 0) {
  hasIssue = true
  console.log('\n🔴 英文有，中文缺 (%d 个):', enOnly.length)
  enOnly.forEach(k => console.log(`   ${k}`))
}

if (missingInAll.length > 0) {
  hasIssue = true
  console.log('\n🔴 代码中使用但翻译文件未定义 (%d 个):', missingInAll.length)
  missingInAll.forEach(k => console.log(`   ${k}`))
}

if (!hasIssue) {
  console.log('\n✅ 翻译 key 检查通过，无缺失。')
} else {
  console.log('')
}

process.exit(hasIssue ? 1 : 0)
