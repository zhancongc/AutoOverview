/**
 * GenerateReviewPage - 独立的文献综述生成页面
 * 从首页脱钩，专注于综述生成流程：输入 → 提交 → 进度条 → 跳转结果
 */
import { useState, useEffect, useRef } from 'react'
import { useNavigate, useSearchParams, useLocation } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { api } from '../api'
import { isLoggedIn as checkLoggedIn } from '../authApi'
import { LoginModal } from './LoginModal'
import { PaymentModal } from './PaymentModal'
import { PayPalPaymentModal } from './PayPalPaymentModal'
import './SimpleApp.css'
import './SearchPapersPage.css'

interface TaskProgress {
  step: string
  message: string
}

export function GenerateReviewPage() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const location = useLocation()
  const [searchParams] = useSearchParams()

  const [isChineseSite, setIsChineseSite] = useState(false)
  const [topic, setTopic] = useState('')
  const [language, setLanguage] = useState<'zh' | 'en'>('zh')
  const [isGenerating, setIsGenerating] = useState(false)
  const [progress, setProgress] = useState<TaskProgress | null>(null)
  const [error, setError] = useState('')
  const [showLoginModal, setShowLoginModal] = useState(false)
  const [showPaymentModal, setShowPaymentModal] = useState<string | false>(false)
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [credits, setCredits] = useState<number>(0)
  const [prevCredits, setPrevCredits] = useState<number>(0)
  const [showToast, setShowToast] = useState(false)
  const [toastMessage, setToastMessage] = useState('')
  const isPollingRef = useRef(false)

  useEffect(() => {
    setIsChineseSite(!document.documentElement.classList.contains('intl'))
  }, [])

  useEffect(() => {
    const loggedIn = checkLoggedIn()
    setIsLoggedIn(loggedIn)
    if (loggedIn) {
      api.getCredits().then(data => setCredits(data.credits)).catch(() => {})
      // 检查是否有进行中的任务
      api.getActiveTask().then(data => {
        if (data.active && data.task_id) {
          isPollingRef.current = true
          setTopic(data.topic || '')
          setIsGenerating(true)
          setProgress({ step: 'processing', message: t('home.progress.restoring') })
          sessionStorage.setItem('active_task_id', data.task_id)
          sessionStorage.setItem('active_task_topic', data.topic || '')
          pollTask(data.task_id)
        }
      }).catch(() => {})
    }
  }, [])

  // URL 参数处理
  useEffect(() => {
    const taskIdParam = searchParams.get('task_id')
    if (taskIdParam) {
      isPollingRef.current = true
      setIsGenerating(true)
      setProgress({ step: 'processing', message: t('home.progress.processing') })
      sessionStorage.setItem('active_task_id', taskIdParam)
      pollTask(taskIdParam)
      window.history.replaceState({}, '', '/generate')
      return
    }

    const reuseTaskId = searchParams.get('reuse_task_id')
    const reuseTopic = searchParams.get('topic')
    if (reuseTaskId && reuseTopic) {
      setTopic(reuseTopic)
      sessionStorage.setItem('reuse_task_id', reuseTaskId)
      sessionStorage.setItem('pending_topic', reuseTopic)
      window.history.replaceState({}, '', '/generate')
    }
  }, [searchParams])

  useEffect(() => {
    const pendingTopic = sessionStorage.getItem('pending_topic')
    if (pendingTopic) {
      sessionStorage.removeItem('pending_topic')
      setTopic(pendingTopic)
    }
  }, [])

  const pollTask = (taskId: string) => {
    const startTime = Date.now()
    const doPoll = async () => {
      try {
        const statusResponse = await api.getTaskStatus(taskId)
        if (!statusResponse.success) {
          sessionStorage.removeItem('active_task_id')
          sessionStorage.removeItem('active_task_topic')
          setIsGenerating(false)
          isPollingRef.current = false
          return
        }

        const taskInfo = statusResponse.data
        if (taskInfo.status === 'completed' && taskInfo.result) {
          sessionStorage.removeItem('active_task_id')
          sessionStorage.removeItem('active_task_topic')
          isPollingRef.current = false
          navigate(`/review?task_id=${taskId}`)
          return
        } else if (taskInfo.status === 'failed') {
          sessionStorage.removeItem('active_task_id')
          sessionStorage.removeItem('active_task_topic')
          setError(taskInfo.error || t('home.errors.task_failed'))
          setIsGenerating(false)
          isPollingRef.current = false
          return
        }

        setProgress({ step: taskInfo.progress?.step || 'processing', message: taskInfo.progress?.message || t('home.progress.processing') })

        const elapsed = Date.now() - startTime
        const elapsedMinutes = elapsed / (60 * 1000)
        let nextInterval: number
        if (elapsedMinutes < 1) {
          nextInterval = 20000
        } else if (elapsedMinutes < 3) {
          nextInterval = 15000
        } else {
          nextInterval = 10000
        }
        setTimeout(doPoll, nextInterval)
      } catch {
        sessionStorage.removeItem('active_task_id')
        sessionStorage.removeItem('active_task_topic')
        setIsGenerating(false)
        isPollingRef.current = false
      }
    }
    setTimeout(doPoll, 5000)
  }

  const handleGenerate = async () => {
    if (!topic.trim()) {
      setError(t('generate_page.error_empty'))
      return
    }

    if (!checkLoggedIn()) {
      setShowLoginModal(true)
      return
    }

    setIsGenerating(true)
    setProgress({ step: 'init', message: t('generate_page.submitting') })
    setError('')

    try {
      const submitResponse = await api.submitReviewTask(topic, {
        language,
        targetCount: 50,
        recentYearsRatio: 0.5,
        englishRatio: 0.3,
        searchYears: 10,
        maxSearchQueries: 8
      })

      if (!submitResponse.success || !submitResponse.data?.task_id) {
        if (submitResponse.message?.includes('额度已用完') || submitResponse.message?.includes('credits')) {
          setError(submitResponse.message)
          setShowPaymentModal('single')
        } else {
          setError(submitResponse.message || t('generate_page.error_submit'))
        }
        setIsGenerating(false)
        return
      }

      const taskId = submitResponse.data.task_id
      sessionStorage.setItem('active_task_id', taskId)
      sessionStorage.setItem('active_task_topic', topic)
      const startTime = Date.now()

      const doPoll = async () => {
        try {
          const statusResponse = await api.getTaskStatus(taskId)

          if (!statusResponse.success) {
            setError(t('generate_page.error_status'))
            setIsGenerating(false)
            return
          }

          const taskInfo = statusResponse.data
          const elapsedMinutes = (Date.now() - startTime) / 1000 / 60
          let expectedRemainingMinutes = Math.max(0, Math.round(5 - elapsedMinutes))

          let progressMessage = taskInfo.progress?.message || t('home.progress.processing')
          if (expectedRemainingMinutes > 0) {
            progressMessage += `（${t('generate_page.estimated_remaining')}${expectedRemainingMinutes}${t('generate_page.minutes')}）`
          }

          setProgress({
            step: taskInfo.progress?.step || 'processing',
            message: progressMessage
          })

          if (taskInfo.status === 'completed' && taskInfo.result) {
            setProgress({ step: 'completed', message: t('generate_page.completed') })
            sessionStorage.removeItem('active_task_id')
            sessionStorage.removeItem('active_task_topic')
            setTimeout(() => {
              navigate(`/review?task_id=${taskId}`)
            }, 500)
            return
          } else if (taskInfo.status === 'failed') {
            sessionStorage.removeItem('active_task_id')
            sessionStorage.removeItem('active_task_topic')
            setError(taskInfo.error || t('generate_page.error_task_failed'))
            setIsGenerating(false)
            return
          }

          let nextInterval: number
          if (elapsedMinutes < 1) {
            nextInterval = 20000
          } else if (elapsedMinutes < 3) {
            nextInterval = 15000
          } else if (elapsedMinutes < 5) {
            nextInterval = 10000
          } else {
            nextInterval = 8000
          }

          setTimeout(doPoll, nextInterval)
        } catch {
          setError(t('generate_page.error_status'))
          setIsGenerating(false)
        }
      }

      setTimeout(doPoll, 3000)
    } catch {
      setError(t('generate_page.error_network'))
      setIsGenerating(false)
    }
  }

  const handleLoginSuccess = () => {
    const loggedIn = checkLoggedIn()
    setIsLoggedIn(loggedIn)
    setShowLoginModal(false)
    if (loggedIn) {
      api.getCredits().then(data => setCredits(data.credits)).catch(() => {})
    }
  }

  const handlePaymentSuccess = async () => {
    setShowPaymentModal(false)
    setError('')
    try {
      const data = await api.getCredits()
      setPrevCredits(credits)
      setCredits(data.credits)
      setToastMessage(t('common.payment_success'))
      setShowToast(true)
      setTimeout(() => setShowToast(false), 3000)
    } catch {}
  }

  const getProgressPercentage = () => {
    if (!progress) return 0
    switch (progress.step) {
      case 'init': return 5
      case 'waiting': return 5
      case 'generating_outline': return 15
      case 'analyzing': return 20
      case 'optimizing_keywords': return 25
      case 'searching': return 40
      case 'filtering': return 60
      case 'topic_relevance_check': return 65
      case 'generating': return 80
      case 'validating': return 90
      case 'completed': return 100
      default: return 5
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !isGenerating && topic.trim()) {
      handleGenerate()
    }
  }

  // Esc 关闭弹窗
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        if (showLoginModal) setShowLoginModal(false)
        if (showPaymentModal) setShowPaymentModal(false)
        if (mobileMenuOpen) setMobileMenuOpen(false)
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [showLoginModal, showPaymentModal, mobileMenuOpen])

  const renderNav = () => (
    <nav className="home-nav">
      <div className="nav-logo" onClick={() => navigate('/')} style={{ cursor: 'pointer' }}>
        <span className="logo-icon">📚</span>
        <span className="logo-text">AutoOverview</span>
      </div>
      <div className="nav-links">
        <a href="/" className={location.pathname === '/' ? 'active' : ''} onClick={(e) => { e.preventDefault(); navigate('/') }}>{t('nav.home')}</a>
        <a href="/search-papers" className={location.pathname === '/search-papers' ? 'active' : ''} onClick={(e) => { e.preventDefault(); navigate('/search-papers') }}>{t('search_papers.nav.search')}</a>
        <a href="/comparison-matrix" className={location.pathname === '/comparison-matrix' ? 'active' : ''} onClick={(e) => { e.preventDefault(); navigate('/comparison-matrix') }}>{t('search_papers.nav.comparison_matrix')}</a>
        <a href="/generate" className={location.pathname === '/generate' ? 'active' : ''} onClick={(e) => { e.preventDefault() }}>{t('search_papers.nav.generate')}</a>
      </div>
      <div className="nav-actions">
        {isLoggedIn ? (
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
          <span className="logo-text">AutoOverview</span>
          <button className="sidebar-close" onClick={() => setMobileMenuOpen(false)}>&times;</button>
        </div>
        <nav className="sidebar-links">
          <a href="/" className={location.pathname === '/' ? 'active' : ''} onClick={(e) => { e.preventDefault(); setMobileMenuOpen(false); navigate('/') }}>{t('nav.home')}</a>
          <a href="/search-papers" className={location.pathname === '/search-papers' ? 'active' : ''} onClick={(e) => { e.preventDefault(); setMobileMenuOpen(false); navigate('/search-papers') }}>{t('search_papers.nav.search')}</a>
          <a href="/comparison-matrix" className={location.pathname === '/comparison-matrix' ? 'active' : ''} onClick={(e) => { e.preventDefault(); setMobileMenuOpen(false); navigate('/comparison-matrix') }}>{t('search_papers.nav.comparison_matrix')}</a>
          <a href="/generate" className={location.pathname === '/generate' ? 'active' : ''} onClick={(e) => { e.preventDefault(); setMobileMenuOpen(false) }}>{t('search_papers.nav.generate')}</a>
        </nav>
        <div className="sidebar-bottom">
          {isLoggedIn ? (
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

  return (
    <div className="search-papers-page">
      {renderNav()}
      {renderMobileSidebar()}

      {/* Hero */}
      <div className="sp-hero">
        <span className="sp-hero-badge">{t('generate_page.hero_badge')}</span>
        <h1>{t('generate_page.title')}</h1>
        <p className="sp-hero-subtitle">{t('generate_page.subtitle')}</p>
      </div>

      {/* Input Card */}
      <div className="sp-search-section">
        <div className="sp-search-card">
          {isLoggedIn && (
            <span className={`credits-badge ${prevCredits !== credits ? 'credits-updated' : ''}`} style={{ marginBottom: '12px' }}>
              {t('input.credits_remaining')} <span className="credits-number">{credits}</span>
            </span>
          )}

          {/* Language toggle */}
          <div className="language-toggle-wrapper" style={{ marginBottom: '12px' }}>
            <span className="language-label">{t('input.language')}</span>
            <div className="language-toggle">
              <button
                className={`language-option ${language === 'zh' ? 'active' : ''}`}
                onClick={() => setLanguage('zh')}
                disabled={isGenerating}
              >
                {t('input.language_zh')}
              </button>
              <button
                className={`language-option ${language === 'en' ? 'active' : ''}`}
                onClick={() => setLanguage('en')}
                disabled={isGenerating}
              >
                {t('input.language_en')}
              </button>
            </div>
          </div>

          <textarea
            className="sp-search-input"
            placeholder={t('generate_page.placeholder')}
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleKeyDown(e) } }}
            disabled={isGenerating}
            rows={3}
          />

          <div className="sp-search-actions">
            <button
              className="sp-search-btn"
              onClick={handleGenerate}
              disabled={isGenerating || !topic.trim()}
            >
              {isGenerating ? t('input.button_generating') : t('generate_page.button')}
            </button>
          </div>

          {error && !isGenerating && (
            <div className="home-error" style={{ marginTop: '12px' }}>
              <span>{error}</span>
              <button className="retry-button" onClick={handleGenerate}>{t('input.retry')}</button>
            </div>
          )}
        </div>

        <div className="social-proof-bar">
          <span className="social-proof-icon">🏆</span>
          <span className="social-proof-text" dangerouslySetInnerHTML={{ __html: t('home.social_proof.text') }} />
        </div>
      </div>

      {/* Progress */}
      {isGenerating && progress && (
        <div className="sp-loading">
          <div className="sp-loading-card">
            <div className="progress-bar" style={{ width: '100%', height: '8px', background: '#e0e0e0', borderRadius: '4px', overflow: 'hidden', marginBottom: '12px' }}>
              <div
                className="progress-fill"
                style={{
                  width: `${getProgressPercentage()}%`,
                  height: '100%',
                  background: 'linear-gradient(90deg, #e67e22, #d35400)',
                  borderRadius: '4px',
                  transition: 'width 0.5s ease'
                }}
              />
            </div>
            <p className="sp-loading-status">{progress.message}</p>
            <p className="sp-loading-estimate">{t('generate_page.estimate')}</p>
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

      {/* Footer */}
      <footer className="sp-footer">
        <div className="sp-footer-links">
          <a href="/terms-and-conditions">{t('search_papers.footer.terms')}</a>
          <a href="/privacy-policy">{t('search_papers.footer.privacy')}</a>
          <a href="/refund-policy">{t('search_papers.footer.refund')}</a>
        </div>
        <p className="sp-footer-copy">&copy; {new Date().getFullYear()} AutoOverview. {t('search_papers.footer.rights')}</p>
      </footer>

      {/* Modals */}
      {showLoginModal && <LoginModal onClose={() => setShowLoginModal(false)} onLoginSuccess={handleLoginSuccess} />}
      {showPaymentModal && !isChineseSite && (
        <PayPalPaymentModal
          onClose={() => setShowPaymentModal(false)}
          onPaymentSuccess={handlePaymentSuccess}
          planType={showPaymentModal}
        />
      )}
      {showPaymentModal && isChineseSite && (
        <PaymentModal
          onClose={() => setShowPaymentModal(false)}
          onPaymentSuccess={handlePaymentSuccess}
          planType={showPaymentModal}
        />
      )}

      {/* Toast */}
      {showToast && (
        <div className="toast-notification">
          {toastMessage}
        </div>
      )}
    </div>
  )
}
