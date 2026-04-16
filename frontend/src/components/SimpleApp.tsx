import { useState, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { api } from '../api'
import { isLoggedIn as checkLoggedIn } from '../authApi'
import { LoginModal } from './LoginModal'
import { PaymentModal } from './PaymentModal'
import './SimpleApp.css'

export function SimpleApp({ autoShowLogin }: { autoShowLogin?: boolean } = {}) {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const location = useLocation()
  const [showLoginModal, setShowLoginModal] = useState(false)
  const [showPaymentModal, setShowPaymentModal] = useState<string | false>(false)
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [showToast, setShowToast] = useState(false)
  const [toastMessage, setToastMessage] = useState('')
  const [plans, setPlans] = useState<any[]>([])
  const [plansLoading, setPlansLoading] = useState(true)
  const [demoCases, setDemoCases] = useState<any[]>([])
  const [casesLoading, setCasesLoading] = useState(true)

  useEffect(() => {
    const loggedIn = checkLoggedIn()
    setIsLoggedIn(loggedIn)
    if (!loggedIn && autoShowLogin) {
      setShowLoginModal(true)
    }

    api.getSubscriptionPlans().then(data => {
      setPlans(data.plans)
      setPlansLoading(false)
    }).catch(() => {
      setPlansLoading(false)
    })

    fetch('/api/cases')
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

  // 从其他页面跳转过来时，处理 hash 滚动
  useEffect(() => {
    if (location.hash) {
      const id = location.hash.replace('#', '')
      const timer = setTimeout(() => {
        const el = document.getElementById(id)
        if (el) {
          const navHeight = 60
          const elPosition = el.getBoundingClientRect().top + window.pageYOffset
          window.scrollTo({ top: elPosition - navHeight, behavior: 'smooth' })
        }
      }, 300)
      return () => clearTimeout(timer)
    }
  }, [location.hash])

  const handleLoginSuccess = () => {
    const loggedIn = checkLoggedIn()
    setIsLoggedIn(loggedIn)
    setShowLoginModal(false)
  }

  const handlePaymentSuccess = async () => {
    setShowPaymentModal(false)
    setToastMessage(t('common.payment_success'))
    setShowToast(true)
    setTimeout(() => setShowToast(false), 3000)
  }

  return (
    <div className="simple-home">
      <nav className="home-nav">
        <div className="nav-logo">
          <span className="logo-icon">📚</span>
          <span className="logo-text">AutoOverview</span>
        </div>
        <div className="nav-links">
          <a href="/search-papers" onClick={(e) => { e.preventDefault(); navigate('/search-papers') }}>{t('home.nav.search_papers')}</a>
          <a href="/comparison-matrix" onClick={(e) => { e.preventDefault(); navigate('/comparison-matrix') }}>{t('home.nav.comparison_matrix')}</a>
          <a href="/generate" onClick={(e) => { e.preventDefault(); navigate('/generate') }}>{t('home.nav.generate')}</a>
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

      {/* 移动端侧边栏遮罩 */}
      {mobileMenuOpen && (
        <div className="mobile-sidebar-overlay" onClick={() => setMobileMenuOpen(false)} />
      )}

      {/* 移动端侧边栏 */}
      <aside className={`mobile-sidebar ${mobileMenuOpen ? 'sidebar-open' : ''}`}>
        <div className="sidebar-header">
          <span className="logo-icon">📚</span>
          <span className="logo-text">AutoOverview</span>
          <button className="sidebar-close" onClick={() => setMobileMenuOpen(false)}>&times;</button>
        </div>
        <nav className="sidebar-links">
          <a href="#features" onClick={() => setMobileMenuOpen(false)}>{t('home.nav.features')}</a>
          <a href="#process" onClick={() => setMobileMenuOpen(false)}>{t('home.nav.process')}</a>
          <a href="#cases" onClick={() => setMobileMenuOpen(false)}>{t('home.nav.cases')}</a>
          <a href="#pricing" onClick={() => setMobileMenuOpen(false)}>{t('home.nav.pricing')}</a>
          <a href="/search-papers" onClick={(e) => { e.preventDefault(); setMobileMenuOpen(false); navigate('/search-papers') }}>{t('home.nav.search_papers')}</a>
          <a href="/comparison-matrix" onClick={(e) => { e.preventDefault(); setMobileMenuOpen(false); navigate('/comparison-matrix') }}>{t('home.nav.comparison_matrix')}</a>
          <a href="/generate" onClick={(e) => { e.preventDefault(); setMobileMenuOpen(false); navigate('/generate') }}>{t('home.nav.generate')}</a>
        </nav>
        <div className="sidebar-bottom">
          {isLoggedIn ? (
            <>
              <button className="sidebar-user-btn" onClick={() => { setMobileMenuOpen(false); navigate('/profile') }}>
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

      {/* 左侧侧边栏 - 桌面端 */}
      <aside className="left-sidebar left-sidebar-visible">
        <nav className="left-sidebar-nav">
          <a href="#features" onClick={(e) => {
            e.preventDefault()
            const el = document.getElementById('features')
            if (el) {
              const navHeight = 60
              const elPosition = el.getBoundingClientRect().top + window.pageYOffset
              window.scrollTo({ top: elPosition - navHeight, behavior: 'smooth' })
            }
          }}>{t('home.nav.features')}</a>
          <a href="#process" onClick={(e) => {
            e.preventDefault()
            const el = document.getElementById('process')
            if (el) {
              const navHeight = 60
              const elPosition = el.getBoundingClientRect().top + window.pageYOffset
              window.scrollTo({ top: elPosition - navHeight, behavior: 'smooth' })
            }
          }}>{t('home.nav.process')}</a>
          <a href="#cases" onClick={(e) => {
            e.preventDefault()
            const el = document.getElementById('cases')
            if (el) {
              const navHeight = 60
              const elPosition = el.getBoundingClientRect().top + window.pageYOffset
              window.scrollTo({ top: elPosition - navHeight, behavior: 'smooth' })
            }
          }}>{t('home.nav.cases')}</a>
          <a href="#pricing" onClick={(e) => {
            e.preventDefault()
            const el = document.getElementById('pricing')
            if (el) {
              const navHeight = 60
              const elPosition = el.getBoundingClientRect().top + window.pageYOffset
              window.scrollTo({ top: elPosition - navHeight, behavior: 'smooth' })
            }
          }}>{t('home.nav.pricing')}</a>
        </nav>
      </aside>

      <div className="home-container">
        <div id="generate" className="home-hero-wrapper">
          <div className="home-hero">
            <span className="hero-accent">{t('home.hero.accent')}</span>
            <h1 className="home-title">
              <span dangerouslySetInnerHTML={{ __html: t('home.hero.title') }} />
            </h1>
            <p className="home-subtitle">
              {t('home.hero.subtitle')}
            </p>

            {/* Three entry cards */}
            <div className="hero-entry-cards">
              <div className="hero-entry-card" onClick={() => navigate('/search-papers')}>
                <span className="hero-entry-icon">🔍</span>
                <h3>{t('home.hero.cards.search')}</h3>
                <p>{t('home.hero.cards.search_desc')}</p>
              </div>
              <div className="hero-entry-card" onClick={() => navigate('/comparison-matrix')}>
                <span className="hero-entry-icon">📊</span>
                <h3>{t('home.hero.cards.matrix')}</h3>
                <p>{t('home.hero.cards.matrix_desc')}</p>
              </div>
              <div className="hero-entry-card hero-entry-card-primary" onClick={() => navigate('/generate')}>
                <span className="hero-entry-icon">📝</span>
                <h3>{t('home.hero.cards.generate')}</h3>
                <p>{t('home.hero.cards.generate_desc')}</p>
              </div>
            </div>
          </div>

          <div className="hero-visual">
            <div className="visual-card">
              <div className="visual-icon-large">📊</div>
              <div className="visual-stats">
                <div className="visual-stat">
                  <span className="visual-stat-number">2亿+</span>
                  <span className="visual-stat-label">{t('home.stats.papers')}</span>
                </div>
                <div className="visual-stat">
                  <span className="visual-stat-number">5min</span>
                  <span className="visual-stat-label">{t('home.stats.time')}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <section id="features" className="landing-section">
        <div className="section-inner">
          <h2 className="section-title">{t('home.features.title')}</h2>
          <div className="comparison-grid">
            <div className="comparison-card">
              <div className="comparison-card-header">
                <span className="comparison-icon">🤖</span>
                <h3 className="comparison-card-title">{t('home.comparison.free_llm.title')}</h3>
              </div>
              <ul className="comparison-list">
                <li className="comparison-item negative">{t('home.comparison.free_llm.con1')}</li>
                <li className="comparison-item negative">{t('home.comparison.free_llm.con2')}</li>
                <li className="comparison-item negative">{t('home.comparison.free_llm.con3')}</li>
              </ul>
            </div>
            <div className="comparison-card">
              <div className="comparison-card-header">
                <span className="comparison-icon">🔧</span>
                <h3 className="comparison-card-title">{t('home.comparison.tools.title')}</h3>
              </div>
              <ul className="comparison-list">
                <li className="comparison-item negative">{t('home.comparison.tools.con1')}</li>
                <li className="comparison-item negative">{t('home.comparison.tools.con2')}</li>
                <li className="comparison-item negative">{t('home.comparison.tools.con3')}</li>
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
              </ul>
            </div>
            <div className="comparison-card">
              <div className="comparison-card-header">
                <span className="comparison-icon">👤</span>
                <h3 className="comparison-card-title">{t('home.comparison.services.title')}</h3>
              </div>
              <ul className="comparison-list">
                <li className="comparison-item negative">{t('home.comparison.services.con1')}</li>
                <li className="comparison-item negative">{t('home.comparison.services.con2')}</li>
                <li className="comparison-item negative">{t('home.comparison.services.con3')}</li>
              </ul>
            </div>
            <div className="comparison-card">
              <div className="comparison-card-header">
                <span className="comparison-icon">📖</span>
                <h3 className="comparison-card-title">{t('home.comparison.manual.title')}</h3>
              </div>
              <ul className="comparison-list">
                <li className="comparison-item negative">{t('home.comparison.manual.con1')}</li>
                <li className="comparison-item negative">{t('home.comparison.manual.con2')}</li>
                <li className="comparison-item negative">{t('home.comparison.manual.con3')}</li>
              </ul>
            </div>
          </div>
          <div className="home-features">
            <div className="feature-item">
              <span className="feature-icon">📚</span>
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
              <span className="feature-icon">🎯</span>
              <div>
                <h3 className="feature-title">{t('home.features.format')}</h3>
                <p className="feature-desc">{t('home.features.format_desc')}</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="landing-section comparison-section">
        <div className="section-inner">
          <h2 className="section-title">{t('home.comparison.title')}</h2>
          <div className="comparison-flow">
            <div className="comparison-flow-card comparison-flow-manual">
              <div className="comparison-flow-label">{t('home.comparison.traditional_label')}</div>
              <ul className="comparison-flow-steps">
                <li><span className="comparison-flow-step-num">{t('home.comparison.traditional_step1')}</span> {t('home.comparison.traditional_step1_desc')}</li>
                <li><span className="comparison-flow-step-num">{t('home.comparison.traditional_step2')}</span> {t('home.comparison.traditional_step2_desc')}</li>
                <li><span className="comparison-flow-step-num">{t('home.comparison.traditional_step3')}</span> {t('home.comparison.traditional_step3_desc')}</li>
                <li><span className="comparison-flow-step-num">{t('home.comparison.traditional_step4')}</span> {t('home.comparison.traditional_step4_desc')}</li>
              </ul>
              <div className="comparison-flow-result">
                <span className="comparison-flow-time">{t('home.comparison.traditional_result_time')}</span>
                <span className="comparison-flow-mood">{t('home.comparison.traditional_result_mood')}</span>
              </div>
            </div>
            <div className="comparison-flow-vs">VS</div>
            <div className="comparison-flow-card comparison-flow-auto">
              <div className="comparison-flow-label">{t('home.comparison.auto_label')}</div>
              <ul className="comparison-flow-steps">
                <li><span className="comparison-flow-step-num">{t('home.comparison.auto_step1')}</span> {t('home.comparison.auto_step1_desc')}</li>
                <li><span className="comparison-flow-step-num">{t('home.comparison.auto_step2')}</span> {t('home.comparison.auto_step2_desc')}</li>
                <li><span className="comparison-flow-step-num">{t('home.comparison.auto_step3')}</span> {t('home.comparison.auto_step3_desc')}</li>
              </ul>
              <div className="comparison-flow-result">
                <span className="comparison-flow-time">{t('home.comparison.auto_result_time')}</span>
                <span className="comparison-flow-mood">{t('home.comparison.auto_result_mood')}</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section id="process" className="landing-section section-alt">
        <div className="section-inner">
          <h2 className="section-title">{t('home.process.title')}</h2>
          <p className="section-subtitle">{t('home.process.subtitle')}</p>
          <div className="process-steps">
            <div className="process-step">
              <div className="step-number">01</div>
              <div className="step-icon">✏️</div>
              <h3 className="step-title">{t('home.process.step1_title')}</h3>
              <p className="step-desc">{t('home.process.step1_desc')}</p>
            </div>
            <div className="process-arrow">→</div>
            <div className="process-step">
              <div className="step-number">02</div>
              <div className="step-icon">✨</div>
              <h3 className="step-title">{t('home.process.step2_title')}</h3>
              <p className="step-desc">{t('home.process.step2_desc')}</p>
            </div>
            <div className="process-arrow">→</div>
            <div className="process-step">
              <div className="step-number">03</div>
              <div className="step-icon">📄</div>
              <h3 className="step-title">{t('home.process.step3_title')}</h3>
              <p className="step-desc">{t('home.process.step3_desc')}</p>
            </div>
          </div>
        </div>
      </section>

      <section id="cases" className="landing-section">
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
                  {case_item.tags && case_item.tags.length > 0 && (
                    <div className="case-tags">
                      {case_item.tags.map((tag: string, idx: number) => (
                        <span key={idx} className="case-tag">{tag}</span>
                      ))}
                    </div>
                  )}
                  <div className="case-action">{t('home.demo.view_details')}</div>
                </div>
              ))
            )}
          </div>
        </div>
      </section>

      <section id="pricing" className="landing-section section-alt">
        <div className="section-inner">
          <h2 className="section-title">{t('pricing.title')}</h2>
          <p className="section-subtitle">{t('pricing.note')}</p>
          {plansLoading ? (
            <div className="pricing-grid">
              <div className="pricing-card">
                <div className="pricing-price">Loading...</div>
              </div>
            </div>
          ) : (
            <div className="pricing-grid">
              {plans.filter((p: any) => p.type !== 'unlock').map((plan: any) => {
                // 从 API 数据直接读取，不硬编码
                const planName = plan.name
                const planPrice = plan.price
                const planOriginal = plan.original_price
                const planFeatures = plan.features
                const planBadge = plan.badge
                const isFeatured = !!planBadge
                const currency = '¥'

                return (
                  <div
                    key={plan.type}
                    className={`pricing-card ${isFeatured ? 'pricing-featured' : ''}`}
                  >
                    {isFeatured && planBadge && (
                      <div className="pricing-badge">{planBadge}</div>
                    )}
                    <h3 className="pricing-name">{planName}</h3>
                    <div className="pricing-price">
                      {planOriginal > 0 && (
                        <span className="pricing-original">{currency}{planOriginal}</span>
                      )}
                      {currency}{planPrice}
                    </div>
                    <ul className="pricing-features">
                      {Array.isArray(planFeatures) && planFeatures.map((feature: string, index: number) => (
                        <li key={index}>{feature}</li>
                      ))}
                    </ul>
                    <button
                      className="pricing-btn pricing-btn-primary"
                      onClick={() => {
                        isLoggedIn ? setShowPaymentModal(plan.type) : setShowLoginModal(true)
                      }}
                    >
                      {plan.type === 'single' ? '立即购买' : plan.type === 'semester' ? '选择标准包' : '选择进阶包'}
                    </button>
                  </div>
                )
              })}
            </div>
          )}
          <p className="pricing-note">{t('pricing.note')}</p>

          <div className="testimonials">
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
                <span className="testimonial-avatar">📚</span>
                <div>
                  <span className="testimonial-name">{t('home.testimonials.name2')}</span>
                  <span className="testimonial-role">{t('home.testimonials.role2')}</span>
                </div>
              </div>
            </div>
            <div className="testimonial-card">
              <p className="testimonial-text">{t('home.testimonials.text3')}</p>
              <div className="testimonial-author">
                <span className="testimonial-avatar">🔬</span>
                <div>
                  <span className="testimonial-name">{t('home.testimonials.name3')}</span>
                  <span className="testimonial-role">{t('home.testimonials.role3')}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <footer className="home-footer">
        <div className="footer-content">
          <div className="footer-links">
            <a href="/terms-and-conditions" className="footer-link">{t('home.footer.terms')}</a>
            <a href="/privacy-policy" className="footer-link">{t('home.footer.privacy')}</a>
            <a href="/refund-policy" className="footer-link">{t('home.footer.refund')}</a>
          </div>
          <p className="footer-copyright">© 2026 AutoOverview. All rights reserved.</p>
          <a href="https://beian.miit.gov.cn/" target="_blank" rel="noopener noreferrer" className="footer-icp">
            沪ICP备2023018158号-4
          </a>
        </div>
      </footer>

      {showLoginModal && (
        <LoginModal
          onClose={() => setShowLoginModal(false)}
          onLoginSuccess={handleLoginSuccess}
        />
      )}

      {showPaymentModal && (
        <PaymentModal
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
    </div>
  )
}
