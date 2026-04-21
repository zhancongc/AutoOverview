import { useState, useEffect, useCallback, useRef } from 'react'
import { useNavigate, useLocation, useSearchParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { ReviewViewer } from './ReviewViewer'
import { CitationFormatSelector } from './CitationFormatSelector'
import { api } from '../api'
import type { Paper } from '../types'
import './ReviewPage.css'

interface ReviewState {
  title: string
  content: string
  papers: Paper[]
  recordId?: number
  isPublic?: boolean
  isPaid?: boolean
}

type TabType = 'content' | 'references'
type CitationFormat = 'ieee' | 'apa' | 'mla' | 'gb_t_7714'

interface TocItem {
  id: string
  text: string
  level: number
  children: TocItem[]
}

export function ReviewPage() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const location = useLocation()
  const [searchParams] = useSearchParams()
  const taskId = searchParams.get('task_id') || ''
  const recordIdParam = searchParams.get('record_id')
  const state = location.state as ReviewState | null
  const [hasUpdatedUrl, setHasUpdatedUrl] = useState(false) // 标记是否已更新过URL

  // 通过 taskId 或 recordId 加载的数据
  const [taskData, setTaskData] = useState<{
    title: string
    content: string
    papers: Paper[]
    recordId?: number
    isPublic: boolean
    isPaid: boolean
  } | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [activeTab, setActiveTab] = useState<TabType>('content')
  const [showReviewExportModal, setShowReviewExportModal] = useState(false)
  const [reviewExportFormat, setReviewExportFormat] = useState<'markdown' | 'word'>('markdown')
  const [exportingReview, setExportingReview] = useState(false)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [tocItems, setTocItems] = useState<TocItem[]>([])
  const [citationFormat, setCitationFormat] = useState<CitationFormat>('ieee')
  const [formatLoading, setFormatLoading] = useState(false)
  const [shareCopied, setShareCopied] = useState(false)

  const handleTocUpdate = useCallback((toc: TocItem[]) => {
    setTocItems(toc)
  }, [])

  // 判断是否可以使用引用格式切换（有 taskId 或 recordId）
  const canSwitchFormat = !!(taskId || state?.recordId || recordIdParam || taskData?.recordId)

  // 如果 URL 中有 taskId 或 recordId，从后端加载完整数据
  useEffect(() => {
    // 优先使用 taskId，其次使用 recordId（从 URL 或 state）
    const effectiveRecordId = recordIdParam ? parseInt(recordIdParam) : (state?.recordId || taskData?.recordId)

    if (taskId) {
      setLoading(true)
      api.getTaskReview(taskId, citationFormat)
        .then(res => {
          if (res.success && res.data) {
            setTaskData({
              title: res.data.topic,
              content: res.data.review,
              papers: res.data.papers || [],
              recordId: res.data.record_id,
              isPublic: res.data.is_public,
              isPaid: res.data.is_paid,
            })
          } else {
            setError('综述不存在或尚未完成')
          }
        })
        .catch(err => {
          setError('加载失败：' + (err.response?.data?.detail || err.message))
        })
        .finally(() => {
          setLoading(false)
          setFormatLoading(false)
        })
    } else if (effectiveRecordId) {
      // 通过 recordId 加载数据
      setLoading(true)
      api.getRecordReview(effectiveRecordId, citationFormat)
        .then(res => {
          if (res.success && res.data) {
            setTaskData({
              title: res.data.topic,
              content: res.data.review,
              papers: res.data.papers || [],
              recordId: res.data.record_id,
              isPublic: res.data.is_public,
              isPaid: res.data.is_paid,
            })

            // 如果返回了 task_id 且 URL 中没有，更新 URL（只执行一次）
            if (res.data.task_id && !taskId && !hasUpdatedUrl) {
              setHasUpdatedUrl(true)
              navigate(`/review?task_id=${res.data.task_id}`, { replace: true })
            }
          } else {
            setError('综述不存在或尚未完成')
          }
        })
        .catch(err => {
          setError('加载失败：' + (err.response?.data?.detail || err.message))
        })
        .finally(() => {
          setLoading(false)
          setFormatLoading(false)
        })
    } else if (!state) {
      // 没有 taskId 也没有 state，回到首页
      navigate('/')
    }
  }, [taskId, recordIdParam, state, citationFormat, hasUpdatedUrl, navigate])

  // 确定使用哪个数据源
  const reviewData = state || taskData

  if (error) {
    return (
      <div className="review-page">
        <div className="review-page-header">
          <button className="back-button" onClick={() => navigate(-1)}>←</button>
        </div>
        <div className="error-fallback-container">
          <div className="error-icon">⚠️</div>
          <h2 className="error-title">{t('review.error.loading_failed')}</h2>
          <p className="error-message">{error}</p>

          <div className="error-options">
            <button className="error-option-btn primary" onClick={() => window.location.reload()}>
              <span className="btn-icon">🔄</span>
              <span className="btn-text">{t('review.error.reload')}</span>
            </button>

            <button className="error-option-btn" onClick={() => navigate('/')}>
              <span className="btn-icon">🏠</span>
              <span className="btn-text">{t('review.error.go_home')}</span>
            </button>
          </div>

          <div className="error-hint">
            {t('review.error.hint')}
          </div>
        </div>

        <style>{`
          .error-fallback-container {
            max-width: 600px;
            margin: 100px auto;
            padding: 2rem;
            text-align: center;
          }

          .error-icon {
            font-size: 4rem;
            margin-bottom: 1rem;
          }

          .error-title {
            font-size: 1.5rem;
            font-weight: 600;
            color: var(--ink-black, #1A1A1A);
            margin-bottom: 1rem;
          }

          .error-message {
            color: var(--text-gray, #636E72);
            margin-bottom: 2rem;
            line-height: 1.6;
          }

          .error-options {
            display: flex;
            flex-direction: column;
            gap: 1rem;
            max-width: 320px;
            margin: 0 auto;
            align-items: center;
          }

          .error-option-btn {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.75rem;
            padding: 1rem 1.5rem;
            background: white;
            border: 2px solid var(--border-gray, #E8ECEF);
            border-radius: 12px;
            cursor: pointer;
            font-size: 1rem;
            font-weight: 500;
            transition: all 0.2s;
            color: var(--charcoal, #2D3436);
          }

          .error-option-btn:hover {
            border-color: var(--academic-red, #D63031);
            background: var(--cream-white, #FFFBF5);
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(214, 48, 49, 0.15);
          }

          .error-option-btn.primary {
            background: var(--academic-red, #D63031);
            border-color: var(--academic-red, #D63031);
            color: white;
          }

          .error-option-btn.primary:hover {
            background: var(--academic-red-dark, #B71C1C);
            border-color: var(--academic-red-dark, #B71C1C);
          }

          .btn-icon {
            font-size: 1.25rem;
          }

          .btn-text {
            font-weight: 600;
          }

          .error-hint {
            margin-top: 2rem;
            padding: 1rem;
            background: var(--light-gray, #DFE6E9);
            border-radius: 8px;
            color: var(--text-gray, #636E72);
            font-size: 0.9rem;
          }

          @media (min-width: 768px) {
            .error-options {
              flex-direction: row;
              max-width: 420px;
              justify-content: center;
            }

            .error-option-btn {
              min-width: 160px;
              flex: 0 1 auto;
            }
          }
        `}</style>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="review-page">
        <div className="review-page-header">
          <button className="back-button" onClick={() => navigate(-1)}>←</button>
        </div>
        <div style={{ textAlign: 'center', padding: '4rem', color: '#666' }}>{t('common.loading')}</div>
      </div>
    )
  }

  if (!reviewData || !reviewData.content) {
    // taskId 场景下，数据还在加载中或加载失败（error 已在上面处理）
    if (taskId) {
      if (loading) {
        return (
          <div className="review-page">
            <div className="review-page-header">
              <button className="back-button" onClick={() => navigate(-1)}>←</button>
            </div>
            <div style={{ textAlign: 'center', padding: '4rem', color: '#666' }}>{t('common.loading')}</div>
          </div>
        )
      }

      // 数据为空，显示兜底方案
      return (
        <div className="review-page">
          <div className="review-page-header">
            <button className="back-button" onClick={() => navigate(-1)}>←</button>
          </div>
          <div className="error-fallback-container">
            <div className="error-icon">📭</div>
            <h2 className="error-title">{t('review.error.no_content')}</h2>
            <p className="error-message">
              {t('review.error.review_not_ready')}
            </p>

            <div className="error-options">
              <button className="error-option-btn primary" onClick={() => window.location.reload()}>
                <span className="btn-icon">🔄</span>
                <span className="btn-text">{t('review.error.reload')}</span>
              </button>

              <button className="error-option-btn" onClick={() => navigate('/')}>
                <span className="btn-icon">🏠</span>
                <span className="btn-text">{t('review.error.go_home')}</span>
              </button>
            </div>

            <div className="error-hint">
              {t('review.error.generating_hint')}
            </div>

            <style>{`
              .error-fallback-container {
                min-height: 100vh;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                padding: 2rem;
                background: var(--cream-white, #FFFBF5);
              }

              .error-icon {
                font-size: 4rem;
                margin-bottom: 1rem;
                animation: float 3s ease-in-out infinite;
              }

              @keyframes float {
                0%, 100% { transform: translateY(0px); }
                50% { transform: translateY(-10px); }
              }

              .error-title {
                font-family: 'Playfair Display', Georgia, serif;
                font-size: 1.8rem;
                font-weight: 700;
                color: var(--ink-black, #1A1A1A);
                margin-bottom: 1rem;
              }

              .error-message {
                font-size: 1rem;
                color: var(--text-gray, #636E72);
                margin-bottom: 2rem;
                line-height: 1.6;
              }

              .error-options {
                display: flex;
                flex-direction: column;
                gap: 1rem;
                max-width: 320px;
                margin: 0 auto;
                align-items: center;
              }

              .error-option-btn {
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 0.75rem;
                padding: 1rem 1.5rem;
                border: 2px solid var(--border-gray, #E8ECEF);
                border-radius: 12px;
                background: var(--pure-white, #FFFFFF);
                font-size: 0.95rem;
                font-weight: 500;
                transition: all 0.2s;
                color: var(--charcoal, #2D3436);
                cursor: pointer;
              }

              .error-option-btn:hover {
                border-color: var(--academic-red, #D63031);
                background: var(--cream-white, #FFFBF5);
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(214, 48, 49, 0.15);
              }

              .error-option-btn.primary {
                background: var(--academic-red, #D63031);
                border-color: var(--academic-red, #D63031);
                color: white;
              }

              .error-option-btn.primary:hover {
                background: var(--academic-red-dark, #B71C1C);
                border-color: var(--academic-red-dark, #B71C1C);
              }

              .btn-icon {
                font-size: 1.1rem;
                line-height: 1;
              }

              .btn-text {
                font-size: 0.95rem;
                font-weight: 600;
              }

              .error-hint {
                margin-top: 2rem;
                padding: 0.75rem 1.25rem;
                background: var(--light-gray, #DFE6E9);
                border-radius: 8px;
                font-size: 0.85rem;
                color: var(--text-gray, #636E72);
              }

              @media (min-width: 768px) {
                .error-options {
                  flex-direction: row;
                  max-width: 420px;
                  justify-content: center;
                }

                .error-option-btn {
                  min-width: 160px;
                  flex: 0 1 auto;
                }
              }
            `}</style>
          </div>
        </div>
      )
    }
    navigate('/')
    return null
  }

  const handleBack = () => {
    navigate(-1)
  }

  const handleRegenerate = () => {
    sessionStorage.setItem('pending_topic', reviewData.title)
    navigate('/')
  }


  const doExportReviewFrontend = async () => {
    if (!reviewData) return
    setExportingReview(true)
    try {
      const safeName = reviewData.title.replace(/[\/\\:]/g, '-').substring(0, 50)
      if (reviewExportFormat === 'markdown') {
        let content = `# ${reviewData.title}\n\n${reviewData.content}\n\n## 参考文献\n\n`
        ;(reviewData.papers || []).forEach((p: any, i: number) => {
          content += `[${i + 1}] ${p.authors?.join(', ') || ''}. (${p.year || ''}). ${p.title}.\n`
        })
        const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' })
        const { saveAs } = await import('file-saver')
        saveAs(blob, `${safeName}.md`)
      } else {
        const { Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType } = await import('docx')
        const lines = reviewData.content.split('\n')
        const children: any[] = []
        children.push(new Paragraph({ text: reviewData.title, heading: HeadingLevel.TITLE, alignment: AlignmentType.CENTER, spacing: { after: 400 } }))
        for (const line of lines) {
          const trimmed = line.trim()
          if (!trimmed) { children.push(new Paragraph({})); continue }
          if (trimmed.startsWith('#### ')) {
            children.push(new Paragraph({ text: trimmed.replace('#### ', ''), heading: HeadingLevel.HEADING_4, spacing: { before: 300 } }))
          } else if (trimmed.startsWith('### ')) {
            children.push(new Paragraph({ text: trimmed.replace('### ', ''), heading: HeadingLevel.HEADING_3, spacing: { before: 300 } }))
          } else if (trimmed.startsWith('## ')) {
            children.push(new Paragraph({ text: trimmed.replace('## ', ''), heading: HeadingLevel.HEADING_2, spacing: { before: 300 } }))
          } else if (trimmed.startsWith('# ')) {
            children.push(new Paragraph({ text: trimmed.replace('# ', ''), heading: HeadingLevel.HEADING_1, spacing: { before: 300 } }))
          } else if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
            children.push(new Paragraph({ children: [new TextRun({ text: trimmed.replace(/^[-*]\s*/, '') })], bullet: { level: 0 } }))
          } else {
            children.push(new Paragraph({ children: [new TextRun({ text: trimmed.replace(/\*\*/g, '') })] }))
          }
        }
        if (reviewData.papers?.length > 0) {
          children.push(new Paragraph({ text: '参考文献', heading: HeadingLevel.HEADING_2, spacing: { before: 400 } }))
          reviewData.papers.forEach((p: any, i: number) => {
            children.push(new Paragraph({
              children: [new TextRun({ text: `[${i + 1}] ${p.authors?.join(', ') || ''}. (${p.year || ''}). ${p.title}.` })],
              spacing: { before: 100 },
            }))
          })
        }
        const doc = new Document({ sections: [{ children }] })
        const blob = await Packer.toBlob(doc)
        const { saveAs } = await import('file-saver')
        saveAs(blob, `${safeName}.docx`)
      }
      setShowReviewExportModal(false)
    } catch (err) {
      console.error('Export review failed:', err)
    } finally {
      setExportingReview(false)
    }
  }

  const handleExportWord = () => {
    setShowReviewExportModal(true)
  }

  // 格式切换处理
  const handleFormatChange = (format: CitationFormat) => {
    if (format !== citationFormat) {
      // 只有通过 taskId 或 recordId 加载的页面才需要 loading（因为会重新请求后端）
      if (canSwitchFormat) {
        setFormatLoading(true)
      }
      setCitationFormat(format)
    }
  }

  const handleShare = async () => {
    if (!taskId) return
    try {
      await api.shareSearchResult(taskId)
      const url = `${window.location.origin}/review?task_id=${taskId}`
      await navigator.clipboard.writeText(url)
      setShareCopied(true)
      setTimeout(() => setShareCopied(false), 2000)
    } catch (err) {
      console.error('Share failed:', err)
    }
  }

  // 侧边栏目录点击
  const handleSidebarTocClick = (id: string) => {
    setMobileMenuOpen(false)
    setTimeout(() => {
      const element = document.getElementById(id)
      if (element) {
        window.scrollTo({ top: element.offsetTop - 80, behavior: 'smooth' })
      }
    }, 300)
  }

  // 渲染侧边栏目录
  const renderSidebarTocItem = (item: TocItem) => (
    <li key={item.id} className={`sidebar-toc-item sidebar-toc-level-${item.level}`}>
      <a href={`#${item.id}`} onClick={(e) => { e.preventDefault(); handleSidebarTocClick(item.id) }}>
        {item.text}
      </a>
      {item.children.length > 0 && (
        <ul className="sidebar-toc-children">
          {item.children.map(renderSidebarTocItem)}
        </ul>
      )}
    </li>
  )

  return (
    <div className="review-page">
      <div className="review-page-header">
        <button className="back-button" onClick={handleBack}>
          ←
        </button>
        <div className="review-segmented-tabs">
          <button
            className={`segmented-tab ${activeTab === 'content' ? 'active' : ''}`}
            onClick={() => setActiveTab('content')}
          >
            {t('review.tabs.content')}
          </button>
          <button
            className={`segmented-tab ${activeTab === 'references' ? 'active' : ''}`}
            onClick={() => setActiveTab('references')}
          >
            {t('review.tabs.references')}
          </button>
        </div>
        <div className="header-actions">
          <CitationFormatSelector
            currentFormat={citationFormat}
            onFormatChange={handleFormatChange}
            disabled={!canSwitchFormat || formatLoading || loading}
          />
          <button className="stats-action-btn" onClick={handleRegenerate}>
            {t('review.regenerate')}
          </button>

          <button className="stats-action-btn" onClick={handleExportWord}>
            {t('review.export.export_word', '导出')}
          </button>

          {taskId && (
            <button className="stats-action-btn" onClick={handleShare}>
              {shareCopied ? t('review.share_copied', '已复制') : t('review.share', '分享')}
            </button>
          )}
        </div>
        <button
          className="mobile-menu-toggle review-mobile-toggle"
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          style={{
            display: 'flex',
            minWidth: '44px',
            height: '44px',
            fontSize: '1.5rem',
            color: '#1A1A1A',
            background: 'transparent',
            border: 'none',
            cursor: 'pointer',
            borderRadius: '8px',
            padding: '0.5rem',
            flexShrink: 0,
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 2000
          }}
        >
          ☰
        </button>
      </div>
      {activeTab === 'content' ? (
        <ReviewViewer
          title={reviewData.title}
          content={reviewData.content}
          papers={reviewData.papers}
          onTocUpdate={handleTocUpdate}
        />
      ) : (
        reviewData.papers.length > 0 ? (
          <div className="review-references" style={{ maxWidth: 960, margin: '80px auto 0', padding: '2rem' }}>
            <h2>{t('review.references.title')}</h2>
            <p className="references-summary">
              {t('review.references.total', { count: reviewData.papers.length })}
              {(() => {
                const currentYear = new Date().getFullYear()
                const recentCount = reviewData.papers.filter(p => p.year >= currentYear - 5).length
                const englishCount = reviewData.papers.filter(p => p.is_english).length
                const total = reviewData.papers.length
                const parts = []
                if (total > 0) {
                  parts.push(t('review.references.recent_5_years', { percent: Math.round(recentCount / total * 100) }))
                  parts.push(t('review.references.english', { percent: Math.round(englishCount / total * 100) }))
                }
                return parts.length > 0 ? ` · ${parts.join(' · ')}` : ''
              })()}
            </p>
            <div className="references-notice">
              <span className="notice-icon">💡</span>
              <span className="notice-text">
                {t('review.references.verify_notice')}
              </span>
            </div>
            <ol className="references-list">
              {reviewData.papers.map((paper, index) => {
                const searchQuery = encodeURIComponent(paper.title)
                const verificationLinks = [
                  { name: 'Google Scholar', url: `https://scholar.google.com/scholar?q=${searchQuery}`, icon: '🔬', color: '#4285f4' },
                  { name: '百度学术', url: `https://xueshu.baidu.com/s?wd=${searchQuery}`, icon: '🎓', color: '#2932e1' },
                  ...(paper.doi ? [{ name: 'DOI', url: `https://doi.org/${paper.doi}`, icon: '🔗', color: '#7f8c8d' }] : [])
                ]
                return (
                  <li key={paper.id} className="reference-item">
                    <div className="reference-header">
                      <span className="ref-number">{index + 1}.</span>
                      <div className="ref-verification">
                        {verificationLinks.map((link) => (
                          <a
                            key={link.name}
                            href={link.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="verification-link"
                            title={t('review.references.verify_on', { platform: link.name })}
                            style={{ '--link-color': link.color } as any}
                          >
                            <span className="link-icon">{link.icon}</span>
                            <span className="link-name">{link.name}</span>
                          </a>
                        ))}
                      </div>
                    </div>
                    <div className="ref-content">
                      <a
                        href={verificationLinks[0]?.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="ref-title-link"
                        title={t('review.references.view_on', { platform: verificationLinks[0]?.name || 'third-party platform' })}
                      >
                        {paper.title}
                      </a>
                      <div className="ref-meta">
                        <span className="ref-authors">{paper.authors.join(', ')}</span>
                        <span className="ref-year"> ({paper.year})</span>
                      </div>
                    </div>
                  </li>
                )
              })}
            </ol>
          </div>
        ) : (
          <div style={{ textAlign: 'center', padding: '4rem', color: '#666' }}>
            {t('review.error.no_references')}
          </div>
        )
      )}

      {/* 综述导出格式选择弹窗 */}
      {showReviewExportModal && (
        <div className="confirm-modal-overlay" onClick={() => setShowReviewExportModal(false)}>
          <div className="confirm-modal" onClick={e => e.stopPropagation()}>
            <button className="confirm-modal-close" onClick={() => setShowReviewExportModal(false)}>&times;</button>
            <div className="confirm-modal-header">
              <span className="confirm-modal-icon">📄</span>
              <h2 className="confirm-modal-title">{t('review.export.export_review', '导出综述')}</h2>
            </div>
            <div className="confirm-modal-body">
              <div className="export-format-options">
                {([
                  { key: 'markdown' as const, icon: '📝', name: 'Markdown', desc: t('review.export.markdown_desc', '导出为 .md 文件，保留原始格式') },
                  { key: 'word' as const, icon: '📄', name: 'Word', desc: t('review.export.word_desc', '导出为 .docx 文件，方便编辑分享') },
                ]).map(fmt => (
                  <label key={fmt.key} className={`export-format-option ${reviewExportFormat === fmt.key ? 'active' : ''}`}>
                    <input type="radio" name="review-export-format" value={fmt.key} checked={reviewExportFormat === fmt.key} onChange={() => setReviewExportFormat(fmt.key)} />
                    <span className="export-format-icon">{fmt.icon}</span>
                    <span className="export-format-info">
                      <span className="export-format-name">{fmt.name}</span>
                      <span className="export-format-desc">{fmt.desc}</span>
                    </span>
                  </label>
                ))}
              </div>
            </div>
            <div className="confirm-modal-footer">
              <button className="confirm-modal-btn confirm-modal-btn-cancel" onClick={() => setShowReviewExportModal(false)} disabled={exportingReview}>{t('common.cancel')}</button>
              <button className="confirm-modal-btn confirm-modal-btn-primary" onClick={doExportReviewFrontend} disabled={exportingReview}>
                {exportingReview && <span className="confirm-modal-spinner" />}
                {exportingReview ? t('review.export.exporting') : t('review.export.confirm', '确认导出')}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 移动端侧边栏遮罩 */}
      {mobileMenuOpen && (
        <div className="mobile-sidebar-overlay" onClick={() => setMobileMenuOpen(false)} />
      )}

      {/* 移动端侧边栏 */}
      <aside className={`mobile-sidebar ${mobileMenuOpen ? 'sidebar-open' : ''}`}>
        <div className="sidebar-header">
          <span className="sidebar-header-title">{t('review.sidebar.actions')}</span>
          <button className="sidebar-close" onClick={() => setMobileMenuOpen(false)}>&times;</button>
        </div>
        <div className="sidebar-actions">
          {/* 引用格式选择 */}
          <div className="sidebar-format-section">
            <div className="sidebar-format-label">{t('review.sidebar.format')}</div>
            <div className="sidebar-format-options">
              {(['ieee', 'apa', 'mla', 'gb_t_7714'] as const).map((format) => (
                <button
                  key={format}
                  className={`sidebar-format-btn ${citationFormat === format ? 'active' : ''}`}
                  onClick={() => {
                    handleFormatChange(format);
                  }}
                  disabled={!canSwitchFormat || formatLoading || loading}
                >
                  {format === 'ieee' ? 'IEEE' :
                   format === 'apa' ? 'APA' :
                   format === 'mla' ? 'MLA' : 'GB/T 7714'}
                </button>
              ))}
            </div>
          </div>
          <button
            className="sidebar-action-btn"
            onClick={() => { setMobileMenuOpen(false); handleExportWord() }}
          >
            {t('review.export.export_review', '导出综述')}
          </button>
          <button
            className="sidebar-action-btn sidebar-action-secondary"
            onClick={() => { setMobileMenuOpen(false); handleRegenerate() }}
          >
            {t('review.regenerate')}
          </button>
        </div>
        {tocItems.length > 0 && (
          <div className="sidebar-toc">
            <div className="sidebar-toc-title">{t('review.sidebar.toc')}</div>
            <ul className="sidebar-toc-list">
              {tocItems.map(renderSidebarTocItem)}
            </ul>
          </div>
        )}
      </aside>
    </div>
  )
}
