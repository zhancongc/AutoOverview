/**
 * SimpleApp Component - International Academic Version
 * Designed for overseas market with clean, professional academic style
 */
import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { api } from '../api'
import { isLoggedIn as checkLoggedIn, getLocalUserInfo } from '../authApi'
import { LoginModalInternational } from './LoginModalInternational'
import { PaymentModal } from './PaymentModal'
import { PaddlePaymentModal } from './PaddlePaymentModal'
import { CookieConsentBanner } from './CookieConsentBanner'
import './SimpleAppInternational.css'

interface TaskProgress {
  step: string
  message: string
}

export function SimpleAppInternational({ autoShowLogin }: { autoShowLogin?: boolean } = {}) {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const [topic, setTopic] = useState('')
  const [language] = useState<'zh' | 'en'>('en')
  const [isGenerating, setIsGenerating] = useState(false)
  const [progress, setProgress] = useState<TaskProgress | null>(null)
  const [, setError] = useState('')
  const [showLoginModal, setShowLoginModal] = useState(false)
  const [showPaymentModal, setShowPaymentModal] = useState<string | false>(false)
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [, setActiveTaskId] = useState<string | null>(null)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [, setUserInfo] = useState<any>(null)
  const [credits, setCredits] = useState<number>(0)
  const [prevCredits, setPrevCredits] = useState<number>(0)
  const [showToast, setShowToast] = useState(false)
  const [toastMessage, setToastMessage] = useState('')
  const [, setPlans] = useState<any[]>([])
  const [plansLoading, setPlansLoading] = useState(true)
  const [demoCases, setDemoCases] = useState<any[]>([])
  const [casesLoading, setCasesLoading] = useState(true)

  useEffect(() => {
    const loggedIn = checkLoggedIn()
    setIsLoggedIn(loggedIn)
    // Auto show login modal if not logged in and autoShowLogin is true
    if (!loggedIn && autoShowLogin) {
      setShowLoginModal(true)
    }
    if (loggedIn) {
      setUserInfo(getLocalUserInfo())
      api.getCredits().then(data => {
        setCredits(data.credits)
        setPrevCredits(data.credits)
      }).catch(err => console.error(t('home.errors.credits_fetch_failed'), err))
    }

    // Check for active task
    const activeTaskId = sessionStorage.getItem('active_task_id')
    const activeTaskTopic = sessionStorage.getItem('active_task_topic')
    if (activeTaskId && activeTaskTopic) {
      setActiveTaskId(activeTaskId)
      setTopic(activeTaskTopic)
      setProgress({ step: 'processing', message: t('home.progress.restoring') })
    }

    // Get pricing plans
    api.getSubscriptionPlans().then(data => {
      setPlans(data.plans)
      setPlansLoading(false)
    }).catch(err => {
      console.error(t('home.errors.plans_fetch_failed'), err)
      setPlansLoading(false)
    })

    // Get demo cases
    fetch('/api/cases')
      .then(res => res.json())
      .then(data => {
        if (data.success && data.data.cases) {
          setDemoCases(data.data.cases)
        }
        setCasesLoading(false)
      })
      .catch(err => {
        console.error('Failed to fetch demo cases:', err)
        setCasesLoading(false)
      })
  }, [t])

  const handleGenerate = async () => {
    if (!topic.trim()) {
      alert('Please enter a research topic')
      return
    }

    if (!isLoggedIn) {
      setShowLoginModal(true)
      sessionStorage.setItem('pending_topic', topic)
      return
    }

    setIsGenerating(true)
    setError('')
    setProgress(null)

    try {
      const submitResponse = await api.submitReviewTask(topic, {
        language: language,
        targetCount: 50,
        recentYearsRatio: 0.5,
        englishRatio: language === 'en' ? 0.8 : 0.3
      })

      if (!submitResponse.success || !submitResponse.data?.task_id) {
        const msg = submitResponse.message || ''
        if (msg.includes('credits') || msg.includes('额度')) {
          setError(msg)
          setShowPaymentModal('single')
        } else {
          setError(msg || t('home.errors.task_failed'))
        }
        setIsGenerating(false)
        return
      }

      const taskId = submitResponse.data.task_id
      setActiveTaskId(taskId)
      sessionStorage.setItem('active_task_id', taskId)
      sessionStorage.setItem('active_task_topic', topic)

      // Start polling
      const startTime = Date.now()
      const doPoll = async () => {
        try {
          const statusResponse = await api.getTaskStatus(taskId)

          if (!statusResponse.success) {
            setError(t('home.errors.task_failed'))
            setIsGenerating(false)
            return
          }

          const taskInfo = statusResponse.data
          const elapsedMinutes = (Date.now() - startTime) / 1000 / 60
          let expectedRemainingMinutes = Math.max(0, Math.round(5 - elapsedMinutes))

          let progressMessage = taskInfo.progress?.message || t('home.progress.processing')
          if (expectedRemainingMinutes > 0) {
            progressMessage += ` (${expectedRemainingMinutes} min remaining)`
          }

          setProgress({
            step: taskInfo.progress?.step || 'processing',
            message: progressMessage
          })

          if (taskInfo.status === 'completed' && taskInfo.result) {
            setProgress({ step: 'completed', message: 'Complete! Redirecting...' })
            sessionStorage.removeItem('active_task_id')
            sessionStorage.removeItem('active_task_topic')
            setTimeout(() => {
              navigate(`/review?task_id=${taskId}`)
            }, 500)
            return
          } else if (taskInfo.status === 'failed') {
            sessionStorage.removeItem('active_task_id')
            sessionStorage.removeItem('active_task_topic')
            setError(taskInfo.error || t('home.errors.task_failed'))
            setIsGenerating(false)
            setActiveTaskId(null)
            return
          }

          // Continue polling
          setTimeout(doPoll, 3000)
        } catch {
        }
      }

      setTimeout(doPoll, 3000)
    } catch (err) {
      setError(t('home.errors.task_failed'))
      setIsGenerating(false)
      console.error(err)
    }
  }

  const handleLoginSuccess = () => {
    const loggedIn = checkLoggedIn()
    setIsLoggedIn(loggedIn)
    if (loggedIn) {
      setUserInfo(getLocalUserInfo())
      api.getCredits().then(data => {
        setCredits(data.credits)
        setPrevCredits(data.credits)
      }).catch(err => console.error(t('home.errors.credits_refresh_failed'), err))
    }

    const pendingTopic = sessionStorage.getItem('pending_topic')
    if (pendingTopic) {
      setTopic(pendingTopic)
      sessionStorage.removeItem('pending_topic')
      handleGenerate()
    }
  }

  const handleLogout = () => {
    localStorage.removeItem('auth_token')
    localStorage.removeItem('user_info')
    navigate('/')
  }

  const handlePaymentSuccess = async (_addedCredits: number = 0) => {
    setShowPaymentModal(false)
    setUserInfo(getLocalUserInfo())
    setError('')

    api.getCredits().then(data => {
      setPrevCredits(credits)
      setCredits(data.credits)
      if (data.credits > prevCredits) {
        setShowToast(true)
        setToastMessage(t('common.payment_success'))
        setTimeout(() => setShowToast(false), 3000)
      }
    }).catch(err => {
      console.error(t('home.errors.credits_refresh_failed'), err)
    })

    // Scroll to generate section
    document.getElementById('generate')?.scrollIntoView({ behavior: 'smooth' })
  }

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

  return (
    <div className="simple-home simple-home-international">
      <nav className="home-nav">
        <div className="nav-logo" onClick={() => navigate('/')} style={{ cursor: 'pointer' }}>
          <span className="logo-icon">📚</span>
          <span className="logo-text">AutoOverview</span>
        </div>
        <div className="nav-links">
          <a
            href="#generate"
            onClick={(e) => {
              e.preventDefault()
              const el = document.getElementById('generate')
              if (el) {
                const navHeight = 60
                const elPosition = el.getBoundingClientRect().top + window.pageYOffset
                window.location.hash = 'generate'
                window.scrollTo({ top: elPosition - navHeight, behavior: 'smooth' })
              }
            }}
          >{t('home.nav.generate')}</a>
          <a
            href="#features"
            onClick={(e) => {
              e.preventDefault()
              const el = document.getElementById('features')
              if (el) {
                const navHeight = 60
                const elPosition = el.getBoundingClientRect().top + window.pageYOffset
                window.location.hash = 'features'
                window.scrollTo({ top: elPosition - navHeight, behavior: 'smooth' })
              }
            }}
          >{t('home.nav.features')}</a>
          <a
            href="#process"
            onClick={(e) => {
              e.preventDefault()
              const el = document.getElementById('process')
              if (el) {
                const navHeight = 60
                const elPosition = el.getBoundingClientRect().top + window.pageYOffset
                window.location.hash = 'process'
                window.scrollTo({ top: elPosition - navHeight, behavior: 'smooth' })
              }
            }}
          >{t('home.nav.process')}</a>
          <a
            href="#cases"
            onClick={(e) => {
              e.preventDefault()
              const el = document.getElementById('cases')
              if (el) {
                const navHeight = 60
                const elPosition = el.getBoundingClientRect().top + window.pageYOffset
                window.location.hash = 'cases'
                window.scrollTo({ top: elPosition - navHeight, behavior: 'smooth' })
              }
            }}
          >{t('home.nav.cases')}</a>
          <a
            href="#pricing"
            onClick={(e) => {
              e.preventDefault()
              const el = document.getElementById('pricing')
              if (el) {
                const navHeight = 60
                const elPosition = el.getBoundingClientRect().top + window.pageYOffset
                window.location.hash = 'pricing'
                window.scrollTo({ top: elPosition - navHeight, behavior: 'smooth' })
              }
            }}
          >{t('home.nav.pricing')}</a>
        </div>
        <div className="nav-actions">
          {isLoggedIn ? (
            <div className="user-menu">
              <button className="user-info" onClick={() => navigate('/profile')}>
                <span className="user-avatar">👤</span>
                <span className="user-name">{t('home.nav.profile')}</span>
              </button>
              <button className="nav-btn nav-btn-logout" onClick={handleLogout}>
                {t('home.nav.logout')}
              </button>
            </div>
          ) : (
            <div className="auth-buttons">
              <button
                className="nav-btn nav-btn-register"
                onClick={() => setShowLoginModal(true)}
              >
                {t('home.nav.login_register')}
              </button>
            </div>
          )}
        </div>
        <button className="mobile-menu-toggle" onClick={() => setMobileMenuOpen(!mobileMenuOpen)}>
          <span className={`hamburger ${mobileMenuOpen ? 'open' : ''}`} />
        </button>
      </nav>

      {/* Mobile sidebar overlay */}
      {mobileMenuOpen && (
        <div className="mobile-sidebar-overlay" onClick={() => setMobileMenuOpen(false)} />
      )}

      {/* Mobile sidebar */}
      <aside className={`mobile-sidebar ${mobileMenuOpen ? 'sidebar-open' : ''}`}>
        <div className="sidebar-header">
          <span className="logo-icon">📚</span>
          <span className="logo-text">AutoOverview</span>
          <button className="sidebar-close" onClick={() => setMobileMenuOpen(false)}>&times;</button>
        </div>
        <nav className="sidebar-links">
          <a
            href="#generate"
            onClick={(e) => {
              e.preventDefault()
              setMobileMenuOpen(false)
              const el = document.getElementById('generate')
              if (el) {
                window.location.hash = 'generate'
                el.scrollIntoView({ behavior: 'smooth', block: 'start' })
              }
            }}
          >{t('home.nav.generate')}</a>
          <a
            href="#features"
            onClick={(e) => {
              e.preventDefault()
              setMobileMenuOpen(false)
              const el = document.getElementById('features')
              if (el) {
                window.location.hash = 'features'
                el.scrollIntoView({ behavior: 'smooth', block: 'start' })
              }
            }}
          >{t('home.nav.features')}</a>
          <a
            href="#process"
            onClick={(e) => {
              e.preventDefault()
              setMobileMenuOpen(false)
              const el = document.getElementById('process')
              if (el) {
                window.location.hash = 'process'
                el.scrollIntoView({ behavior: 'smooth', block: 'start' })
              }
            }}
          >{t('home.nav.process')}</a>
          <a
            href="#cases"
            onClick={(e) => {
              e.preventDefault()
              setMobileMenuOpen(false)
              const el = document.getElementById('cases')
              if (el) {
                window.location.hash = 'cases'
                el.scrollIntoView({ behavior: 'smooth', block: 'start' })
              }
            }}
          >{t('home.nav.cases')}</a>
          <a
            href="#pricing"
            onClick={(e) => {
              e.preventDefault()
              setMobileMenuOpen(false)
              const el = document.getElementById('pricing')
              if (el) {
                window.location.hash = 'pricing'
                el.scrollIntoView({ behavior: 'smooth', block: 'start' })
              }
            }}
          >{t('home.nav.pricing')}</a>
        </nav>
        <div className="sidebar-bottom">
          {isLoggedIn ? (
            <>
              <button
                className="sidebar-user-btn"
                onClick={() => { setMobileMenuOpen(false); navigate('/profile') }}
              >
                <span className="user-avatar">👤</span>
                <span className="user-name">{t('home.nav.profile')}</span>
              </button>
              <button
                className="nav-btn nav-btn-logout"
                onClick={() => { setMobileMenuOpen(false); handleLogout() }}
              >
                {t('home.nav.logout')}
              </button>
            </>
          ) : (
            <button
              className="nav-btn nav-btn-register"
              onClick={() => { setMobileMenuOpen(false); setShowLoginModal(true) }}
            >
              {t('home.nav.login_register')}
            </button>
          )}
        </div>
      </aside>

      <div className="home-container">
        {/* Hero Section with Input */}
        <div id="generate" className="home-hero-wrapper">
          <div className="home-hero">
            <span className="hero-accent">{t('home.hero.accent')}</span>
            <h1 className="home-title">
              <span dangerouslySetInnerHTML={{ __html: t('home.hero.title') }} />
            </h1>
            <p className="home-subtitle">{t('home.hero.subtitle')}</p>
          </div>

          <div className="hero-visual">
            <div className="visual-card">
              <div className="visual-stats">
                <div className="visual-stat">
                  <span className="visual-stat-number">200M+</span>
                  <span className="visual-stat-label">{t('home.stats.papers')}</span>
                </div>
                <div className="visual-stat">
                  <span className="visual-stat-number">100%</span>
                  <span className="visual-stat-label">{t('home.stats.citations')}</span>
                </div>
                <div className="visual-stat">
                  <span className="visual-stat-number">5min</span>
                  <span className="visual-stat-label">{t('home.stats.time')}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Input Section - Directly in Hero */}
          <div className="home-input-section">
            {isLoggedIn && (
              <span className={`credits-badge ${prevCredits !== credits ? 'credits-updated' : ''}`}>
                {t('home.input.credits_remaining')} <span className="credits-number">{credits}</span>
              </span>
            )}
            <div className="input-section-header">
              <div className="input-section-title-row">
                <h2 className="input-section-title">{t('home.input.title')}</h2>
              </div>
              <p className="input-section-subtitle">{t('home.input.subtitle')}</p>
            </div>

            <div className="input-wrapper">
              <textarea
                className="topic-input"
                placeholder={t('home.input.placeholder')}
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                disabled={isGenerating}
                rows={3}
              />
              <div className="input-actions">
                <button
                  className="generate-btn"
                  onClick={handleGenerate}
                  disabled={isGenerating || !topic.trim()}
                >
                  {isGenerating ? t('home.input.button_generating') : t('home.input.button')}
                </button>
                <button
                  className="secondary-btn"
                  onClick={() => document.getElementById('process')?.scrollIntoView({ behavior: 'smooth' })}
                >
                  {t('home.input.how_it_works')}
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Data Sources Section */}
        <div className="data-sources-section">
          <div className="section-inner">
            <p className="data-sources-title">{t('home.sources.title')}</p>
            <div className="data-sources-logos">
              <div className="data-source-logo">Web of Science</div>
              <div className="data-source-logo">IEEE Xplore</div>
              <div className="data-source-logo">CrossRef</div>
              <div className="data-source-logo">Semantic Scholar</div>
            </div>
          </div>
        </div>

        {/* Progress Section */}
        {isGenerating && progress && (
          <div className="home-progress">
            <div className="progress-bar">
              <div
                className="progress-fill"
                style={{ width: `${getProgressPercentage()}%` }}
              />
            </div>
            <div className="progress-message">{progress.message}</div>
            <div className="progress-hint">
              {t('home.progress.hint')}
              <span className="progress-hint-link" onClick={() => navigate('/profile')}>
                {t('home.progress.view_profile')}
              </span>
            </div>
          </div>
        )}

        {/* Comparison Section - Simplified */}
        <section id="features" className="landing-section">
          <div className="section-inner">
            <h2 className="section-title">{t('home.comparison.title')}</h2>
            <p className="section-subtitle">{t('home.comparison.subtitle')}</p>
            <div className="comparison-grid comparison-grid-simple">
              <div className="comparison-card">
                <div className="comparison-card-header">
                  <span className="comparison-icon">🤖</span>
                  <h3 className="comparison-card-title">{t('home.comparison.free_ai.title')}</h3>
                </div>
                <ul className="comparison-list">
                  <li className="comparison-item negative">{t('home.comparison.free_ai.con1')}</li>
                  <li className="comparison-item negative">{t('home.comparison.free_ai.con2')}</li>
                  <li className="comparison-item negative">{t('home.comparison.free_ai.con3')}</li>
                  <li className="comparison-item negative">{t('home.comparison.free_ai.con4')}</li>
                </ul>
              </div>
              <div className="comparison-card highlight">
                <div className="comparison-card-header">
                  <span className="comparison-icon">📄</span>
                  <h3 className="comparison-card-title">{t('home.comparison.autooverview.title')}</h3>
                </div>
                <ul className="comparison-list">
                  <li className="comparison-item positive">{t('home.comparison.autooverview.pro1')}</li>
                  <li className="comparison-item positive">{t('home.comparison.autooverview.pro2')}</li>
                  <li className="comparison-item positive">{t('home.comparison.autooverview.pro3')}</li>
                  <li className="comparison-item positive">{t('home.comparison.autooverview.pro4')}</li>
                </ul>
              </div>
            </div>
          </div>
        </section>

        {/* Core Features */}
        <section className="landing-section section-alt">
          <div className="section-inner">
            <h2 className="section-title">{t('home.features.title')}</h2>
            <div className="home-features">
              <div className="feature-item">
                <span className="feature-icon">🔍</span>
                <div>
                  <h3 className="feature-title">{t('home.features.papers')}</h3>
                  <p className="feature-desc">{t('home.features.papers_desc')}</p>
                </div>
              </div>
              <div className="feature-item">
                <span className="feature-icon">⚡</span>
                <div>
                  <h3 className="feature-title">{t('home.features.time')}</h3>
                  <p className="feature-desc">{t('home.features.time_desc')}</p>
                </div>
              </div>
              <div className="feature-item">
                <span className="feature-icon">📝</span>
                <div>
                  <h3 className="feature-title">{t('home.features.format')}</h3>
                  <p className="feature-desc">{t('home.features.format_desc')}</p>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* How It Works */}
        <section id="process" className="landing-section">
          <div className="section-inner">
            <h2 className="section-title">{t('home.process.title')}</h2>
            <p className="section-subtitle">{t('home.process.subtitle')}</p>
            <div className="process-steps process-steps-simple">
              <div className="process-step">
                <div className="step-number">1</div>
                <div className="step-icon">✏️</div>
                <h3 className="step-title">{t('home.process.step1_title')}</h3>
                <p className="step-desc">{t('home.process.step1_desc')}</p>
              </div>
              <div className="process-arrow">→</div>
              <div className="process-step">
                <div className="step-number">2</div>
                <div className="step-icon">✨</div>
                <h3 className="step-title">{t('home.process.step2_title')}</h3>
                <p className="step-desc">{t('home.process.step2_desc')}</p>
              </div>
              <div className="process-arrow">→</div>
              <div className="process-step">
                <div className="step-number">3</div>
                <div className="step-icon">📄</div>
                <h3 className="step-title">{t('home.process.step3_title')}</h3>
                <p className="step-desc">{t('home.process.step3_desc')}</p>
              </div>
            </div>
            <div className="process-cta">
              <button
                className="generate-btn"
                onClick={() => {
                  const el = document.getElementById('generate')
                  if (el) {
                    const navHeight = 60
                    const elPosition = el.getBoundingClientRect().top + window.pageYOffset
                    window.scrollTo({ top: elPosition - navHeight, behavior: 'smooth' })
                  }
                }}
              >
                {t('home.input.button')}
              </button>
            </div>
          </div>
        </section>

        {/* Sample Reviews */}
        <section id="cases" className="landing-section section-alt">
          <div className="section-inner">
            <h2 className="section-title">{t('home.demo.title')}</h2>
            <p className="section-subtitle">{t('home.demo.subtitle')}</p>
            <div className="cases-grid">
              {casesLoading ? (
                <div className="cases-loading">{t('home.demo.loading')}</div>
              ) : demoCases.length === 0 ? (
                <div className="cases-empty">{t('home.demo.empty')}</div>
              ) : (
                demoCases.map((case_item) => (
                  <div
                    key={case_item.task_id}
                    className="case-card"
                    onClick={() => navigate(`/review?task_id=${case_item.task_id}`)}
                    role="button"
                    tabIndex={0}
                  >
                    <div className="case-icon">{case_item.icon}</div>
                    <h3 className="case-title">{case_item.title}</h3>
                    <p className="case-desc">{case_item.description || t('home.demo.ai_generated')}</p>
                    <div className="case-action">{t('home.demo.view_details')}</div>
                  </div>
                ))
              )}
            </div>
            <div className="cases-cta">
              <button
                className="secondary-btn"
                onClick={() => {
                  const el = document.getElementById('pricing')
                  if (el) {
                    const navHeight = 60
                    const elPosition = el.getBoundingClientRect().top + window.pageYOffset
                    window.scrollTo({ top: elPosition - navHeight, behavior: 'smooth' })
                  }
                }}
              >
                {t('home.pricing.title')}
              </button>
            </div>
          </div>
        </section>

        {/* Testimonials */}
        <section className="landing-section">
          <div className="section-inner">
            <h2 className="section-title">{t('home.testimonials.title')}</h2>
            <div className="testimonials testimonials-international">
              <div className="testimonial-card">
                <p className="testimonial-text">{t('home.testimonials.text1')}</p>
                <div className="testimonial-author">
                  <span className="testimonial-avatar">🎓</span>
                  <div>
                    <span className="testimonial-name">{t('home.testimonials.name1')}</span>
                    <span className="testimonial-role">{t('home.testimonials.role1')}</span>
                  </div>
                </div>
              </div>
              <div className="testimonial-card">
                <p className="testimonial-text">{t('home.testimonials.text2')}</p>
                <div className="testimonial-author">
                  <span className="testimonial-avatar">🔬</span>
                  <div>
                    <span className="testimonial-name">{t('home.testimonials.name2')}</span>
                    <span className="testimonial-role">{t('home.testimonials.role2')}</span>
                  </div>
                </div>
              </div>
              <div className="testimonial-card">
                <p className="testimonial-text">{t('home.testimonials.text3')}</p>
                <div className="testimonial-author">
                  <span className="testimonial-avatar">📚</span>
                  <div>
                    <span className="testimonial-name">{t('home.testimonials.name3')}</span>
                    <span className="testimonial-role">{t('home.testimonials.role3')}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Pricing */}
        <section id="pricing" className="landing-section section-alt">
          <div className="section-inner">
            <h2 className="section-title">{t('home.pricing.title')}</h2>
            <p className="section-subtitle">{t('home.pricing.subtitle')}</p>
            <p className="pricing-note">{t('home.pricing.note')}</p>

            {plansLoading ? (
              <div className="pricing-grid">
                <div className="pricing-card">
                  <div className="pricing-price">{t('common.loading')}</div>
                </div>
              </div>
            ) : (
              <div className="pricing-grid pricing-grid-international">
                {/* Plan 1: Single Review */}
                <div className="pricing-card pricing-card-english">
                  <h3 className="pricing-name">{t('home.pricing.single.name')}</h3>
                  <div className="pricing-price">
                    <span className="currency">$</span>
                    <span className="amount">{t('home.pricing.single.price')}</span>
                  </div>
                  <ul className="pricing-features">
                    {(t('home.pricing.single.features', { returnObjects: true }) as string[]).map((feature: string, index: number) => (
                      <li key={index}>✓ {feature}</li>
                    ))}
                  </ul>
                  <button
                    className="pricing-btn pricing-btn-primary"
                    onClick={() => {
                      isLoggedIn ? setShowPaymentModal('single') : setShowLoginModal(true)
                    }}
                  >
                    {t('home.pricing.buy_now')}
                  </button>
                </div>

                {/* Plan 2: 3 Reviews */}
                <div className="pricing-card pricing-card-english pricing-featured">
                  <div className="pricing-badge">Best Value</div>
                  <h3 className="pricing-name">{t('home.pricing.pack3.name')}</h3>
                  <div className="pricing-price">
                    <span className="currency">$</span>
                    <span className="amount">{t('home.pricing.pack3.price')}</span>
                  </div>
                  <ul className="pricing-features">
                    {(t('home.pricing.pack3.features', { returnObjects: true }) as string[]).map((feature: string, index: number) => (
                      <li key={index}>✓ {feature}</li>
                    ))}
                  </ul>
                  <button
                    className="pricing-btn pricing-btn-primary"
                    onClick={() => {
                      isLoggedIn ? setShowPaymentModal('pack3') : setShowLoginModal(true)
                    }}
                  >
                    {t('home.pricing.buy_now')}
                  </button>
                </div>

                {/* Plan 3: 6 Reviews */}
                <div className="pricing-card pricing-card-english">
                  <div className="pricing-badge">Popular</div>
                  <h3 className="pricing-name">{t('home.pricing.pack6.name')}</h3>
                  <div className="pricing-price">
                    <span className="currency">$</span>
                    <span className="amount">{t('home.pricing.pack6.price')}</span>
                  </div>
                  <ul className="pricing-features">
                    {(t('home.pricing.pack6.features', { returnObjects: true }) as string[]).map((feature: string, index: number) => (
                      <li key={index}>✓ {feature}</li>
                    ))}
                  </ul>
                  <button
                    className="pricing-btn pricing-btn-primary"
                    onClick={() => {
                      isLoggedIn ? setShowPaymentModal('pack6') : setShowLoginModal(true)
                    }}
                  >
                    {t('home.pricing.buy_now')}
                  </button>
                </div>
              </div>
            )}
          </div>
        </section>

        {/* Academic Integrity */}
        <section className="landing-section academic-integrity-section">
          <div className="section-inner">
            <div className="integrity-notice">
              <span className="integrity-icon">🎓</span>
              <div className="integrity-content">
                <h3 className="integrity-title">{t('home.integrity.title')}</h3>
                <p className="integrity-description">{t('home.integrity.description')}</p>
                <a href="/integrity" className="integrity-link">{t('home.integrity.link')}</a>
              </div>
            </div>
          </div>
        </section>

        {/* Footer */}
        <footer className="home-footer home-footer-international">
          <div className="footer-content">
            <p className="footer-copyright">{t('home.footer.copyright')}</p>
            <div className="footer-links">
              <a href="/terms-and-conditions" className="footer-link">{t('home.footer.terms')}</a>
              <span className="footer-separator">•</span>
              <a href="/privacy-policy" className="footer-link">{t('home.footer.privacy')}</a>
              <span className="footer-separator">•</span>
              <a href="/refund-policy" className="footer-link">{t('home.footer.refund')}</a>
            </div>
            <p className="footer-databases">{t('home.footer.databases')}</p>
          </div>
        </footer>
      </div>

      {/* Modals */}
      {showLoginModal && (
        <LoginModalInternational
          onClose={() => setShowLoginModal(false)}
          onLoginSuccess={handleLoginSuccess}
          pendingTopic={topic}
        />
      )}

      {showPaymentModal && (
        <>
          {language === 'en' ? (
            <PaddlePaymentModal
              onClose={() => setShowPaymentModal(false)}
              onPaymentSuccess={handlePaymentSuccess}
              planType={showPaymentModal}
            />
          ) : (
            <PaymentModal
              onClose={() => setShowPaymentModal(false)}
              onPaymentSuccess={handlePaymentSuccess}
              planType={showPaymentModal}
            />
          )}
        </>
      )}

      {showToast && (
        <div className="toast toast-success">
          <span className="toast-icon">✓</span>
          <span className="toast-message">{toastMessage}</span>
        </div>
      )}

      <CookieConsentBanner />
    </div>
  )

  function getProgressPercentage(): number {
    if (!progress) return 0
    const stepValues: Record<string, number> = {
      'processing': 30,
      'searching': 50,
      'analyzing': 70,
      'generating': 90,
      'completed': 100
    }
    return stepValues[progress.step] || 50
  }
}
