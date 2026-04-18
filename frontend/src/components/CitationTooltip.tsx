import { useState, useEffect, useRef, useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import './CitationTooltip.css'

interface Paper {
  id: string
  title: string
  authors: string[]
  year: number
  doi?: string
  url?: string
  venue?: string
  abstract?: string
}

interface CitationTooltipProps {
  index: number
  paper: Paper | null
  targetPosition: { x: number; y: number }
  isFixed: boolean
  onClose: () => void
}

export function CitationTooltip({ index, paper, targetPosition, isFixed, onClose }: CitationTooltipProps) {
  const { t } = useTranslation()
  const [abstractExpanded, setAbstractExpanded] = useState(false)
  const tooltipRef = useRef<HTMLDivElement>(null)

  // 点击外部关闭（仅在固定模式下）
  useEffect(() => {
    if (!isFixed) return

    const handleClickOutside = (e: MouseEvent) => {
      if (tooltipRef.current && !tooltipRef.current.contains(e.target as Node)) {
        onClose()
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [isFixed, onClose])

  // 计算位置，避免超出视口
  const getPosition = useCallback(() => {
    const screenWidth = window.innerWidth
    const screenHeight = window.innerHeight
    const tooltipWidth = 400
    const tooltipHeight = 300

    let x = targetPosition.x + 10
    let y = targetPosition.y - 10

    // 水平边界检测
    if (x + tooltipWidth > screenWidth - 20) {
      x = screenWidth - tooltipWidth - 20
    }
    if (x < 20) {
      x = 20
    }

    // 垂直边界检测
    if (y + tooltipHeight > screenHeight - 20) {
      y = targetPosition.y + 30
    }
    if (y < 20) {
      y = 20
    }

    return { x, y }
  }, [targetPosition])

  const position = getPosition()

  // 生成验证链接
  const getLinks = () => {
    const links = []

    if (paper?.url) {
      links.push({ name: t('citation_tooltip.view_original', 'View Original'), url: paper.url })
    }

    if (paper?.doi) {
      links.push({ name: 'DOI', url: `https://doi.org/${paper.doi}` })
    }

    // Google Scholar
    if (paper?.title) {
      const searchQuery = encodeURIComponent(paper.title)
      links.push({ name: 'Google Scholar', url: `https://scholar.google.com/scholar?q=${searchQuery}` })
    }

    return links
  }

  if (!paper || paper === undefined) {
    return (
      <div
        ref={tooltipRef}
        className={`citation-tooltip citation-tooltip-empty ${isFixed ? 'fixed' : ''}`}
        style={{
          left: `${position.x}px`,
          top: `${position.y}px`,
        }}
      >
        <div className="citation-tooltip-header">
          <div className="citation-tooltip-title">
            [{index}] {t('citation_tooltip.paper_unavailable', 'Paper information unavailable')}
          </div>
          {isFixed && (
            <button className="citation-tooltip-close" onClick={onClose}>
              ✕
            </button>
          )}
        </div>
        <div className="citation-tooltip-meta">
          <p style={{ color: '#666', fontSize: '0.9rem' }}>
            {t('citation_tooltip.paper_missing', 'The referenced paper information is missing or index out of range')}
          </p>
        </div>
      </div>
    )
  }

  const links = getLinks()

  return (
    <div
      ref={tooltipRef}
      className={`citation-tooltip ${isFixed ? 'fixed' : ''}`}
      style={{
        left: `${position.x}px`,
        top: `${position.y}px`,
      }}
    >
      {/* 头部：标题 + 关闭按钮 */}
      <div className="citation-tooltip-header">
        <div className="citation-tooltip-title">
          [{index}]{' '}
          {paper.url ? (
            <a href={paper.url} target="_blank" rel="noopener noreferrer">
              {paper.title}
            </a>
          ) : (
            paper.title
          )}
        </div>
        {isFixed && (
          <button className="citation-tooltip-close" onClick={onClose}>
            ✕
          </button>
        )}
      </div>

      {/* 元数据 */}
      <div className="citation-tooltip-meta">
        <div className="citation-tooltip-authors">
          {paper.authors.length > 0 ? paper.authors.join(', ') : t('citation_tooltip.unknown_author', 'Unknown Author')}
        </div>
        <div className="citation-tooltip-venue">
          {paper.venue && <span>{paper.venue}</span>}
          {paper.venue && paper.year && <span>, </span>}
          {paper.year && <span className="citation-tooltip-year">{paper.year}</span>}
        </div>
      </div>

      {/* 摘要（可折叠） */}
      {paper.abstract && (
        <div className="citation-tooltip-abstract-section">
          <button
            className={`citation-tooltip-abstract-toggle ${abstractExpanded ? 'expanded' : ''}`}
            onClick={() => setAbstractExpanded(!abstractExpanded)}
          >
            <span className="citation-tooltip-abstract-toggle-icon">
              {abstractExpanded ? '▼' : '▶'}
            </span>
            {abstractExpanded ? t('citation_tooltip.collapse_abstract', 'Collapse Abstract') : t('citation_tooltip.expand_abstract', 'Expand Abstract')}
          </button>
          {abstractExpanded && (
            <div className="citation-tooltip-abstract">{paper.abstract}</div>
          )}
        </div>
      )}

      {/* 链接 */}
      {links.length > 0 && (
        <div className="citation-tooltip-links">
          {links.map((link) => (
            <a
              key={link.name}
              href={link.url}
              target="_blank"
              rel="noopener noreferrer"
              className="citation-tooltip-link"
            >
              {link.name}
            </a>
          ))}
        </div>
      )}
    </div>
  )
}

interface CitationMarkerProps {
  index: number
  paper: Paper | null
}

export function CitationMarker({ index, paper }: CitationMarkerProps) {
  const [showTooltip, setShowTooltip] = useState(false)
  const [isFixed, setIsFixed] = useState(false)
  const [position, setPosition] = useState({ x: 0, y: 0 })
  const hoverTimerRef = useRef<NodeJS.Timeout | null>(null)

  const handleMouseEnter = (e: any) => {
    if (isFixed) return

    // 清除之前的定时器
    if (hoverTimerRef.current) {
      clearTimeout(hoverTimerRef.current)
    }

    // 延迟 200ms 显示（更快的响应）
    hoverTimerRef.current = setTimeout(() => {
      const rect = (e.currentTarget as HTMLElement).getBoundingClientRect()
      setPosition({ x: rect.right, y: rect.top })
      setShowTooltip(true)
    }, 200)
  }

  const handleMouseLeave = () => {
    if (isFixed) return

    if (hoverTimerRef.current) {
      clearTimeout(hoverTimerRef.current)
    }
    setShowTooltip(false)
  }

  const handleClick = (e: any) => {
    const rect = (e.currentTarget as HTMLElement).getBoundingClientRect()
    setPosition({ x: rect.right, y: rect.top })

    if (isFixed) {
      // 如果已经固定，再次点击则关闭
      setIsFixed(false)
      setShowTooltip(false)
    } else {
      // 固定显示
      setIsFixed(true)
      setShowTooltip(true)
    }
  }

  const handleClose = () => {
    setIsFixed(false)
    setShowTooltip(false)
  }

  return (
    <>
      <span
        className="citation-marker"
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        onClick={handleClick}
      >
        [{index}]
      </span>
      {showTooltip && (
        <CitationTooltip
          index={index}
          paper={paper}
          targetPosition={position}
          isFixed={isFixed}
          onClose={handleClose}
        />
      )}
    </>
  )
}

// 多引用范围标记组件，如 [7-9] 或 [7-9, 11, 12]
interface CitationRangeItem {
  index: number
  paper: Paper | null
}

interface CitationRangeMarkerProps {
  display: string
  citations: CitationRangeItem[]
}

export function CitationRangeMarker({ display, citations }: CitationRangeMarkerProps) {
  const { t } = useTranslation()
  const [showPopup, setShowPopup] = useState(false)
  const [position, setPosition] = useState({ x: 0, y: 0 })
  const popupRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!showPopup) return
    const handleClickOutside = (e: MouseEvent) => {
      if (popupRef.current && !popupRef.current.contains(e.target as Node)) {
        setShowPopup(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [showPopup])

  const handleClick = (e: any) => {
    const rect = (e.currentTarget as HTMLElement).getBoundingClientRect()
    setPosition({ x: rect.left, y: rect.bottom + 4 })
    setShowPopup(!showPopup)
  }

  return (
    <>
      <span
        className="citation-marker citation-range-marker"
        onClick={handleClick}
      >
        {display}
      </span>
      {showPopup && (
        <div
          ref={popupRef}
          className="citation-range-popup"
          style={{ left: `${position.x}px`, top: `${position.y}px` }}
        >
          <div className="citation-range-popup-header">
            <span>{citations.length} {t('review.references.title', 'References').toLowerCase()}</span>
            <button className="citation-tooltip-close" onClick={() => setShowPopup(false)}>✕</button>
          </div>
          <div className="citation-range-popup-list">
            {citations.map(({ index, paper }) => (
              <div key={index} className="citation-range-popup-item">
                <span className="citation-range-popup-index">[{index}]</span>
                {paper ? (
                  <>
                    <div className="citation-range-popup-title">
                      {paper.url ? (
                        <a href={paper.url} target="_blank" rel="noopener noreferrer">{paper.title}</a>
                      ) : (
                        paper.title
                      )}
                    </div>
                    <div className="citation-range-popup-meta">
                      {paper.authors.length > 0 && <span>{paper.authors.slice(0, 3).join(', ')}{paper.authors.length > 3 ? ' et al.' : ''}</span>}
                      {paper.year && <span> ({paper.year})</span>}
                    </div>
                  </>
                ) : (
                  <span style={{ color: '#999' }}>Reference not available</span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </>
  )
}
