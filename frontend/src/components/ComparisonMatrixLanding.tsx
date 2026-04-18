/**
 * ComparisonMatrixLanding - 对比矩阵着陆页
 * URL: /comparison-matrix（无 task_id）
 * 搜索文献 → 生成对比矩阵，保留通用导航栏
 */
import { useState, useEffect, useCallback } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { api } from '../api'
import { isLoggedIn as checkLoggedIn } from '../authApi'
import { LoginModal } from './LoginModal'
import { LoginModalInternational } from './LoginModalInternational'
import { PayPalPaymentModal } from './PayPalPaymentModal'
import { ConfirmModalInternational } from './ConfirmModalInternational'
import { ConfirmModal } from './ConfirmModal'
import { useMatrixAuth, Paper, Statistics, SortMode, CombinedPhase } from './ComparisonMatrixShared'
import './ComparisonMatrixPage.css'
import './SearchPapersPage.css'

export function ComparisonMatrixLanding() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const location = useLocation()
  const { isChineseSite, loggedIn, showLoginModal, setShowLoginModal, handleLoginSuccess, setCredits, credits } = useMatrixAuth()

  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [showPaymentModal, setShowPaymentModal] = useState<string | false>(false)
  const [showCreditConfirm, setShowCreditConfirm] = useState(false)

  // Search state
  const [topic, setTopic] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [papers, setPapers] = useState<Paper[]>([])
  const [statistics, setStatistics] = useState<Statistics | null>(null)
  const [searchError, setSearchError] = useState('')
  const [sortMode, setSortMode] = useState<SortMode>('citations')
  const [hasSearched, setHasSearched] = useState(false)

  // Combined flow state
  const [combinedPhase, setCombinedPhase] = useState<CombinedPhase>('idle')
  const [combinedProgress, setCombinedProgress] = useState(0)
  const [combinedMessage, setCombinedMessage] = useState('')
  const [pendingTopic, setPendingTopic] = useState('')

  // Restore search state from localStorage
  useEffect(() => {
    const savedTopic = localStorage.getItem('cm_topic')
    const savedPapers = localStorage.getItem('cm_papers')
    const savedStats = localStorage.getItem('cm_statistics')
    const savedHasSearched = localStorage.getItem('cm_has_searched')
    if (savedTopic) setTopic(savedTopic)
    if (savedPapers) setPapers(JSON.parse(savedPapers))
    if (savedStats) setStatistics(JSON.parse(savedStats))
    if (savedHasSearched) setHasSearched(savedHasSearched === 'true')

    // Restore in-progress matrix generation
    const pendingMatrixTaskId = localStorage.getItem('cm_matrix_task_id')
    if (pendingMatrixTaskId && savedTopic) {
      setCombinedPhase('generating_matrix')
      setCombinedProgress(40)
      setCombinedMessage(t('comparison_matrix_page.phase_generating'))
      pollMatrixResult(pendingMatrixTaskId)
    }
  }, [])

  const pollMatrixResult = async (matrixTaskId: string) => {
    let attempts = 0
    const maxAttempts = 120

    while (attempts < maxAttempts) {
      attempts++
      setCombinedProgress(Math.min(40 + (attempts / maxAttempts) * 55, 95))

      try {
        const taskResult = await api.getTaskStatus(matrixTaskId)
        if (taskResult.success && taskResult.data) {
          const task = taskResult.data

          if (task.status === 'completed' && task.result) {
            setCombinedProgress(100)
            setCombinedPhase('idle')
            localStorage.removeItem('cm_matrix_task_id')
            navigate(`/comparison-matrix?task_id=${matrixTaskId}`)
            return
          } else if (task.status === 'failed') {
            setSearchError(task.error || t('comparison_matrix_page.error'))
            setCombinedPhase('idle')
            localStorage.removeItem('cm_matrix_task_id')
            return
          } else if (task.progress?.message) {
            setCombinedMessage(task.progress.message)
          }
        }
      } catch {
        // ignore
      }

      await new Promise(resolve => setTimeout(resolve, 5000))
    }

    setSearchError(t('comparison_matrix_page.error'))
    setCombinedPhase('idle')
    localStorage.removeItem('cm_matrix_task_id')
  }

  const handleGenerateAll = useCallback(async () => {
    if (!topic.trim()) return

    if (!checkLoggedIn()) {
      setShowLoginModal(true)
      return
    }

    setSearchError('')
    setPapers([])
    setStatistics(null)
    setHasSearched(true)
    setSortMode('citations')
    localStorage.setItem('cm_topic', topic)

    // Phase 1: Search papers
    setCombinedPhase('searching')
    setCombinedProgress(5)
    setCombinedMessage(t('comparison_matrix_page.phase_searching'))
    setIsLoading(true)

    let currentSearchTaskId = ''

    try {
      const response = await api.searchPapersOnly(topic, {
        targetCount: 30,
        searchYears: 10
      })

      if (response.success && response.data) {
        const foundPapers = response.data.all_papers || []
        const stats = response.data.statistics || null
        const tid = response.data.task_id || ''

        setPapers(foundPapers)
        setStatistics(stats)
        currentSearchTaskId = tid

        localStorage.setItem('cm_papers', JSON.stringify(foundPapers))
        localStorage.setItem('cm_statistics', JSON.stringify(stats))
        localStorage.setItem('cm_search_task_id', tid)
        localStorage.setItem('cm_has_searched', 'true')

      } else {
        setSearchError(response.message || t('comparison_matrix_page.error'))
        setCombinedPhase('idle')
        setIsLoading(false)
        return
      }
    } catch (err: any) {
      if (err.response?.status === 429) {
        setSearchError(t('search_papers.input.limit_exceeded_full'))

        setCombinedPhase('idle')
        setIsLoading(false)
        return
      } else if (err.code === 'ECONNABORTED' || err.message?.includes('timeout')) {
        setSearchError(t('search_papers.error.timeout'))
      } else {
        setSearchError(t('comparison_matrix_page.error'))
      }
      setCombinedPhase('idle')
      setIsLoading(false)
      return
    }

    setIsLoading(false)
    setCombinedProgress(40)
    setCombinedMessage(t('comparison_matrix_page.phase_generating'))

    // Phase 2: Generate comparison matrix
    setCombinedPhase('generating_matrix')

    try {
      const matrixResponse = await api.generateComparisonMatrix(topic, {
        reuseTaskId: currentSearchTaskId,
        language: isChineseSite ? 'zh' : 'en'
      })

      if (!matrixResponse.success || !matrixResponse.data?.task_id) {
        setSearchError(matrixResponse.message || t('comparison_matrix_page.error'))
        setCombinedPhase('idle')
        return
      }

      const matrixTaskId = matrixResponse.data.task_id
      localStorage.setItem('cm_matrix_task_id', matrixTaskId)
      await pollMatrixResult(matrixTaskId)
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || t('comparison_matrix_page.error')
      if (errorMsg.toLowerCase().includes('credit') || errorMsg.toLowerCase().includes('积分')) {
        setPendingTopic(topic)
        setSearchError('')
        setCombinedPhase('idle')
        localStorage.removeItem('cm_matrix_task_id')
        setShowPaymentModal('starter')
      } else {
        setSearchError(errorMsg)
        setCombinedPhase('idle')
        localStorage.removeItem('cm_matrix_task_id')
      }
    }
  }, [topic, t, isChineseSite, navigate])

  const handlePaymentSuccess = async () => {
    setShowPaymentModal(false)
    api.getCredits().then(data => {
      setCredits(data.credits)
    }).catch(() => {})
    if (pendingTopic) {
      const topicToGenerate = pendingTopic
      setPendingTopic('')
      setTopic(topicToGenerate)
      await handleGenerateAll()
    }
  }

  const handleGenerateReview = async () => {
    if (!topic.trim()) return

    if (!checkLoggedIn()) {
      setShowLoginModal(true)
      return
    }

    // Check credits and confirm
    try {
      const creditsData = await api.getCredits()
      setCredits(creditsData.credits)
      if (creditsData.credits < 1) {
        setShowPaymentModal('starter')
        return
      }
    } catch { /* proceed */ }
    setShowCreditConfirm(true)
  }

  const doGenerateReview = async () => {
    if (!topic.trim()) return

    try {
      const activeTask = await api.getActiveTask()
      if (activeTask.active && activeTask.task_id) {
        setSearchError('You already have a review in progress. Redirecting to view progress...')
        setTimeout(() => {
          navigate(`/generate?task_id=${activeTask.task_id}`)
        }, 1500)
        return
      }
    } catch { /* don't block */ }

    try {
      const response = await api.submitReviewTask(topic, {
        language: isChineseSite ? 'zh' : 'en',
        reuseTaskId: localStorage.getItem('cm_search_task_id') || '',
      })

      if (response.success && response.data?.task_id) {
        navigate(`/generate?task_id=${response.data.task_id}`)
      } else {
        const msg = response.message || ''
        if (msg.includes('credits') || msg.includes('积分')) {
          setShowPaymentModal('starter')
        } else {
          setSearchError(msg || 'Something went wrong')
        }
      }
    } catch {
      setSearchError('Something went wrong')
    }
  }

  const handleSearch = useCallback(async () => {
    if (!topic.trim()) return

    if (!checkLoggedIn()) {
      setShowLoginModal(true)
      return
    }

    setIsLoading(true)
    setSearchError('')
    setPapers([])
    setStatistics(null)
    setHasSearched(true)
    setSortMode('citations')
    localStorage.setItem('cm_topic', topic)

    try {
      const response = await api.searchPapersOnly(topic, {
        targetCount: 30,
        searchYears: 10
      })

      if (response.success && response.data) {
        const foundPapers = response.data.all_papers || []
        const stats = response.data.statistics || null
        const tid = response.data.task_id || ''

        setPapers(foundPapers)
        setStatistics(stats)

        localStorage.setItem('cm_papers', JSON.stringify(foundPapers))
        localStorage.setItem('cm_statistics', JSON.stringify(stats))
        localStorage.setItem('cm_search_task_id', tid)
        localStorage.setItem('cm_has_searched', 'true')

      } else {
        setSearchError(response.message || t('comparison_matrix_page.error'))
      }
    } catch (err: any) {
      if (err.response?.status === 429) {
        setSearchError(t('search_papers.input.limit_exceeded_full'))

      } else if (err.code === 'ECONNABORTED' || err.message?.includes('timeout')) {
        setSearchError(t('search_papers.error.timeout'))
      } else {
        setSearchError(t('comparison_matrix_page.error'))
      }
    } finally {
      setIsLoading(false)
    }
  }, [topic, t])

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && combinedPhase === 'idle' && topic.trim()) {
      handleGenerateAll()
    }
  }

  const sortedPapers = (() => {
    const sorted = [...papers]
    if (sortMode === 'year') {
      sorted.sort((a, b) => (b.year || 0) - (a.year || 0))
    } else {
      sorted.sort((a, b) => (b.cited_by_count || 0) - (a.cited_by_count || 0))
    }
    return sorted
  })()

  const renderNav = () => (
    <nav className="home-nav">
      <div className="nav-logo" onClick={() => navigate('/')} style={{ cursor: 'pointer' }}>
        <span className="logo-icon">📚</span>
        <span className="logo-text">{isChineseSite ? '澹墨学术' : 'AutoOverview'}</span>
      </div>
      <div className="nav-links">
        <a href="/" className={location.pathname === '/' ? 'active' : ''} onClick={(e) => { e.preventDefault(); navigate('/') }}>{t('nav.home')}</a>
        <a href="/search-papers" className={location.pathname === '/search-papers' ? 'active' : ''} onClick={(e) => { e.preventDefault(); navigate('/search-papers') }}>{t('search_papers.nav.search')}</a>
        <a href="/comparison-matrix" className={location.pathname === '/comparison-matrix' ? 'active' : ''} onClick={(e) => { e.preventDefault(); navigate('/comparison-matrix') }}>{t('search_papers.nav.comparison_matrix')}</a>
        <a href="/generate" className={location.pathname === '/generate' ? 'active' : ''} onClick={(e) => { e.preventDefault(); navigate('/generate') }}>{t('search_papers.nav.generate')}</a>
        <a href="/#pricing" onClick={(e) => { e.preventDefault(); navigate('/#pricing') }}>{t('home.nav.pricing')}</a>
      </div>
      <div className="nav-actions">
        {loggedIn ? (
          <div className="user-menu">
            <button className="user-info" onClick={() => navigate('/profile')}>
              <span className="user-avatar">👤</span>
              <span className="user-name">{t('home.nav.profile')}</span>
            </button>
          </div>
        ) : (
          <div className="auth-buttons">
            <button className="nav-btn nav-btn-register" onClick={() => setShowLoginModal(true)}>
              {t('home.nav.login_register')}
            </button>
          </div>
        )}
      </div>
      <button className="mobile-menu-toggle" onClick={() => setMobileMenuOpen(!mobileMenuOpen)}>
        <span className={`hamburger ${mobileMenuOpen ? 'open' : ''}`} />
      </button>
    </nav>
  )

  const renderMobileSidebar = () => (
    <>
      {mobileMenuOpen && (
        <div className="mobile-sidebar-overlay" onClick={() => setMobileMenuOpen(false)} />
      )}
      <aside className={`mobile-sidebar ${mobileMenuOpen ? 'sidebar-open' : ''}`}>
        <div className="sidebar-header">
          <span className="logo-icon">📚</span>
          <span className="logo-text">{isChineseSite ? '澹墨学术' : 'AutoOverview'}</span>
          <button className="sidebar-close" onClick={() => setMobileMenuOpen(false)}>&times;</button>
        </div>
        <nav className="sidebar-links">
          <a href="/" className={location.pathname === '/' ? 'active' : ''} onClick={(e) => { e.preventDefault(); setMobileMenuOpen(false); navigate('/') }}>{t('nav.home')}</a>
          <a href="/search-papers" className={location.pathname === '/search-papers' ? 'active' : ''} onClick={(e) => { e.preventDefault(); setMobileMenuOpen(false); navigate('/search-papers') }}>{t('search_papers.nav.search')}</a>
          <a href="/comparison-matrix" className={location.pathname === '/comparison-matrix' ? 'active' : ''} onClick={(e) => { e.preventDefault(); setMobileMenuOpen(false) }}>{t('search_papers.nav.comparison_matrix')}</a>
          <a href="/generate" className={location.pathname === '/generate' ? 'active' : ''} onClick={(e) => { e.preventDefault(); setMobileMenuOpen(false); navigate('/generate') }}>{t('search_papers.nav.generate')}</a>
          <a href="/#pricing" onClick={(e) => { e.preventDefault(); setMobileMenuOpen(false); navigate('/#pricing') }}>{t('home.nav.pricing')}</a>
        </nav>
        <div className="sidebar-bottom">
          {loggedIn ? (
            <button className="sidebar-user-btn" onClick={() => { setMobileMenuOpen(false); navigate('/profile') }}>
              <span className="user-avatar">👤</span>
              <span className="user-name">{t('home.nav.profile')}</span>
            </button>
          ) : (
            <button className="nav-btn nav-btn-register" onClick={() => { setMobileMenuOpen(false); setShowLoginModal(true) }}>
              {t('home.nav.login_register')}
            </button>
          )}
        </div>
      </aside>
    </>
  )

  const LoginModalComponent = isChineseSite ? LoginModal : LoginModalInternational

  const creditConfirmMessage = isChineseSite
    ? `您有 ${credits} 个积分。\n生成文献综述将消耗 1 个积分，是否继续？`
    : `You have ${credits} credits.\nGenerate a Literature Summary will use 1 credit. Continue?`
  const creditConfirmBtn = isChineseSite ? '生成' : 'Generate'
  const creditCancelBtn = isChineseSite ? '取消' : 'Cancel'

  return (
    <div className="search-papers-page">
      {renderNav()}
      {renderMobileSidebar()}

      {/* Hero */}
      <div className="sp-hero">
        <span className="sp-hero-badge">{t('comparison_matrix_page.hero_badge')}</span>
        <h1>{t('comparison_matrix_page.hero_title')}</h1>
        <p className="sp-hero-subtitle">{t('comparison_matrix_page.hero_subtitle')}</p>
      </div>

      {/* Search Input */}
      <div className="sp-search-section">
        <div className="sp-search-card">
          <textarea
            className="sp-search-input"
            placeholder={t('comparison_matrix_page.search_placeholder')}
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={combinedPhase !== 'idle'}
            rows={2}
          />
          <div className="sp-search-actions">
            <button
              className="sp-search-btn"
              onClick={handleGenerateAll}
              disabled={combinedPhase !== 'idle' || !topic.trim()}
            >
              {combinedPhase !== 'idle' ? t('comparison_matrix_page.generating_matrix') : t('comparison_matrix_page.btn_generate_all')}
            </button>
          </div>
          {loggedIn && (
            <p className={`sp-search-limit ${credits === 0 ? 'zero' : ''}`}>
              {t('home.input.credits_remaining', { count: credits })}
            </p>
          )}
          <p className="sp-search-helper">{t('search_papers.input.helper')}</p>
          {loggedIn && (
            <div className="sp-search-history-link">
              <button
                className="sp-history-btn"
                onClick={() => navigate('/profile?tab=matrices')}
              >
                {t('comparison_matrix_page.history')}
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Combined progress bar */}
      {combinedPhase !== 'idle' && (
        <div className="sp-loading">
          <div className="sp-loading-card">
            <div className="sp-progress-bar">
              <div className="sp-progress-fill" style={{ width: `${combinedProgress}%`, transition: 'width 0.5s ease' }} />
            </div>
            <p className="sp-loading-status">{combinedMessage}</p>
            <p className="sp-loading-estimate">{t('comparison_matrix_page.estimate')}</p>
          </div>
        </div>
      )}

      {/* Data Sources */}
      <div className="sp-sources">
        <p className="sp-sources-title">{t('home.sources.title')}</p>
        <div className="sp-sources-logos">
          <a href="https://webofscience.com" target="_blank" rel="noopener noreferrer" className="sp-source-logo">Web of Science</a>
          <a href="https://ieeexplore.ieee.org" target="_blank" rel="noopener noreferrer" className="sp-source-logo">IEEE Xplore</a>
          <a href="https://crossref.org" target="_blank" rel="noopener noreferrer" className="sp-source-logo">CrossRef</a>
          <a href="https://semanticscholar.org" target="_blank" rel="noopener noreferrer" className="sp-source-logo">Semantic Scholar</a>
        </div>
      </div>

      {/* Error */}
      {searchError && !isLoading && (
        <div className="sp-error">
          <div className="sp-error-card">
            <p className="sp-error-message">{searchError}</p>
            <button className="sp-error-retry" onClick={handleSearch}>
              {t('search_papers.error.retry')}
            </button>
          </div>
        </div>
      )}

      {/* Pending generation */}
      {pendingTopic && !searchError && (
        <div className="sp-error">
          <div className="sp-error-card">
            <p className="sp-error-message">
              {isChineseSite
                ? '您需要积分才能生成对比矩阵。购买积分后继续。'
                : 'You need credits to generate the comparison matrix. Purchase credits and then continue.'}
            </p>
            <div style={{ display: 'flex', gap: '12px', justifyContent: 'center' }}>
              <button
                className="sp-error-retry"
                onClick={() => setShowPaymentModal('starter')}
              >
                {isChineseSite ? '购买积分' : 'Purchase Credits'}
              </button>
              <button
                className="sp-error-retry"
                style={{ backgroundColor: '#10b981' }}
                onClick={() => {
                  const topicToGenerate = pendingTopic
                  setPendingTopic('')
                  setTopic(topicToGenerate)
                  handleGenerateAll()
                }}
              >
                {isChineseSite ? '继续生成' : 'Continue Generation'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Literature Summary CTA */}
      {hasSearched && !isLoading && papers.length > 0 && (
        <div className="sp-review-cta">
          <div className="sp-review-cta-card">
            <div className="sp-review-cta-icon">📝</div>
            <div className="sp-review-cta-content">
              <h3>{t('comparison_matrix_page.review_cta_title')}</h3>
              <p>{t('comparison_matrix_page.review_cta_desc')}</p>
            </div>
            <button className="sp-review-cta-btn" onClick={handleGenerateReview}>
              {t('comparison_matrix_page.review_cta_button')}
            </button>
          </div>
        </div>
      )}

      {/* Statistics */}
      {statistics && !isLoading && papers.length > 0 && (
        <div className="sp-statistics">
          <div className="sp-statistics-bar">
            <span className="sp-stat-badge">
              <span className="sp-stat-number">{statistics.total}</span> {t('search_papers.results.found')}
            </span>
            <span className="sp-stat-badge">
              {Math.round(statistics.recent_ratio * 100)}% {t('search_papers.results.recent')}
            </span>
            <span className="sp-stat-badge">
              {Math.round(statistics.english_ratio * 100)}% {t('search_papers.results.english')}
            </span>
            <span className="sp-stat-badge">
              {Math.round(statistics.avg_citations)} {t('search_papers.results.avg_citations')}
            </span>
          </div>
        </div>
      )}

      {/* Results */}
      {papers.length > 0 && (
        <div className="sp-results">
          <div className="sp-results-header">
            <div className="sp-sort-controls">
              <span>{t('search_papers.results.sort_by')}:</span>
              {(['citations', 'year'] as SortMode[]).map(mode => (
                <button
                  key={mode}
                  className={`sp-sort-btn ${sortMode === mode ? 'active' : ''}`}
                  onClick={() => setSortMode(mode)}
                  disabled={combinedPhase !== 'idle'}
                >
                  {t(`search_papers.results.sort_${mode}`)}
                </button>
              ))}
            </div>
          </div>

          {sortedPapers.map((paper, index) => (
            <div key={paper.id || index} className="sp-paper-card">
              <div className="sp-paper-top">
                <span className="sp-paper-number">[{index + 1}]</span>
                <div className="sp-paper-title">
                  {paper.doi ? (
                    <a href={`https://doi.org/${paper.doi}`} target="_blank" rel="noopener noreferrer">
                      {paper.title}
                    </a>
                  ) : (
                    paper.title
                  )}
                </div>
              </div>
              <div className="sp-paper-meta">
                {paper.year && (
                  <span className="sp-paper-tag sp-tag-year">{paper.year}</span>
                )}
                {paper.cited_by_count > 0 && (
                  <span className="sp-paper-tag sp-tag-citations">
                    {paper.cited_by_count} {t('search_papers.paper.citations')}
                  </span>
                )}
                {paper.is_english && (
                  <span className="sp-paper-tag sp-tag-lang">EN</span>
                )}
              </div>
              {paper.abstract && (
                <p className="sp-paper-abstract">
                  {paper.abstract.length > 250
                    ? paper.abstract.substring(0, 250) + '...'
                    : paper.abstract
                  }
                </p>
              )}
              {paper.authors && paper.authors.length > 0 && (
                <p className="sp-paper-authors">
                  {paper.authors.slice(0, 4).join(', ')}
                  {paper.authors.length > 4 && ` ${t('search_papers.paper.et_al')}`}
                </p>
              )}
            </div>
          ))}
        </div>
      )}

      {/* No results */}
      {hasSearched && combinedPhase === 'idle' && papers.length === 0 && !searchError && (
        <div className="sp-no-results">
          <div className="sp-no-results-card">
            <div className="sp-no-results-icon">🔍</div>
            <p className="sp-no-results-text">{t('comparison_matrix_page.no_results')}</p>
          </div>
        </div>
      )}

      {/* Footer */}
      <footer className="sp-footer">
        <div className="sp-footer-links">
          <a href="/terms-and-conditions">{t('search_papers.footer.terms')}</a>
          <a href="/privacy-policy">{t('search_papers.footer.privacy')}</a>
          <a href="/refund-policy">{t('search_papers.footer.refund')}</a>
        </div>
        <p>{t('search_papers.footer.copyright')}</p>
      </footer>

      {showLoginModal && (
        <LoginModalComponent onClose={() => setShowLoginModal(false)} onLoginSuccess={handleLoginSuccess} />
      )}

      {showPaymentModal && (
        <PayPalPaymentModal
          onClose={() => setShowPaymentModal(false)}
          onPaymentSuccess={handlePaymentSuccess}
          planType={showPaymentModal}
        />
      )}

      {/* Credit Confirm Modal */}
      {showCreditConfirm && isChineseSite && (
        <ConfirmModal
          title="确认扣除积分"
          message={creditConfirmMessage}
          confirmText={creditConfirmBtn}
          cancelText={creditCancelBtn}
          onConfirm={() => { setShowCreditConfirm(false); doGenerateReview() }}
          onCancel={() => setShowCreditConfirm(false)}
          type="warning"
        />
      )}
      {showCreditConfirm && !isChineseSite && (
        <ConfirmModalInternational
          message={creditConfirmMessage}
          confirmText={creditConfirmBtn}
          cancelText={creditCancelBtn}
          onConfirm={() => { setShowCreditConfirm(false); doGenerateReview() }}
          onCancel={() => setShowCreditConfirm(false)}
          type="warning"
        />
      )}
    </div>
  )
}
