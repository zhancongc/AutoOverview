/**
 * Review Page Component - International Version
 * Displays generated literature reviews with export and payment options
 */
import { useState, useEffect, useCallback } from 'react'
import { useNavigate, useLocation, useSearchParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { ReviewViewerInternational } from './ReviewViewerInternational'

import { PayPalPaymentModal } from './PayPalPaymentModal'
import { ConfirmModalInternational } from './ConfirmModalInternational'
import { CitationFormatSelector } from './CitationFormatSelector'
import { api } from '../api'
import type { Paper } from '../types'
import './ReviewPageInternational.css'

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
    isPublic: boolean
    isPaid: boolean
  } | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [activeTab, setActiveTab] = useState<TabType>('content')
  const [showPayModal, setShowPayModal] = useState(false)
  const [exporting, setExporting] = useState(false)
  const [exportError, setExportError] = useState('')
  const [unlockMode, setUnlockMode] = useState(false)
  const [showCreditConfirmModal, setShowCreditConfirmModal] = useState(false)
  const [credits, setCredits] = useState<number>(0)
  const [, setFreeCredits] = useState<number>(0)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [tocItems, setTocItems] = useState<TocItem[]>([])
  const [citationFormat, setCitationFormat] = useState<CitationFormat>('ieee')
  const [formatLoading, setFormatLoading] = useState(false)

  const handleTocUpdate = useCallback((toc: TocItem[]) => {
    setTocItems(toc)
  }, [])

  const isPublicDocument = taskData?.isPublic ?? false
  const isPaidDocument = taskData?.isPaid ?? state?.isPaid ?? false
  const shouldShowWatermark = !isPublicDocument && !isPaidDocument
  const canExportDirectly = isPublicDocument || isPaidDocument
  const canSwitchFormat = !!(taskId || state?.recordId || recordIdParam || taskData?.recordId)

  useEffect(() => {
    api.getCredits().then(data => {
      setCredits(data.credits)
      setFreeCredits(data.free_credits)
    }).catch(err => console.error('Failed to fetch credits:', err))
  }, [])

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
              isPublic: res.data.is_public,
              isPaid: res.data.is_paid,
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
              isPublic: res.data.is_public,
              isPaid: res.data.is_paid,
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

  const reviewData = state || taskData

  if (error) {
    return (
      <div className="review-page-international">
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
      </div>
    )
  }

  if (loading) {
    return (
      <div className="review-page-international">
        <div className="review-page-header">
          <button className="back-button" onClick={() => navigate(-1)}>←</button>
        </div>
        <div className="review-loading-container">
          <div className="review-loading-spinner" />
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
            <button className="back-button" onClick={() => navigate(-1)}>←</button>
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
    navigate(-1)
  }

  const handleRegenerate = () => {
    sessionStorage.setItem('pending_topic', reviewData.title)
    navigate('/')
  }

  const doExport = async () => {
    if (!reviewData.recordId) {
      setExportError(t('review.export.alert_not_supported'))
      return
    }
    setExporting(true)
    setExportError('')
    try {
      const token = localStorage.getItem('auth_token')
      const headers: Record<string, string> = { 'Content-Type': 'application/json' }
      if (token) headers.Authorization = `Bearer ${token}`
      const response = await fetch('/api/records/export', {
        method: 'POST',
        headers,
        body: JSON.stringify({ record_id: reviewData.recordId })
      })
      if (!response.ok) throw new Error(t('review.export.alert_failed'))
      const blob = await response.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      const filename = reviewData.title.replace(/[\/\\:]/g, '-')
      a.download = `${filename}.docx`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } catch (err) {
      setExportError(t('review.export.alert_failed'))
      console.error(err)
    } finally {
      setExporting(false)
    }
  }

  const handleConfirmUseCredit = async () => {
    if (!reviewData.recordId) return

    setShowCreditConfirmModal(false)
    setExporting(true)

    try {
      const result = await api.unlockRecordWithCredit(reviewData.recordId)
      if (result.success) {
        setExportError('')
        const creditsData = await api.getCredits()
        setCredits(creditsData.credits)
        setFreeCredits(creditsData.free_credits)

        if (taskId) {
          api.getTaskReview(taskId).then(res => {
            if (res.success && res.data) {
              setTaskData({
                title: res.data.topic,
                content: res.data.review,
                papers: res.data.papers || [],
                recordId: res.data.record_id,
                isPublic: res.data.is_public,
                isPaid: res.data.is_paid,
              })
            }
          }).catch(err => console.error('Failed to load record:', err))
        }

        await doExport()
      } else {
        setExportError(result.message || t('review.export.unlock_failed'))
      }
    } catch (err) {
      console.error('Unlock failed:', err)
      setExportError(t('review.export.unlock_failed'))
    } finally {
      setExporting(false)
    }
  }

  const handleExportWord = async () => {
    if (canExportDirectly) {
      await doExport()
      return
    }

    if (credits > 0) {
      setShowCreditConfirmModal(true)
      return
    }

    setUnlockMode(true)
    setShowPayModal(true)
  }

  const handleRequestUnlock = () => {
    setUnlockMode(true)
    setShowPayModal(true)
  }

  const handleFormatChange = (format: CitationFormat) => {
    if (format !== citationFormat) {
      if (canSwitchFormat) {
        setFormatLoading(true)
      }
      setCitationFormat(format)
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
          <button className="regenerate-button" onClick={handleRegenerate}>
            {t('review.regenerate')}
          </button>

          <button className={`export-button export-word-btn ${!canExportDirectly ? 'export-word-premium' : ''}`} onClick={handleExportWord} disabled={exporting}>
            {exporting ? t('review.export.exporting') :
             canExportDirectly ? t('review.export.export_word') :
             '🔒 ' + t('review.export.unlock_export')}
          </button>
          {exportError && (
            <div className="export-error-inline">
              <span>{exportError}</span>
              <button className="export-retry-btn" onClick={() => { setExportError(''); handleExportWord(); }}>{t('payment.retry')}</button>
            </div>
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
        <ReviewViewerInternational
          title={reviewData.title}
          content={reviewData.content}
          papers={reviewData.papers}
          hasPurchased={!shouldShowWatermark}
          onTocUpdate={handleTocUpdate}
          onRequestUnlock={handleRequestUnlock}
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
      {showPayModal && unlockMode && (
        <PayPalPaymentModal
          onClose={() => {
            setShowPayModal(false)
            setUnlockMode(false)
          }}
          onPaymentSuccess={async () => {
            setShowPayModal(false)
            setUnlockMode(false)
            if (taskId) {
              api.getTaskReview(taskId).then(res => {
                if (res.success && res.data) {
                  setTaskData({
                    title: res.data.topic,
                    content: res.data.review,
                    papers: res.data.papers || [],
                    recordId: res.data.record_id,
                    isPublic: res.data.is_public,
                    isPaid: res.data.is_paid,
                  })
                }
              }).catch(err => console.error('Failed to refresh task:', err))
            }
          }}
          planType="unlock"
          recordId={reviewData.recordId}
        />
      )}
      {showPayModal && !unlockMode && (
        <PayPalPaymentModal
          onClose={() => setShowPayModal(false)}
          onPaymentSuccess={async () => {
            setShowPayModal(false)
          }}
          planType="single"
        />
      )}

      {showCreditConfirmModal && (
        <ConfirmModalInternational
          message={t('review.export.confirm_message', { credits })}
          confirmText={t('review.export.confirm_button')}
          cancelText={t('common.cancel')}
          onConfirm={handleConfirmUseCredit}
          onCancel={() => setShowCreditConfirmModal(false)}
          type="warning"
        />
      )}

      {mobileMenuOpen && (
        <div className="mobile-sidebar-overlay" onClick={() => setMobileMenuOpen(false)} />
      )}

      <aside className={`mobile-sidebar ${mobileMenuOpen ? 'sidebar-open' : ''}`}>
        <div className="sidebar-header">
          <span className="sidebar-header-title">{t('review.sidebar.actions')}</span>
          <button className="sidebar-close" onClick={() => setMobileMenuOpen(false)}>&times;</button>
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
            className={`sidebar-action-btn ${!canExportDirectly ? 'sidebar-action-premium' : ''}`}
            onClick={() => { setMobileMenuOpen(false); handleExportWord() }}
            disabled={exporting}
          >
            {exporting ? t('review.export.exporting') : canExportDirectly ? t('review.export.export_word') : '🔒 ' + t('review.export.unlock_export')}
          </button>
          {exportError && (
            <div className="export-error-inline">
              <span>{exportError}</span>
              <button className="export-retry-btn" onClick={() => { setExportError(''); handleExportWord(); }}>{t('payment.retry')}</button>
            </div>
          )}
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
