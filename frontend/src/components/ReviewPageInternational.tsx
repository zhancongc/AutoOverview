/**
 * Review Page Component - International Version
 * Displays generated literature reviews with export and payment options
 */
import { useState, useEffect, useCallback, useRef } from 'react'
import { useNavigate, useLocation, useSearchParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { ReviewViewerInternational } from './ReviewViewerInternational'
import { CitationFormatSelector, type CitationFormat } from './CitationFormatSelector'
import { ExportFormatModal, ExportFormat } from './ExportFormatModal'
import { AcademicPoster, PosterTheme } from './AcademicPoster'
import { ShareRewardModal } from './ShareRewardModal'
import { api } from '../api'
import type { Paper } from '../types'
import './ReviewPageInternational.css'

interface ReviewState {
  title: string
  content: string
  papers: Paper[]
  recordId?: number
  taskId?: string
  isPublic?: boolean
  isPaid?: boolean
  statistics?: any
  createdAt?: string
  durationSeconds?: number
}

type TabType = 'content' | 'references'

interface TocItem {
  id: string
  text: string
  level: number
  children: TocItem[]
}

export function ReviewPageInternational() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const location = useLocation()
  const [searchParams] = useSearchParams()
  const taskId = searchParams.get('task_id') || ''
  const recordIdParam = searchParams.get('record_id')
  const state = location.state as ReviewState | null
  const [hasUpdatedUrl, setHasUpdatedUrl] = useState(false)

  const [taskData, setTaskData] = useState<{
    title: string
    content: string
    papers: Paper[]
    recordId?: number
    taskId?: string
    isPublic: boolean
    isPaid: boolean
    statistics?: any
    createdAt?: string
    durationSeconds?: number
  } | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [activeTab, setActiveTab] = useState<TabType>('content')
  const [showReviewExportModal, setShowReviewExportModal] = useState(false)
  const [reviewExportFormat, setReviewExportFormat] = useState<'markdown' | 'word'>('markdown')
  const [exportingReview, setExportingReview] = useState(false)
  const [showExportRefModal, setShowExportRefModal] = useState(false)
  const [exportRefFormat, setExportRefFormat] = useState<ExportFormat>('bibtex')
  const [exportingRef, setExportingRef] = useState(false)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [tocItems, setTocItems] = useState<TocItem[]>([])
  const [citationFormat, setCitationFormat] = useState<CitationFormat>('ieee')
  const [formatLoading, setFormatLoading] = useState(false)
  const [showToast, setShowToast] = useState(false)
  const [showPosterModal, setShowPosterModal] = useState(false)
  const [generatingPoster, setGeneratingPoster] = useState(false)
  const [posterTheme, setPosterTheme] = useState<PosterTheme>('cosmic')
  const posterGenRef = useRef(false)
  const [showShareReward, setShowShareReward] = useState(false)

  const handleTocUpdate = useCallback((toc: TocItem[]) => {
    setTocItems(toc)
  }, [])

  const canSwitchFormat = !!(taskId || state?.recordId || recordIdParam || taskData?.recordId)

  useEffect(() => {
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
              taskId: res.data.task_id || taskId,
              isPublic: res.data.is_public,
              isPaid: res.data.is_paid,
              statistics: res.data.statistics,
              createdAt: res.data.created_at,
              durationSeconds: res.data.duration_seconds,
            })
          } else {
            setError('Review not found or not yet completed')
          }
        })
        .catch(err => {
          setError('Failed to load: ' + (err.response?.data?.detail || err.message))
        })
        .finally(() => {
          setLoading(false)
          setFormatLoading(false)
        })
    } else if (effectiveRecordId) {
      setLoading(true)
      api.getRecordReview(effectiveRecordId, citationFormat)
        .then(res => {
          if (res.success && res.data) {
            setTaskData({
              title: res.data.topic,
              content: res.data.review,
              papers: res.data.papers || [],
              recordId: res.data.record_id,
              taskId: res.data.task_id ?? undefined,
              isPublic: res.data.is_public,
              isPaid: res.data.is_paid,
              statistics: res.data.statistics,
              createdAt: res.data.created_at,
              durationSeconds: res.data.duration_seconds,
            })

            if (res.data.task_id && !taskId && !hasUpdatedUrl) {
              setHasUpdatedUrl(true)
              navigate(`/review?task_id=${res.data.task_id}`, { replace: true })
            }
          } else {
            setError('Review not found or not yet completed')
          }
        })
        .catch(err => {
          setError('Failed to load: ' + (err.response?.data?.detail || err.message))
        })
        .finally(() => {
          setLoading(false)
          setFormatLoading(false)
        })
    } else if (!state) {
      navigate('/')
    }
  }, [taskId, recordIdParam, state, citationFormat, hasUpdatedUrl, navigate])

  // 分享奖励弹窗：检查 sessionStorage 标记
  useEffect(() => {
    const pendingTaskId = sessionStorage.getItem('share_reward_pending')
    if (pendingTaskId) {
      sessionStorage.removeItem('share_reward_pending')
      const timer = setTimeout(() => setShowShareReward(true), 1500)
      return () => clearTimeout(timer)
    }
  }, [])

  const reviewData = state || taskData

  if (error) {
    return (
      <div className="review-page-international">
        <div className="review-page-header">
          <div className="header-left-buttons">
            <button className="back-button" onClick={() => navigate(-1)}>←</button>
          </div>
        </div>
        <div className="error-fallback-container">
          <div className="error-icon">🔒</div>
          <h2 className="error-title">{t('review.error.access_denied', 'Access Denied')}</h2>
          <p className="error-message">{error}</p>

          <div className="error-options">
            <button className="error-option-btn" onClick={() => navigate('/')}>
              <span className="btn-icon">🏠</span>
              <span className="btn-text">{t('review.error.go_home')}</span>
            </button>
            <button className="error-option-btn primary" onClick={() => navigate('/profile?tab=reviews')}>
              <span className="btn-icon">👤</span>
              <span className="btn-text">{t('review.error.my_profile', 'My Reviews')}</span>
            </button>
          </div>
        </div>

        <style>{`
          .error-fallback-container {
            max-width: 600px;
            margin: 100px auto;
            padding: 3rem 2rem;
            text-align: center;
            background: white;
            border-radius: 16px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
          }

          .error-icon {
            font-size: 4rem;
            margin-bottom: 1.5rem;
          }

          .error-title {
            font-size: 1.75rem;
            font-weight: 700;
            color: #1A1A1A;
            margin-bottom: 0.75rem;
            font-family: 'Playfair Display', Georgia, serif;
          }

          .error-message {
            color: #636E72;
            margin-bottom: 2.5rem;
            line-height: 1.7;
            font-size: 1.05rem;
          }

          .error-options {
            display: flex;
            flex-direction: column;
            gap: 1rem;
            max-width: 360px;
            margin: 0 auto;
            align-items: stretch;
          }

          .error-option-btn {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.75rem;
            padding: 1rem 1.5rem;
            background: white;
            border: 2px solid #E8ECEF;
            border-radius: 12px;
            cursor: pointer;
            font-size: 1rem;
            font-weight: 600;
            transition: all 0.2s;
            color: #2D3436;
          }

          .error-option-btn:hover {
            border-color: #0988E3;
            background: #F0F7FF;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(9, 136, 227, 0.15);
          }

          .error-option-btn.primary {
            background: #0988E3;
            border-color: #0988E3;
            color: white;
          }

          .error-option-btn.primary:hover {
            background: #0770BD;
            border-color: #0770BD;
          }

          .btn-icon {
            font-size: 1.3rem;
          }

          .btn-text {
            font-weight: 600;
          }

          @media (min-width: 768px) {
            .error-options {
              flex-direction: row;
              max-width: 480px;
              justify-content: center;
            }

            .error-option-btn {
              min-width: 180px;
              flex: 0 1 auto;
            }
          }
        `}</style>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="review-page-international">
        <div className="review-page-header">
          <div className="header-left-buttons">
            <button className="back-button" onClick={() => navigate(-1)}>←</button>
          </div>
        </div>
        <div className="review-loading-container">
          <div className="review-loading-spinner"></div>
          <p className="review-loading-text">{t('common.loading')}</p>
        </div>
      </div>
    )
  }

  if (!reviewData || !reviewData.content) {
    if (taskId) {
      return (
        <div className="review-page-international">
          <div className="review-page-header">
            <div className="header-left-buttons">
              <button className="back-button" onClick={() => navigate(-1)}>←</button>
            </div>
          </div>
          <div className="error-fallback-container">
            <div className="error-icon">📭</div>
            <h2 className="error-title">{t('review.error.no_content')}</h2>
            <p className="error-message">{t('review.error.review_not_ready')}</p>

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
          </div>
        </div>
      )
    }
    navigate('/')
    return null
  }

  const handleBack = () => {
    navigate('/profile?tab=reviews')
  }

  const handleRegenerate = () => {
    navigate(`/generate?topic=${encodeURIComponent(reviewData.title)}`)
  }

  const doExportReviewFrontend = async () => {
    if (!reviewData) return
    setExportingReview(true)
    try {
      const safeName = reviewData.title.replace(/[\/\\:]/g, '-').substring(0, 50)
      if (reviewExportFormat === 'markdown') {
        const hasReferences = /##\s*(References|参考文献)/i.test(reviewData.content)
        let content = `# ${reviewData.title}\n\n${reviewData.content}`
        if (!hasReferences && reviewData.papers?.length > 0) {
          content += `\n\n## References\n\n`
          ;(reviewData.papers || []).forEach((p: any, i: number) => {
            content += `[${i + 1}] ${p.authors?.join(', ') || ''}. (${p.year || ''}). ${p.title}.\n`
          })
        }
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
        if (reviewData.papers?.length > 0 && !/##\s*(References|参考文献)/i.test(reviewData.content)) {
          children.push(new Paragraph({ text: 'References', heading: HeadingLevel.HEADING_2, spacing: { before: 400 } }))
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

  const generateBibTeX = (papers: any[]) => {
    return papers.map((paper, i) => {
      const key = (paper.authors?.[0]?.split(' ').pop()?.toLowerCase() || 'unknown')
        + (paper.year || '') + '_' + (i + 1)
      const authors = paper.authors?.join(' and ') || 'Unknown'
      let entry = `@article{${key},\n`
      entry += `  title = {${paper.title}},\n`
      entry += `  author = {${authors}},\n`
      if (paper.year) entry += `  year = {${paper.year}},\n`
      if (paper.doi) entry += `  doi = {${paper.doi}},\n`
      if (paper.journal) entry += `  journal = {${paper.journal}},\n`
      entry += `}`
      return entry
    }).join('\n\n')
  }

  const generateRIS = (papers: any[]) => {
    return papers.map(paper => {
      let ris = `TY  - JOUR\n`
      ris += `TI  - ${paper.title}\n`
      if (paper.authors) {
        paper.authors.forEach((a: string) => { ris += `AU  - ${a}\n` })
      }
      if (paper.year) ris += `PY  - ${paper.year}\n`
      if (paper.doi) ris += `DO  - ${paper.doi}\n`
      if (paper.journal) ris += `JO  - ${paper.journal}\n`
      ris += `ER  - \n`
      return ris
    }).join('\n')
  }

  const handleExportReferences = async () => {
    const papers = reviewData?.papers || []
    if (papers.length === 0) return

    setExportingRef(true)
    try {
      const safeName = (reviewData?.title || 'references').replace(/[\/\\:]/g, '-').substring(0, 50)
      const { saveAs } = await import('file-saver')

      if (exportRefFormat === 'bibtex') {
        const content = generateBibTeX(papers)
        const blob = new Blob([content], { type: 'application/x-bibtex;charset=utf-8' })
        saveAs(blob, `${safeName}.bib`)
      } else if (exportRefFormat === 'ris') {
        const content = generateRIS(papers)
        const blob = new Blob([content], { type: 'application/x-research-info-systems;charset=utf-8' })
        saveAs(blob, `${safeName}.ris`)
      } else {
        const { Document, Packer, Paragraph, TextRun } = await import('docx')
        const children: any[] = [
          new Paragraph({ text: reviewData?.title || 'References', heading: 'Heading1' as any }),
          new Paragraph({ text: '' }),
        ]
        papers.forEach((paper: any, i: number) => {
          const authors = paper.authors?.slice(0, 3).join(', ') + (paper.authors?.length > 3 ? ' et al.' : '')
          children.push(new Paragraph({
            children: [
              new TextRun({ text: `[${i + 1}] `, bold: true }),
              new TextRun({ text: `${paper.title}. ${authors}. ${paper.year || ''} ${paper.doi ? `DOI: ${paper.doi}` : ''}` }),
            ],
            spacing: { after: 200 },
          }))
        })
        const doc = new Document({ sections: [{ children }] })
        const blob = await Packer.toBlob(doc)
        saveAs(blob, `${safeName}.docx`)
      }
    } finally {
      setExportingRef(false)
      setShowExportRefModal(false)
    }
  }

  const handleExportWord = () => {
    setShowReviewExportModal(true)
  }

  const handleFormatChange = (format: CitationFormat) => {
    if (format !== citationFormat) {
      if (canSwitchFormat) {
        setFormatLoading(true)
      }
      setCitationFormat(format)
    }
  }

  const handleShare = async () => {
    const shareTaskId = taskId || taskData?.taskId
    try {
      if (shareTaskId) {
        try { await api.shareSearchResult(shareTaskId) } catch {}
      }
      await navigator.clipboard.writeText(window.location.href)
      setShowToast(true)
      setTimeout(() => { setShowToast(false) }, 3000)
    } catch (err) {
      console.error('Share failed:', err)
    }
  }

  const extractCoreFindings = (content: string): string[] => {
    const findings: string[] = []
    const lines = content.split('\n')
    let inFindings = false
    for (const line of lines) {
      const trimmed = line.trim()
      if (/^#{1,3}\s/.test(trimmed)) {
        const heading = trimmed.replace(/^#+\s*/, '').toLowerCase()
        inFindings = /conclusion|finding|key|main|result|summary|核心|发现/i.test(heading)
        continue
      }
      if (inFindings && /^[-*]\s/.test(trimmed)) {
        const text = trimmed.replace(/^[-*]\s*/, '').replace(/\*\*/g, '').trim()
        if (text.length > 5 && text.length < 150) findings.push(text)
        if (findings.length >= 5) break
      }
    }
    if (findings.length === 0) {
      for (const line of lines) {
        const trimmed = line.trim()
        if (/^[-*]\s/.test(trimmed)) {
          const text = trimmed.replace(/^[-*]\s*/, '').replace(/\*\*/g, '').trim()
          if (text.length > 5 && text.length < 150) findings.push(text)
          if (findings.length >= 5) break
        }
      }
    }
    return findings
  }

  const handleGeneratePoster = async () => {
    if (posterGenRef.current || generatingPoster) return
    posterGenRef.current = true
    setGeneratingPoster(true)

    await new Promise(resolve => setTimeout(resolve, 100))

    try {
      const html2canvas = (await import('html2canvas-pro')).default
      // Find the hidden poster for generation
      const posterEl = document.getElementById('poster-for-generation') as HTMLElement
      if (!posterEl) return

      const canvas = await html2canvas(posterEl, {
        scale: 1,
        useCORS: true,
        logging: false,
        backgroundColor: null,
        width: 1080,
        height: 1920,
      })

      const { saveAs } = await import('file-saver')
      const safeName = (reviewData?.title || 'academic-poster').replace(/[\/\\:]/g, '-').substring(0, 50)
      canvas.toBlob((blob) => {
        if (blob) {
          saveAs(blob, `${safeName}-poster.png`)
        }
      }, 'image/png')
    } catch (err) {
      console.error('Generate poster failed:', err)
    } finally {
      setGeneratingPoster(false)
      posterGenRef.current = false
    }
  }

  const handleSidebarTocClick = (id: string) => {
    setMobileMenuOpen(false)
    setTimeout(() => {
      const element = document.getElementById(id)
      if (element) {
        window.scrollTo({ top: element.offsetTop - 80, behavior: 'smooth' })
      }
    }, 300)
  }

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
    <div className="review-page-international">
      <div className="review-page-header">
        <div className="header-left-buttons">
          <button className="back-button" onClick={handleBack}>
            ←
          </button>
        </div>
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
            {t('review.export.export_word', 'Export')}
          </button>

          {reviewData && (
            <button className="stats-action-btn" onClick={() => setShowPosterModal(true)}>
              {t('review.share', 'Share')}
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
      <div className="review-stats-container">
        <div className="review-stats">
          <div className="review-stats-header">
            <p className="review-topic" style={{ fontSize: '1.05rem', color: '#1f2937', fontWeight: 600, margin: 0, lineHeight: 1.4 }}>
              {reviewData.title}
            </p>
            <button className="stats-action-btn" onClick={() => setShowExportRefModal(true)} disabled={!reviewData.papers || reviewData.papers.length === 0}>
              {t('comparison_matrix_page.export_references', 'Export References')}
            </button>
          </div>
          <div className="stats-left">
            {reviewData.papers && reviewData.papers.length > 0 && (
              <div className="stat-item">
                <span className="stat-label">{t('comparison_matrix_page.papers_used')}</span>
                <span className="stat-value">{reviewData.papers.length} {t('comparison_matrix_page.papers_unit')}</span>
              </div>
            )}
            {(taskData?.statistics?.total_time_seconds || (state as any)?.statistics?.total_time_seconds) && (() => {
              const secs = taskData?.statistics?.total_time_seconds || (state as any)?.statistics?.total_time_seconds
              const display = secs >= 60 ? `${Math.floor(secs / 60)}m${Math.round(secs % 60)}s` : `${secs}s`
              return (
                <div className="stat-item">
                  <span className="stat-label">{t('comparison_matrix_page.time_used')}</span>
                  <span className="stat-value">{display}</span>
                </div>
              )
            })()}
            {(taskData?.createdAt || (state as any)?.createdAt) && (
              <div className="stat-item">
                <span className="stat-label">{t('comparison_matrix_page.generated_at')}</span>
                <span className="stat-value">
                  {new Date(taskData?.createdAt || (state as any)?.createdAt).toLocaleString()}
                </span>
              </div>
            )}
            {(taskData?.durationSeconds ?? (state as any)?.durationSeconds) && (() => {
              const secs = taskData?.durationSeconds ?? (state as any)?.durationSeconds
              const display = secs >= 60 ? `${Math.floor(secs / 60)}m${Math.round(secs % 60)}s` : `${secs}s`
              return (
                <div className="stat-item">
                  <span className="stat-label">{t('review_page.duration')}</span>
                  <span className="stat-value">{display}</span>
                </div>
              )
            })()}
          </div>
        </div>
      </div>

      {showExportRefModal && (
        <ExportFormatModal
          selectedFormat={exportRefFormat}
          onSelectFormat={setExportRefFormat}
          onConfirm={handleExportReferences}
          onCancel={() => setShowExportRefModal(false)}
          loading={exportingRef}
        />
      )}

      {activeTab === 'content' ? (
        <ReviewViewerInternational
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
                  { name: 'Semantic Scholar', url: `https://www.semanticscholar.org/search?q=${searchQuery}`, icon: '📚', color: '#3b8bb5' },
                  ...(paper.doi ? [{ name: 'DOI', url: `https://doi.org/${paper.doi}`, icon: '🔗', color: '#7f8c8d' }] : []),
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

      {showReviewExportModal && (
        <div className="confirm-modal-overlay" onClick={() => setShowReviewExportModal(false)}>
          <div className="confirm-modal" onClick={e => e.stopPropagation()}>
            <button className="confirm-modal-close" onClick={() => setShowReviewExportModal(false)}>×</button>
            <div className="confirm-modal-header">
              <span className="confirm-modal-icon">📄</span>
              <h2 className="confirm-modal-title">{t('review.export.export_review', 'Export Review')}</h2>
            </div>
            <div className="confirm-modal-body">
              <div className="export-format-options">
                {([
                  { key: 'markdown' as const, icon: '📝', name: 'Markdown', desc: t('review.export.markdown_desc', 'Export as .md file') },
                  { key: 'word' as const, icon: '📄', name: 'Word', desc: t('review.export.word_desc', 'Export as .docx file') },
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
                {exportingReview && <span className="confirm-modal-spinner"></span>}
                {exportingReview ? t('review.export.exporting') : t('review.export.confirm', 'Export')}
              </button>
            </div>
          </div>
        </div>
      )}

      {mobileMenuOpen && (
        <div className="mobile-sidebar-overlay" onClick={() => setMobileMenuOpen(false)}></div>
      )}

      <aside className={`mobile-sidebar ${mobileMenuOpen ? 'sidebar-open' : ''}`}>
        <div className="sidebar-header">
          <span className="sidebar-header-title">{t('review.sidebar.actions')}</span>
          <button className="sidebar-close" onClick={() => setMobileMenuOpen(false)}>×</button>
        </div>
        <div className="sidebar-actions">
          <div className="sidebar-format-section">
            <div className="sidebar-format-label">{t('review.sidebar.format')}</div>
            <div className="sidebar-format-options">
              {(['ieee', 'apa', 'mla'] as const).map((format) => (
                <button
                  key={format}
                  className={`sidebar-format-btn ${citationFormat === format ? 'active' : ''}`}
                  onClick={() => {
                    handleFormatChange(format);
                  }}
                  disabled={!canSwitchFormat || formatLoading || loading}
                >
                  {format.toUpperCase()}
                </button>
              ))}
            </div>
          </div>
          <button
            className="sidebar-action-btn"
            onClick={() => { setMobileMenuOpen(false); handleExportWord() }}
          >
            {t('review.export.export_review', 'Export Review')}
          </button>
          <button
            className="sidebar-action-btn sidebar-action-secondary"
            onClick={() => { setMobileMenuOpen(false); handleRegenerate() }}
          >
            {t('review.regenerate')}
          </button>
          <button
            className="sidebar-action-btn"
            onClick={() => { setMobileMenuOpen(false); setShowPosterModal(true) }}
          >
            {t('review.share', 'Share')}
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

      {showToast && (
        <div className="review-toast">
          <div className="review-toast-content">
            <span className="toast-icon">✓</span>
            <span className="toast-message">{t('review.share_toast', 'Share link copied to clipboard, you can paste it on other platforms')}</span>
          </div>
        </div>
      )}

      {showPosterModal && reviewData && (
        <div className="confirm-modal-overlay" onClick={() => setShowPosterModal(false)}>
          <div className="confirm-modal" onClick={e => e.stopPropagation()} style={{ maxWidth: 420 }}>
            <button className="confirm-modal-close" onClick={() => setShowPosterModal(false)}>×</button>
            <div className="confirm-modal-header">
              <h2 className="confirm-modal-title">{t('poster.generate')}</h2>
            </div>
            <div className="confirm-modal-body" style={{ textAlign: 'center', padding: '20px' }}>
              {/* Style selector */}
              <div style={{ display: 'flex', gap: '10px', justifyContent: 'center', marginBottom: '16px', flexWrap: 'wrap' }}>
                {([
                  { key: 'cosmic', label: 'Cosmic', gradient: 'linear-gradient(135deg, #302b63, #24243e)' },
                  { key: 'gold', label: 'Black Gold', gradient: 'linear-gradient(135deg, #0a0a0a, #d4a853)' },
                  { key: 'minimal', label: 'Minimal', gradient: 'linear-gradient(135deg, #f8f9fa, #3b82f6)' },
                  { key: 'forest', label: 'Forest', gradient: 'linear-gradient(135deg, #1a3a2a, #4ade80)' },
                  { key: 'chinese', label: 'Chinese Red', gradient: 'linear-gradient(135deg, #4a1a1a, #fbbf24)' },
                ] as const).map(item => (
                  <button
                    key={item.key}
                    onClick={() => setPosterTheme(item.key)}
                    style={{
                      display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '4px',
                      background: 'none', border: 'none', cursor: 'pointer', padding: '4px',
                    }}
                  >
                    <div style={{
                      width: '40px', height: '40px', borderRadius: '50%',
                      background: item.gradient,
                      border: posterTheme === item.key ? '3px solid #3b82f6' : '3px solid transparent',
                      boxShadow: posterTheme === item.key ? '0 0 0 2px rgba(59,130,246,0.3)' : 'none',
                      transition: 'all 0.2s',
                    }} />
                    <span style={{ fontSize: '12px', color: posterTheme === item.key ? '#3b82f6' : '#6b7280', fontWeight: posterTheme === item.key ? 600 : 400 }}>
                      {item.label}
                    </span>
                  </button>
                ))}
              </div>
              {/* Poster preview */}
              <div style={{
                width: '324px',
                height: '576px',
                margin: '0 auto',
                borderRadius: '12px',
                overflow: 'hidden',
                boxShadow: '0 4px 20px rgba(0,0,0,0.15)',
                position: 'relative',
              }}>
                <div style={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  width: '1080px',
                  height: '1920px',
                  transform: 'scale(0.3)',
                  transformOrigin: 'top left',
                }}>
                  <AcademicPoster
                    title={reviewData.title}
                    content={reviewData.content}
                    papers={reviewData.papers}
                    createdAt={taskData?.createdAt || (state as any)?.createdAt}
                    durationSeconds={taskData?.durationSeconds ?? (state as any)?.durationSeconds}
                    language="en"
                    shareUrl={window.location.href}
                    coreFindings={extractCoreFindings(reviewData.content)}
                    theme={posterTheme}
                    i18n={{
                      coreFindings: t('poster.core_findings'),
                      papersLabel: t('poster.papers_label'),
                      durationLabel: t('poster.duration_label'),
                      dateLabel: t('poster.date_label'),
                      scanToRead: t('poster.scan_to_read'),
                      poweredBy: t('poster.powered_by'),
                      brandName: t('poster.brand_name'),
                    }}
                  />
                </div>
              </div>
            </div>
            <div className="confirm-modal-footer" style={{ gap: '12px' }}>
              <button className="confirm-modal-btn confirm-modal-btn-cancel" onClick={async () => {
                await handleShare()
                setShowPosterModal(false)
              }}>
                {t('poster.copy_link', 'Share Link')}
              </button>
              <button className="confirm-modal-btn confirm-modal-btn-primary" onClick={handleGeneratePoster} disabled={generatingPoster}>
                {generatingPoster && <span className="confirm-modal-spinner"></span>}
                {generatingPoster ? t('poster.generating') : t('poster.save_poster', 'Save Poster')}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Hidden poster for generation */}
      {reviewData && (
        <div id="poster-for-generation" style={{ position: 'fixed', left: '-9999px', top: 0, width: '1080px', height: '1920px', zIndex: -1 }}>
          <AcademicPoster
            title={reviewData.title}
            content={reviewData.content}
            papers={reviewData.papers}
            createdAt={taskData?.createdAt || (state as any)?.createdAt}
            durationSeconds={taskData?.durationSeconds ?? (state as any)?.durationSeconds}
            language="en"
            shareUrl={window.location.href}
            coreFindings={extractCoreFindings(reviewData.content)}
            theme={posterTheme}
            i18n={{
              coreFindings: t('poster.core_findings'),
              papersLabel: t('poster.papers_label'),
              durationLabel: t('poster.duration_label'),
              dateLabel: t('poster.date_label'),
              scanToRead: t('poster.scan_to_read'),
              poweredBy: t('poster.powered_by'),
              brandName: t('poster.brand_name'),
            }}
          />
        </div>
      )}

      {/* 分享奖励弹窗 */}
      {showShareReward && taskId && (
        <ShareRewardModal
          taskId={taskId}
          onClose={() => setShowShareReward(false)}
        />
      )}
    </div>
  )
}
