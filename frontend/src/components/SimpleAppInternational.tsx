/**
 * SimpleApp Component - International Academic Version
 * Designed for overseas market with clean, professional academic style
 */
import { useState, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { api } from '../api'
import { isLoggedIn as checkLoggedIn } from '../authApi'
import { LoginModalInternational } from './LoginModalInternational'
import { PayPalPaymentModal } from './PayPalPaymentModal'
import { CookieConsentBanner } from './CookieConsentBanner'
import './SimpleAppInternational.css'

export function SimpleAppInternational({ autoShowLogin }: { autoShowLogin?: boolean } = {}) {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const location = useLocation()
  const [showLoginModal, setShowLoginModal] = useState(false)
  const [showPaymentModal, setShowPaymentModal] = useState<string | false>(false)
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [credits, setCredits] = useState<number>(0)
  const [prevCredits, setPrevCredits] = useState<number>(0)
  const [showToast, setShowToast] = useState(false)
  const [toastMessage, setToastMessage] = useState('')
  const [plans, setPlans] = useState<any[]>([])
  const [plansLoading, setPlansLoading] = useState(true)
  const [demoCases, setDemoCases] = useState<any[]>([])
  const [casesLoading, setCasesLoading] = useState(true)
  const [activeSection, setActiveSection] = useState<string>('')

  // Handle OAuth callback (token and user in URL params)
  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const oauthCallback = params.get('oauth_callback')
    const oauthError = params.get('oauth_error')

    if (oauthCallback === '1' && !oauthError) {
      const token = params.get('token')
      const user = params.get('user')
      if (token && user) {
        try {
          localStorage.setItem('auth_token', token)
          localStorage.setItem('user_info', user)
          window.history.replaceState({}, '', '/login')
          setIsLoggedIn(true)
          setTimeout(() => navigate('/'), 300)
          return
        } catch (e) {
          console.error('OAuth callback parse error:', e)
        }
      }
    }

    if (oauthError) {
      window.history.replaceState({}, '', '/login')
      setShowLoginModal(true)
    }
  }, [])

  useEffect(() => {
    const loggedIn = checkLoggedIn()
    setIsLoggedIn(loggedIn)
    if (!loggedIn && autoShowLogin) {
      setShowLoginModal(true)
    }
    if (loggedIn) {
      api.getCredits().then(data => {
        setCredits(data.credits)
        setPrevCredits(data.credits)
      }).catch(() => {})
    }

    api.getSubscriptionPlans().then(data => {
      setPlans(data.plans)
      setPlansLoading(false)
    }).catch(() => {
      setPlansLoading(false)
    })

    fetch('/api/cases?lang=en')
      .then(res => res.json())
      .then(data => {
        if (data.success && data.data.cases) {
          setDemoCases(data.data.cases)
        }
        setCasesLoading(false)
      })
      .catch(() => {
        setCasesLoading(false)
      })
  }, [])

  const handleLoginSuccess = () => {
    const loggedIn = checkLoggedIn()
    setIsLoggedIn(loggedIn)
    setShowLoginModal(false)
    if (loggedIn) {
      api.getCredits().then(data => {
        setCredits(data.credits)
        setPrevCredits(data.credits)
      }).catch(() => {})
    }
  }

  const handlePaymentSuccess = async () => {
    setShowPaymentModal(false)
    api.getCredits().then(data => {
      setPrevCredits(credits)
      setCredits(data.credits)
      if (data.credits > prevCredits) {
        setShowToast(true)
        setToastMessage(t('common.payment_success'))
        setTimeout(() => setShowToast(false), 3000)
      }
    }).catch(() => {})
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

  // Handle hash scroll when navigating from other pages
  const scrollToHash = () => {
    const hash = window.location.hash || location.hash
    if (!hash) return
    const id = hash.replace('#', '')
    const el = document.getElementById(id)
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  }

  useEffect(() => {
    const hash = window.location.hash || location.hash
    if (hash) {
      const timer = setTimeout(scrollToHash, 300)
      return () => clearTimeout(timer)
    }
  }, [location.hash])

  // Re-scroll after cases finish loading (content shift affects position)
  useEffect(() => {
    if (!casesLoading) {
      const hash = window.location.hash || location.hash
      if (hash) {
        setTimeout(scrollToHash, 100)
      }
    }
  }, [casesLoading])

  // Track active section for left sidebar highlight
  useEffect(() => {
    const sectionIds = ['features', 'process', 'cases', 'pricing']
    const onScroll = () => {
      const navHeight = 80
      let current = ''
      for (const id of sectionIds) {
        const el = document.getElementById(id)
        if (el) {
          const rect = el.getBoundingClientRect()
          if (rect.top <= navHeight + 100) {
            current = id
          }
        }
      }
      setActiveSection(current)
    }
    window.addEventListener('scroll', onScroll, { passive: true })
    onScroll()
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  return (
    <div className="simple-home simple-home-international">
      <nav className="home-nav">
        <div className="nav-logo" onClick={() => navigate('/')} style={{ cursor: 'pointer' }}>
          <span className="logo-icon">📚</span>
          <span className="logo-text">Danmo Scholar</span>
        </div>
        <div className="nav-links">
          <a href="/" className={location.pathname === '/' ? 'active' : ''} onClick={(e) => {
            e.preventDefault()
            navigate('/')
          }}>{t('nav.home')}</a>
          <a href="/search-papers" className={location.pathname === '/search-papers' ? 'active' : ''} onClick={(e) => {
            e.preventDefault()
            navigate('/search-papers')
          }}>{t('home.nav.search_papers')}</a>
          <a href="/comparison-matrix" className={location.pathname === '/comparison-matrix' ? 'active' : ''} onClick={(e) => {
            e.preventDefault()
            navigate('/comparison-matrix')
          }}>{t('home.nav.comparison_matrix')}</a>
          <a href="/generate" className={location.pathname === '/generate' ? 'active' : ''} onClick={(e) => {
            e.preventDefault()
            navigate('/generate')
          }}>{t('home.nav.generate')}</a>
          <a href="/#pricing" onClick={(e) => {
            e.preventDefault()
            if (location.pathname === '/') {
              const el = document.getElementById('pricing')
              if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
            } else {
              window.location.href = '/#pricing'
            }
          }}>{t('home.nav.pricing')}</a>
        </div>
        <div className="nav-actions">
          {isLoggedIn ? (
            <div className="user-menu">
              <button className="user-info" onClick={() => navigate('/records')}>
                <span className="user-avatar">👤</span>
                <span className="user-name">{t('home.nav.profile')}</span>
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
          <span className="logo-text">Danmo Scholar</span>
          <button className="sidebar-close" onClick={() => setMobileMenuOpen(false)} aria-label="Close menu">&times;</button>
        </div>
        <nav className="sidebar-links">
          <a
            href="/"
            className={location.pathname === '/' ? 'active' : ''}
            onClick={(e) => {
              e.preventDefault()
              setMobileMenuOpen(false)
              navigate('/')
            }}
          >{t('nav.home')}</a>
          <a
            href="/search-papers"
            className={location.pathname === '/search-papers' ? 'active' : ''}
            onClick={(e) => {
              e.preventDefault()
              setMobileMenuOpen(false)
              navigate('/search-papers')
            }}
          >{t('home.nav.search_papers')}</a>
          <a
            href="/comparison-matrix"
            className={location.pathname === '/comparison-matrix' ? 'active' : ''}
            onClick={(e) => {
              e.preventDefault()
              setMobileMenuOpen(false)
              navigate('/comparison-matrix')
            }}
          >{t('home.nav.comparison_matrix')}</a>
          <a
            href="/generate"
            className={location.pathname === '/generate' ? 'active' : ''}
            onClick={(e) => {
              e.preventDefault()
              setMobileMenuOpen(false)
              navigate('/generate')
            }}
          >{t('home.nav.generate')}</a>
          <a
            href="/#pricing"
            onClick={(e) => {
              e.preventDefault()
              setMobileMenuOpen(false)
              window.location.href = '/#pricing'
            }}
          >{t('home.nav.pricing')}</a>
        </nav>
        <div className="sidebar-bottom">
          {isLoggedIn ? (
            <>
              <button
                className="sidebar-user-btn"
                onClick={() => { setMobileMenuOpen(false); navigate('/records') }}
              >
                <span className="user-avatar">👤</span>
                <span className="user-name">{t('home.nav.profile')}</span>
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

      {/* Left Sidebar - Desktop */}
      <aside className="left-sidebar left-sidebar-visible">
        <nav className="left-sidebar-nav">
          <a href="#features" className={activeSection === 'features' ? 'active' : ''} onClick={(e) => {
            e.preventDefault()
            const el = document.getElementById('features')
            if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
          }}>{t('home.nav.features')}</a>
          <a href="#process" className={activeSection === 'process' ? 'active' : ''} onClick={(e) => {
            e.preventDefault()
            const el = document.getElementById('process')
            if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
          }}>{t('home.nav.process')}</a>
          <a href="#cases" className={activeSection === 'cases' ? 'active' : ''} onClick={(e) => {
            e.preventDefault()
            const el = document.getElementById('cases')
            if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
          }}>{t('home.nav.cases')}</a>
          <a href="#pricing" className={activeSection === 'pricing' ? 'active' : ''} onClick={(e) => {
            e.preventDefault()
            const el = document.getElementById('pricing')
            if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
          }}>{t('home.nav.pricing')}</a>
        </nav>
      </aside>

      <div className="home-container">
        {/* Hero Section */}
        <div id="generate" className="home-hero-wrapper">
          <div className="home-hero">
            <span className="hero-accent">{t('home.hero.accent')}</span>
            <h1 className="home-title">
              <span dangerouslySetInnerHTML={{ __html: t('home.hero.title') }} />
            </h1>
            <p className="home-subtitle">{t('home.hero.subtitle')}</p>

            {/* Three entry cards */}
            <div className="hero-entry-cards">
              <div className="hero-entry-card hero-entry-card-primary" onClick={() => navigate('/search-papers')}>
                <span className="hero-entry-icon">🔍</span>
                <h3>{t('home.hero.cards.search')}</h3>
                <p>{t('home.hero.cards.search_desc')}</p>
              </div>
              <div className="hero-entry-card" onClick={() => navigate('/comparison-matrix')}>
                <span className="hero-entry-icon">📊</span>
                <h3>{t('home.hero.cards.matrix')}</h3>
                <p>{t('home.hero.cards.matrix_desc')}</p>
              </div>
              <div className="hero-entry-card" onClick={() => navigate('/generate')}>
                <span className="hero-entry-icon">📝</span>
                <h3>{t('home.hero.cards.generate')}</h3>
                <p>{t('home.hero.cards.generate_desc')}</p>
              </div>
            </div>
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
        </div>


        {/* Core Features */}
        <section id="features" className="landing-section">
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

        {/* Comparison Section */}
        <section className="landing-section section-alt">
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
                  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
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
                    onKeyDown={(e) => { if (e.key === 'Enter') navigate(`/review?task_id=${case_item.task_id}`) }}
                    role="button"
                    tabIndex={0}
                    aria-label={`${case_item.title} - ${t('home.demo.view_details')}`}
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
                  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
                }}
              >
                {t('home.pricing.title')}
              </button>
            </div>
          </div>
        </section>

        {/* Pricing */}
        <section id="pricing" className="landing-section section-alt">
          <div className="section-inner">
            <h2 className="section-title">{t('home.pricing.title')}</h2>
            <p className="section-subtitle">{t('home.pricing.subtitle')}</p>

            {plansLoading ? (
              <div className="pricing-grid">
                <div className="pricing-card">
                  <div className="pricing-price">{t('common.loading')}</div>
                </div>
              </div>
            ) : (
              <div className="pricing-grid pricing-grid-international">
                {plans.filter((p: any) => p.type !== 'unlock').map((plan: any) => {
                  const isFeatured = plan.recommended || !!plan.badge_en
                  return (
                    <div
                      key={plan.type}
                      className={`pricing-card pricing-card-english ${isFeatured ? 'pricing-featured' : ''}`}
                    >
                      {isFeatured && plan.badge_en && (
                        <div className="pricing-badge">{plan.badge_en}</div>
                      )}
                      <h3 className="pricing-name">{plan.name_en || plan.name}</h3>
                      <div className="pricing-price">
                        {plan.original_price_usd > 0 && (
                          <span className="pricing-original">${plan.original_price_usd}</span>
                        )}
                        <span className="currency">$</span>
                        <span className="amount">{plan.price_usd || plan.price}</span>
                      </div>
                      <ul className="pricing-features">
                        {(plan.features_en || plan.features || []).map((feature: string, index: number) => (
                          <li key={index}>✓ {feature}</li>
                        ))}
                      </ul>
                      <button
                        className="pricing-btn pricing-btn-primary"
                        onClick={() => {
                          isLoggedIn ? setShowPaymentModal(plan.type) : setShowLoginModal(true)
                        }}
                      >
                        {t('home.pricing.buy_now')}
                      </button>
                    </div>
                  )
                })}
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
                <a href="/academic-integrity" className="integrity-link">{t('home.integrity.link')}</a>
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
              <span className="footer-separator">•</span>
              <a href="/academic-integrity" className="footer-link">Academic Integrity</a>
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
        />
      )}

      {showPaymentModal && (
        <PayPalPaymentModal
          onClose={() => setShowPaymentModal(false)}
          onPaymentSuccess={handlePaymentSuccess}
          planType={showPaymentModal}
        />
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
}
