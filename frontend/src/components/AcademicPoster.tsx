/**
 * Academic Poster Component
 * Generates a shareable academic poster image from review data.
 * Uses html2canvas for screenshot, qrcode for QR generation.
 */
import { useEffect, useRef } from 'react'
import QRCode from 'qrcode'
import './AcademicPoster.css'

export type PosterTheme = 'cosmic' | 'gold' | 'minimal' | 'forest' | 'chinese'

interface Paper {
  title: string
  authors?: string[]
  year?: number
  abstract?: string
  is_english?: boolean
}

interface ThemeConfig {
  bgGradient: string
  textColor: string
  textSecondary: string
  textMuted: string
  accentColor: string
  accentGradient: string
  cardBg: string
  cardBorder: string
  decoBg: string
  dividerColor: string
  wordCloudColors: string[]
  qrDark: string
  qrLight: string
  brandIcon: string
}

const THEMES: Record<PosterTheme, ThemeConfig> = {
  cosmic: {
    bgGradient: 'linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%)',
    textColor: '#ffffff',
    textSecondary: 'rgba(255,255,255,0.9)',
    textMuted: 'rgba(255,255,255,0.7)',
    accentColor: '#fbbf24',
    accentGradient: 'linear-gradient(135deg, #fbbf24, #f59e0b)',
    cardBg: 'rgba(255,255,255,0.1)',
    cardBorder: 'rgba(255,255,255,0.15)',
    decoBg: 'rgba(255,255,255,0.03)',
    dividerColor: 'rgba(255,255,255,0.15)',
    wordCloudColors: ['#fbbf24','#f59e0b','#fb923c','#f97316','#a78bfa','#8b5cf6','#60a5fa','#3b82f6','#34d399','#10b981','#f472b6','#ec4899','#e2e8f0','#cbd5e1'],
    qrDark: '#1a1a2e',
    qrLight: '#ffffff',
    brandIcon: '📚',
  },
  gold: {
    bgGradient: 'linear-gradient(160deg, #0a0a0a 0%, #1a1a1a 40%, #111111 100%)',
    textColor: '#ffffff',
    textSecondary: 'rgba(255,255,255,0.9)',
    textMuted: 'rgba(255,255,255,0.6)',
    accentColor: '#d4a853',
    accentGradient: 'linear-gradient(135deg, #d4a853, #c9a94e)',
    cardBg: 'rgba(212,168,83,0.08)',
    cardBorder: 'rgba(212,168,83,0.2)',
    decoBg: 'rgba(212,168,83,0.03)',
    dividerColor: 'rgba(212,168,83,0.2)',
    wordCloudColors: ['#d4a853','#c9a94e','#e8c878','#f0d890','#f5e6b8','#b8943e','#a07830','#d4a853','#e8d5a8','#c4a35a','#f0c040','#dab855','#e0c070','#c8a848'],
    qrDark: '#0a0a0a',
    qrLight: '#ffffff',
    brandIcon: '🎓',
  },
  minimal: {
    bgGradient: 'linear-gradient(180deg, #f8f9fa 0%, #ffffff 50%, #f0f1f3 100%)',
    textColor: '#1a1a2e',
    textSecondary: '#374151',
    textMuted: '#6b7280',
    accentColor: '#3b82f6',
    accentGradient: 'linear-gradient(135deg, #3b82f6, #2563eb)',
    cardBg: 'rgba(59,130,246,0.06)',
    cardBorder: 'rgba(59,130,246,0.15)',
    decoBg: 'rgba(59,130,246,0.04)',
    dividerColor: 'rgba(0,0,0,0.08)',
    wordCloudColors: ['#3b82f6','#2563eb','#60a5fa','#1d4ed8','#6366f1','#4f46e5','#0ea5e9','#0284c7','#14b8a6','#059669','#8b5cf6','#7c3aed','#94a3b8','#475569'],
    qrDark: '#1a1a2e',
    qrLight: '#ffffff',
    brandIcon: '📖',
  },
  forest: {
    bgGradient: 'linear-gradient(135deg, #0a1a0f 0%, #1a3a2a 50%, #0d2818 100%)',
    textColor: '#ffffff',
    textSecondary: 'rgba(255,255,255,0.9)',
    textMuted: 'rgba(255,255,255,0.65)',
    accentColor: '#4ade80',
    accentGradient: 'linear-gradient(135deg, #4ade80, #22c55e)',
    cardBg: 'rgba(74,222,128,0.08)',
    cardBorder: 'rgba(74,222,128,0.15)',
    decoBg: 'rgba(74,222,128,0.03)',
    dividerColor: 'rgba(74,222,128,0.15)',
    wordCloudColors: ['#4ade80','#22c55e','#86efac','#16a34a','#a3e635','#65a30d','#fbbf24','#f59e0b','#34d399','#10b981','#6ee7b7','#a7f3d0','#d4fc79','#bef264'],
    qrDark: '#0a1a0f',
    qrLight: '#ffffff',
    brandIcon: '🌿',
  },
  chinese: {
    bgGradient: 'linear-gradient(135deg, #2d0a0a 0%, #4a1a1a 50%, #3d0f0f 100%)',
    textColor: '#ffffff',
    textSecondary: 'rgba(255,255,255,0.9)',
    textMuted: 'rgba(255,255,255,0.65)',
    accentColor: '#fbbf24',
    accentGradient: 'linear-gradient(135deg, #fbbf24, #f59e0b)',
    cardBg: 'rgba(251,191,36,0.08)',
    cardBorder: 'rgba(251,191,36,0.15)',
    decoBg: 'rgba(251,191,36,0.03)',
    dividerColor: 'rgba(251,191,36,0.15)',
    wordCloudColors: ['#fbbf24','#f59e0b','#ef4444','#dc2626','#f87171','#b91c1c','#fca5a5','#fde68a','#fcd34d','#fb923c','#f97316','#e2e8f0','#fecaca','#fda4af'],
    qrDark: '#2d0a0a',
    qrLight: '#ffffff',
    brandIcon: '🏮',
  },
}

interface PosterProps {
  title: string
  content: string
  papers: Paper[]
  createdAt?: string
  durationSeconds?: number
  language?: 'zh' | 'en'
  shareUrl?: string
  coreFindings: string[]
  preview?: boolean
  theme?: PosterTheme
  i18n: {
    coreFindings: string
    papersLabel: string
    durationLabel: string
    dateLabel: string
    scanToRead: string
    poweredBy: string
    brandName: string
  }
}

const EN_STOP_WORDS = new Set([
  'a', 'an', 'the', 'and', 'or', 'but', 'not', 'no', 'nor', 'so', 'yet',
  'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'as', 'up',
  'is', 'are', 'was', 'were', 'be', 'been', 'being', 'am', 'do', 'does',
  'did', 'have', 'has', 'had', 'having', 'will', 'would', 'could', 'should',
  'shall', 'may', 'might', 'must', 'can', 'need', 'dare', 'ought',
  'this', 'that', 'these', 'those', 'it', 'its', 'we', 'our', 'us',
  'they', 'them', 'their', 'he', 'she', 'him', 'her', 'his', 'you', 'your',
  'which', 'who', 'whom', 'whose', 'what', 'where', 'when', 'how', 'why',
  'all', 'each', 'every', 'both', 'few', 'many', 'some', 'any', 'more',
  'most', 'other', 'another', 'such', 'than', 'too', 'very', 'just',
  'about', 'above', 'after', 'before', 'below', 'between', 'among',
  'through', 'during', 'until', 'while', 'since', 'into', 'onto',
  'over', 'under', 'again', 'further', 'then', 'once', 'here', 'there',
  'also', 'only', 'own', 'same', 'well', 'much', 'still', 'even',
  'if', 'because', 'although', 'though', 'whether', 'unless', 'however',
  'therefore', 'thus', 'hence', 'moreover', 'furthermore', 'nevertheless',
  'i', 'me', 'my', 'myself', 'yourself', 'himself', 'herself', 'itself',
  'people', 'person', 'way', 'thing', 'things', 'something', 'anything',
  'nothing', 'everything', 'one', 'two', 'three', 'first', 'second',
  'new', 'old', 'good', 'great', 'different', 'important', 'possible',
  'based', 'using', 'used', 'use', 'via', 'like', 'within', 'without',
  'across', 'along', 'around', 'against', 'according', 'due',
  'study', 'paper', 'article', 'review', 'research', 'work', 'previous',
  'propose', 'proposed', 'present', 'presented', 'provide', 'provided',
  'show', 'shown', 'shows', 'demonstrate', 'demonstrated', 'observe',
  'observed', 'report', 'reported', 'describe', 'described', 'discuss',
  'find', 'found', 'found', 'consider', 'considered', 'suggest', 'suggested',
  'approach', 'method', 'methods', 'model', 'models', 'framework',
  'result', 'results', 'performance', 'effect', 'effects', 'impact',
  'significant', 'significantly', 'related', 'relative', 'respectively',
  'et', 'al', 'de', 'la', 'le', 'el', 'en',
])

const ZH_STOP_WORDS = new Set([
  '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都',
  '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你',
  '会', '着', '没有', '看', '好', '自己', '这', '那', '他', '她',
  '它', '们', '与', '及', '对', '中', '等', '被', '从', '把',
  '可以', '通过', '进行', '提出', '基于', '利用', '研究', '方法',
  '结果', '分析', '表明', '本文', '该', '其', '以及', '一种',
  '虽然', '但是', '因为', '所以', '如果', '那么', '而且', '或者',
  '同时', '为了', '关于', '随着', '根据', '由于', '目前', '现状',
  '问题', '情况', '方面', '角度', '能够', '使得', '从而', '进而',
  '不仅', '而且', '对于', '之间', '过程', '机制', '作用', '不同',
  '较为', '较为', '相对', '一定', '已经', '仍然', '依然', '首先',
  '其次', '最后', '总之', '综上', '因此', '此外', '另外', '然后',
  '总之', '并', '且', '个', '之', '而', '以', '于', '将', '给',
  '更', '最', '还', '让', '当', '能', '些', '个', '所', '地',
  '得', '着', '过', '吗', '呢', '吧', '啊', '呀',
  'ng', 'nd', 'he', 'de', 'al', 'et', 'en', 'es', 'ed', 'er',
  'te', 'in', 'on', 'at', 'or', 'by', 'to', 'of', 'is', 'it',
])

function extractKeywords(papers: Paper[], _lang: 'zh' | 'en'): Map<string, number> {
  const titles = papers.map(p => p.title).filter(Boolean)
  const abstracts = papers.map(p => p.abstract).filter(Boolean)

  // Detect if content is primarily English
  const allText = [...titles, ...abstracts].join(' ')
  const isEnglish = (allText.match(/[一-鿿]/g) || []).length < allText.length * 0.15

  const freq = new Map<string, number>()

  if (isEnglish) {
    // English: extract meaningful 2-3 word phrases from titles, plus single academic terms
    const titleTexts = titles.map(t => t.toLowerCase().replace(/[^a-z0-9\s-]/g, ' '))

    // Extract bigrams and trigrams from titles
    for (const text of titleTexts) {
      const words = text.split(/\s+/).filter(w => w.length >= 2)
      // Bigrams
      for (let i = 0; i < words.length - 1; i++) {
        const w1 = words[i], w2 = words[i + 1]
        if (!EN_STOP_WORDS.has(w1) && !EN_STOP_WORDS.has(w2) && w1.length >= 3 && w2.length >= 3) {
          const phrase = `${w1} ${w2}`
          freq.set(phrase, (freq.get(phrase) || 0) + 2) // titles count more
        }
      }
      // Trigrams
      for (let i = 0; i < words.length - 2; i++) {
        const parts = [words[i], words[i + 1], words[i + 2]]
        const stopCount = parts.filter(w => EN_STOP_WORDS.has(w)).length
        if (stopCount === 0) {
          const phrase = parts.join(' ')
          freq.set(phrase, (freq.get(phrase) || 0) + 3) // trigrams from titles count even more
        }
      }
      // Single words from titles (higher weight)
      for (const w of words) {
        if (w.length >= 4 && !EN_STOP_WORDS.has(w)) {
          freq.set(w, (freq.get(w) || 0) + 1)
        }
      }
    }

    // Also extract from abstracts (lower weight)
    for (const abs of abstracts.slice(0, 10)) {
      const words = abs!.toLowerCase().replace(/[^a-z0-9\s-]/g, ' ').split(/\s+/)
      for (let i = 0; i < words.length - 1; i++) {
        const w1 = words[i], w2 = words[i + 1]
        if (!EN_STOP_WORDS.has(w1) && !EN_STOP_WORDS.has(w2) && w1.length >= 3 && w2.length >= 3) {
          const phrase = `${w1} ${w2}`
          freq.set(phrase, (freq.get(phrase) || 0) + 1)
        }
      }
    }
  } else {
    // Chinese: extract from titles using punctuation-aware segmentation
    for (const title of titles) {
      // Split by non-Chinese chars and common delimiters
      const segments = title.split(/[^一-鿿A-Za-z0-9]/).filter(s => s.length >= 2)
      for (const seg of segments) {
        // Extract 2-6 char sub-phrases
        for (let len = 2; len <= Math.min(6, seg.length); len++) {
          for (let i = 0; i <= seg.length - len; i++) {
            const phrase = seg.substring(i, i + len)
            if (!ZH_STOP_WORDS.has(phrase)) {
              freq.set(phrase, (freq.get(phrase) || 0) + 2)
            }
          }
        }
      }
    }

    // Also extract from abstracts
    for (const abs of abstracts.slice(0, 10)) {
      const segments = abs!.split(/[^一-鿿A-Za-z0-9]/).filter(s => s.length >= 2)
      for (const seg of segments) {
        for (let len = 2; len <= Math.min(4, seg.length); len++) {
          for (let i = 0; i <= seg.length - len; i++) {
            const phrase = seg.substring(i, i + len)
            if (!ZH_STOP_WORDS.has(phrase)) {
              freq.set(phrase, (freq.get(phrase) || 0) + 1)
            }
          }
        }
      }
    }
  }

  // Sort by frequency, prefer longer phrases
  const scored = [...freq.entries()]
    .filter(([, count]) => count >= 1) // Lower threshold to get more keywords
    .map(([w, count]) => [w, count + w.length * 0.1] as [string, number])
    .sort((a, b) => b[1] - a[1])

  const result = new Map<string, number>()
  const seen = new Set<string>()
  for (const [w] of scored) {
    const word = w
    // Skip if dominated by a longer phrase that already exists
    let dominated = false
    for (const s of seen) {
      if (s !== word && (s.includes(word) || word.includes(s))) {
        // Keep the longer one if scores are similar
        if (s.includes(word) && freq.get(s)! >= freq.get(word)! * 0.3) {
          dominated = true
          break
        }
        if (word.includes(s) && freq.get(word)! < freq.get(s)! * 3) {
          dominated = true
          break
        }
      }
    }
    if (!dominated) {
      result.set(word, freq.get(word)!)
      seen.add(word)
    }
    if (result.size >= 40) break // Collect more to ensure we have enough
  }
  return result
}

function drawWordCloud(canvas: HTMLCanvasElement, keywords: Map<string, number>, colors: string[]) {
  const ctx = canvas.getContext('2d')!
  const width = canvas.width
  const height = canvas.height

  ctx.clearRect(0, 0, width, height)

  const entries = [...keywords.entries()]
  if (entries.length === 0) return

  // Take top 24 keywords for clarity
  const topEntries = entries.slice(0, 24)
  const maxFreq = topEntries[0][1]
  const placed: { x: number; y: number; w: number; h: number }[] = []

  const centerX = width / 2
  const centerY = height / 2

  for (let i = 0; i < topEntries.length; i++) {
    const [word, freq] = topEntries[i]
    const ratio = freq / maxFreq
    const fontSize = Math.round(16 + ratio * 28)
    const color = colors[i % colors.length]

    ctx.font = `${fontSize}px 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', Arial, sans-serif`
    const metrics = ctx.measureText(word)
    const textW = metrics.width + 12
    const textH = fontSize + 10

    // Try to place in spiral pattern from center
    let placedOk = false
    const maxAttempts = 500
    const angleStep = 0.4

    let bestX = 0, bestY = 0, minOverlap = Infinity

    for (let attempt = 0; attempt < maxAttempts; attempt++) {
      // Spiral outward
      const angle = attempt * angleStep
      const radius = 3 + attempt * 1.2
      const x = centerX + Math.cos(angle) * radius - textW / 2
      const y = centerY + Math.sin(angle) * radius + fontSize / 2

      // Check boundaries
      if (x < 5 || x + textW > width - 5 || y - textH < 5 || y > height - 5) {
        continue
      }

      // Check overlap
      let overlapAmount = 0
      for (const r of placed) {
        const overlapX = Math.max(0, Math.min(x + textW, r.x + r.w) - Math.max(x, r.x))
        const overlapY = Math.max(0, Math.min(y, r.y) - Math.max(y - textH, r.y - r.h))
        overlapAmount += overlapX * overlapY
      }

      if (overlapAmount === 0) {
        // Perfect placement - no overlap
        ctx.fillStyle = color
        ctx.globalAlpha = 0.85 + ratio * 0.15
        ctx.fillText(word, x, y)
        ctx.globalAlpha = 1
        placed.push({ x, y, w: textW, h: textH })
        placedOk = true
        break
      } else if (overlapAmount < minOverlap) {
        minOverlap = overlapAmount
        bestX = x
        bestY = y
      }
    }

    // If no perfect placement, use the one with minimal overlap with reduced opacity
    if (!placedOk && minOverlap < textW * textH * 0.3) {
      ctx.fillStyle = color
      ctx.globalAlpha = 0.65
      ctx.fillText(word, bestX, bestY)
      ctx.globalAlpha = 1
      placed.push({ x: bestX, y: bestY, w: textW, h: textH })
    }
  }
}

export function AcademicPoster(props: PosterProps) {
  const {
    title, papers, createdAt, durationSeconds,
    language = 'zh', shareUrl, coreFindings, i18n,
    theme = 'cosmic',
  } = props

  const t = THEMES[theme]

  const qrRef = useRef<HTMLCanvasElement>(null)
  const wordCloudRef = useRef<HTMLCanvasElement>(null)

  // Generate QR code
  useEffect(() => {
    if (qrRef.current && shareUrl) {
      QRCode.toCanvas(qrRef.current, shareUrl, {
        width: 160,
        margin: 2,
        color: { dark: t.qrDark, light: t.qrLight },
      })
    }
  }, [shareUrl, theme])

  // Draw word cloud
  useEffect(() => {
    if (wordCloudRef.current && papers.length > 0) {
      const canvas = wordCloudRef.current
      canvas.width = 960
      canvas.height = 400
      const keywords = extractKeywords(papers, language)
      drawWordCloud(canvas, keywords, t.wordCloudColors)
    }
  }, [papers, language, theme])

  const formatDuration = (secs: number) => {
    if (secs >= 60) return `${Math.floor(secs / 60)}m${Math.round(secs % 60)}s`
    return `${secs}s`
  }

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return new Date().getFullYear().toString()
    return new Date(dateStr).toLocaleDateString(language === 'zh' ? 'zh-CN' : 'en-US', {
      year: 'numeric', month: 'short',
    })
  }

  return (
    <div
      className={`academic-poster ${language === 'en' ? 'academic-poster-intl' : ''} poster-theme-${theme}`}
    >
      <div className="poster-bg" style={{
        '--poster-bg': t.bgGradient,
        '--poster-text': t.textColor,
        '--poster-text-secondary': t.textSecondary,
        '--poster-text-muted': t.textMuted,
        '--poster-accent': t.accentColor,
        '--poster-accent-gradient': t.accentGradient,
        '--poster-card-bg': t.cardBg,
        '--poster-card-border': t.cardBorder,
        '--poster-deco': t.decoBg,
        '--poster-divider': t.dividerColor,
      } as React.CSSProperties}>
        {/* Decorative circles */}
        <div className="poster-deco-circle poster-deco-circle-1" />
        <div className="poster-deco-circle poster-deco-circle-2" />

        {/* Brand */}
        <div className="poster-brand">
          <span className="poster-brand-icon">{t.brandIcon}</span>
          <span className="poster-brand-name">{i18n.brandName}</span>
        </div>

        {/* Title */}
        <h1 className="poster-title">{title}</h1>

        {/* Core findings */}
        {coreFindings.length > 0 && (
          <div className="poster-findings">
            <div className="poster-findings-title">
              <span>💡</span>
              <span>{i18n.coreFindings}</span>
            </div>
            <ul className="poster-findings-list">
              {coreFindings.slice(0, 5).map((finding, i) => (
                <li key={i} className="poster-finding-item">{finding}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Stats */}
        <div className="poster-stats">
          <div className="poster-stat">
            <span className="poster-stat-value">{papers.length}</span>
            <span className="poster-stat-label">{i18n.papersLabel}</span>
          </div>
          {durationSeconds != null && durationSeconds > 0 && (
            <div className="poster-stat">
              <span className="poster-stat-value">{formatDuration(durationSeconds)}</span>
              <span className="poster-stat-label">{i18n.durationLabel}</span>
            </div>
          )}
          <div className="poster-stat">
            <span className="poster-stat-value">{formatDate(createdAt)}</span>
            <span className="poster-stat-label">{i18n.dateLabel}</span>
          </div>
        </div>

        {/* Word cloud */}
        <div className="poster-wordcloud-section">
          <canvas ref={wordCloudRef} className="poster-wordcloud-canvas" />
        </div>

        {/* Bottom: QR + brand */}
        <div className="poster-bottom">
          <div className="poster-qr-section">
            <canvas ref={qrRef} className="poster-qr-canvas" />
            <div className="poster-qr-text">
              <span className="poster-qr-hint">{i18n.scanToRead}</span>
            </div>
          </div>
          <span className="poster-brand-footer">{i18n.poweredBy}</span>
        </div>
      </div>
    </div>
  )
}
