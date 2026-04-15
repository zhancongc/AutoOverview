/**
 * ComparisonMatrixPage - 文献对比矩阵展示页面
 */
import { useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { api } from '../api'
import { isLoggedIn } from '../authApi'
import { LoginModal } from './LoginModal'
import './ComparisonMatrixPage.css'

interface ComparisonMatrixData {
  topic: string
  comparison_matrix: string
  statistics: {
    papers_used: number
    total_time_seconds: number
    generated_at: string
  }
}

// 生成对比矩阵的模态框组件
function GenerateComparisonModal({
  isOpen,
  onClose,
  onSubmit,
  loading,
  t
}: {
  isOpen: boolean
  onClose: () => void
  onSubmit: (topic: string) => void
  loading: boolean
  t: (key: string) => string
}) {
  const [topic, setTopic] = useState('')

  if (!isOpen) return null

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{t('comparison_matrix_page.generate_title')}</h2>
          <button className="modal-close" onClick={onClose}>&times;</button>
        </div>
        <div className="modal-body">
          <input
            type="text"
            className="topic-input"
            placeholder={t('comparison_matrix_page.topic_placeholder')}
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            disabled={loading}
          />
        </div>
        <div className="modal-footer">
          <button className="modal-btn modal-btn-cancel" onClick={onClose} disabled={loading}>
            {t('comparison_matrix_page.cancel')}
          </button>
          <button
            className="modal-btn modal-btn-primary"
            onClick={() => onSubmit(topic)}
            disabled={loading || !topic.trim()}
          >
            {loading ? t('comparison_matrix_page.generating') : t('comparison_matrix_page.generate_now')}
          </button>
        </div>
      </div>
    </div>
  )
}

export function ComparisonMatrixPage() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const taskId = searchParams.get('task_id') || ''
  const [isChineseSite, setIsChineseSite] = useState(false)
  const [showLoginModal, setShowLoginModal] = useState(false)
  const [showGenerateModal, setShowGenerateModal] = useState(false)
  const [generateLoading, setGenerateLoading] = useState(false)
  const [loggedIn, setLoggedIn] = useState(isLoggedIn())
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  const [matrixData, setMatrixData] = useState<ComparisonMatrixData | null>(null)
  const [loading, setLoading] = useState(false)
  const [loadingMessage, setLoadingMessage] = useState('')
  const [error, setError] = useState('')
  const [progress, setProgress] = useState(0) // 0-100

  useEffect(() => {
    document.documentElement.classList.contains('intl') ? setIsChineseSite(false) : setIsChineseSite(true)
  }, [])

  useEffect(() => {
    if (taskId) {
      loadMatrixData(taskId)
    }
  }, [taskId])

  const loadMatrixData = async (id: string) => {
    try {
      setLoading(true)
      setLoadingMessage(t('comparison_matrix_page.loading'))
      setError('')
      setProgress(10)

      // 首先尝试轮询任务状态，直到完成
      let attempts = 0
      const maxAttempts = 120 // 最多轮询10分钟（每5秒一次）

      while (attempts < maxAttempts) {
        attempts++

        // 更新进度条（最多到90%，留10%给最后完成）
        setProgress(Math.min(10 + (attempts / maxAttempts) * 80, 90))

        try {
          // 先尝试直接获取对比矩阵
          const result = await api.getComparisonMatrix(id)
          if (result.success && result.data) {
            setMatrixData({
              topic: result.data.topic,
              comparison_matrix: result.data.comparison_matrix,
              statistics: result.data.statistics
            })
            setProgress(100)
            setLoading(false)
            return
          }
        } catch (err: any) {
          // 如果404说明还没完成，继续轮询任务状态
          if (err.response?.status !== 404) {
            throw err
          }
        }

        // 轮询任务状态
        try {
          const taskResult = await api.getTaskStatus(id)
          if (taskResult.success && taskResult.data) {
            const task = taskResult.data

            if (task.status === 'completed' && task.result) {
              // 任务完成，有结果
              setMatrixData({
                topic: task.result.topic || task.topic,
                comparison_matrix: task.result.comparison_matrix,
                statistics: task.result.statistics
              })
              setProgress(100)
              setLoading(false)
              return
            } else if (task.status === 'failed') {
              setError(task.error || t('comparison_matrix_page.error'))
              setLoading(false)
              return
            } else if (task.status === 'processing' || task.status === 'pending') {
              // 更新加载状态信息
              if (task.progress?.message) {
                setLoadingMessage(task.progress.message)
              }
            }
          }
        } catch {
          // 忽略轮询错误
        }

        // 等待5秒后继续轮询
        await new Promise(resolve => setTimeout(resolve, 5000))
      }

      // 超时
      setError(t('comparison_matrix_page.error') || '生成超时，请稍后重试')
      setLoading(false)

    } catch (err: any) {
      setError(err.message || t('comparison_matrix_page.error'))
      setLoading(false)
    }
  }

  const handleLoginSuccess = () => {
    setShowLoginModal(false)
    setLoggedIn(true)
  }

  const handleGenerateClick = () => {
    if (!loggedIn) {
      setShowLoginModal(true)
      return
    }
    setShowGenerateModal(true)
  }

  const handleGenerateSubmit = async (topic: string) => {
    if (!topic.trim()) return

    setGenerateLoading(true)
    try {
      // 检查是否有进行中的任务
      const activeTask = await api.getActiveTask()
      if (activeTask.active) {
        alert(t('search_papers.has_active_task'))
        return
      }

      const result = await api.generateComparisonMatrix(topic, {
        language: isChineseSite ? 'zh' : 'en'
      })

      if (result.success && result.data) {
        setShowGenerateModal(false)
        navigate(`/comparison-matrix?task_id=${result.data.task_id}`)
      } else {
        alert(result.message || t('comparison_matrix_page.error'))
      }
    } catch (err: any) {
      console.error('Generate comparison matrix failed:', err)
      alert(err.message || t('comparison_matrix_page.error'))
    } finally {
      setGenerateLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="comparison-matrix-page">
        {/* Navigation */}
        <nav className="home-nav">
          <div className="nav-logo" onClick={() => navigate('/')} style={{ cursor: 'pointer' }}>
            <span className="logo-icon">📚</span>
            <span className="logo-text">AutoOverview</span>
          </div>
          <div className="nav-links">
            <a href="/search-papers" onClick={(e) => { e.preventDefault(); navigate('/search-papers') }}>{t('search_papers.nav.search')}</a>
            <a href="/" onClick={(e) => { e.preventDefault(); navigate('/') }}>{t('search_papers.nav.generate')}</a>
            <a href="/#pricing" onClick={(e) => { e.preventDefault(); navigate('/#pricing') }}>{t('search_papers.nav.pricing')}</a>
          </div>
          <div className="nav-actions">
            <button className="nav-btn nav-btn-primary nav-generate-btn" onClick={handleGenerateClick}>
              {t('comparison_matrix_page.nav_generate')}
            </button>
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
            <a href="/search-papers" onClick={(e) => { e.preventDefault(); setMobileMenuOpen(false) }}>{t('search_papers.nav.search')}</a>
            <a href="/" onClick={(e) => { e.preventDefault(); setMobileMenuOpen(false); navigate('/') }}>{t('search_papers.nav.generate')}</a>
            <a href="/#pricing" onClick={(e) => { e.preventDefault(); setMobileMenuOpen(false); navigate('/#pricing') }}>{t('search_papers.nav.pricing')}</a>
            <button
              className="sidebar-generate-btn"
              onClick={() => {
                setMobileMenuOpen(false)
                handleGenerateClick()
              }}
            >
              {t('comparison_matrix_page.nav_generate')}
            </button>
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

        <div className="loading-container">
          <div className="progress-bar-container">
            <div className="progress-bar" style={{ width: `${progress}%` }}></div>
          </div>
          <p>{loadingMessage || t('comparison_matrix_page.loading')}</p>
        </div>

        {/* Login Modal */}
        {showLoginModal && (
          <LoginModal
            onClose={() => setShowLoginModal(false)}
            onLoginSuccess={handleLoginSuccess}
          />
        )}
      </div>
    )
  }

  if (error) {
    return (
      <div className="comparison-matrix-page">
        {/* Navigation */}
        <nav className="home-nav">
          <div className="nav-logo" onClick={() => navigate('/')} style={{ cursor: 'pointer' }}>
            <span className="logo-icon">📚</span>
            <span className="logo-text">AutoOverview</span>
          </div>
          <div className="nav-links">
            <a href="/search-papers" onClick={(e) => { e.preventDefault(); navigate('/search-papers') }}>{t('search_papers.nav.search')}</a>
            <a href="/" onClick={(e) => { e.preventDefault(); navigate('/') }}>{t('search_papers.nav.generate')}</a>
            <a href="/#pricing" onClick={(e) => { e.preventDefault(); navigate('/#pricing') }}>{t('search_papers.nav.pricing')}</a>
          </div>
          <div className="nav-actions">
            <button className="nav-btn nav-btn-primary nav-generate-btn" onClick={handleGenerateClick}>
              {t('comparison_matrix_page.nav_generate')}
            </button>
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
            <a href="/search-papers" onClick={(e) => { e.preventDefault(); setMobileMenuOpen(false) }}>{t('search_papers.nav.search')}</a>
            <a href="/" onClick={(e) => { e.preventDefault(); setMobileMenuOpen(false); navigate('/') }}>{t('search_papers.nav.generate')}</a>
            <a href="/#pricing" onClick={(e) => { e.preventDefault(); setMobileMenuOpen(false); navigate('/#pricing') }}>{t('search_papers.nav.pricing')}</a>
            <button
              className="sidebar-generate-btn"
              onClick={() => {
                setMobileMenuOpen(false)
                handleGenerateClick()
              }}
            >
              {t('comparison_matrix_page.nav_generate')}
            </button>
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

        <div className="error-container">
          <p>{error}</p>
          <button onClick={() => navigate(-1)} className="back-btn">
            {t('comparison_matrix_page.back')}
          </button>
        </div>

        {/* Login Modal */}
        {showLoginModal && (
          <LoginModal
            onClose={() => setShowLoginModal(false)}
            onLoginSuccess={handleLoginSuccess}
          />
        )}
      </div>
    )
  }

  if (!matrixData) {
    return (
      <div className="comparison-matrix-page">
        {/* Navigation */}
        <nav className="home-nav">
          <div className="nav-logo" onClick={() => navigate('/')} style={{ cursor: 'pointer' }}>
            <span className="logo-icon">📚</span>
            <span className="logo-text">AutoOverview</span>
          </div>
          <div className="nav-links">
            <a href="/search-papers" onClick={(e) => { e.preventDefault(); navigate('/search-papers') }}>{t('search_papers.nav.search')}</a>
            <a href="/" onClick={(e) => { e.preventDefault(); navigate('/') }}>{t('search_papers.nav.generate')}</a>
            <a href="/#pricing" onClick={(e) => { e.preventDefault(); navigate('/#pricing') }}>{t('search_papers.nav.pricing')}</a>
          </div>
          <div className="nav-actions">
            <button className="nav-btn nav-btn-primary nav-generate-btn" onClick={handleGenerateClick}>
              {t('comparison_matrix_page.nav_generate')}
            </button>
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
            <a href="/search-papers" onClick={(e) => { e.preventDefault(); setMobileMenuOpen(false) }}>{t('search_papers.nav.search')}</a>
            <a href="/" onClick={(e) => { e.preventDefault(); setMobileMenuOpen(false); navigate('/') }}>{t('search_papers.nav.generate')}</a>
            <a href="/#pricing" onClick={(e) => { e.preventDefault(); setMobileMenuOpen(false); navigate('/#pricing') }}>{t('search_papers.nav.pricing')}</a>
            <button
              className="sidebar-generate-btn"
              onClick={() => {
                setMobileMenuOpen(false)
                handleGenerateClick()
              }}
            >
              {t('comparison_matrix_page.nav_generate')}
            </button>
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

        <div className="error-container">
          <p>{t('comparison_matrix_page.not_found')}</p>
          <button onClick={() => navigate('/search-papers')} className="back-btn">
            {t('comparison_matrix_page.go_search')}
          </button>
        </div>

        {/* Login Modal */}
        {showLoginModal && (
          <LoginModal
            onClose={() => setShowLoginModal(false)}
            onLoginSuccess={handleLoginSuccess}
          />
        )}
      </div>
    )
  }

  return (
    <div className="comparison-matrix-page">
      {/* Navigation */}
      <nav className="home-nav">
        <div className="nav-logo" onClick={() => navigate('/')} style={{ cursor: 'pointer' }}>
          <span className="logo-icon">📚</span>
          <span className="logo-text">AutoOverview</span>
        </div>
        <div className="nav-links">
          <a href="/search-papers" onClick={(e) => { e.preventDefault(); navigate('/search-papers') }}>{t('search_papers.nav.search')}</a>
          <a href="/" onClick={(e) => { e.preventDefault(); navigate('/') }}>{t('search_papers.nav.generate')}</a>
          <a href="/#pricing" onClick={(e) => { e.preventDefault(); navigate('/#pricing') }}>{t('search_papers.nav.pricing')}</a>
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
          <a href="/search-papers" onClick={(e) => { e.preventDefault(); setMobileMenuOpen(false) }}>{t('search_papers.nav.search')}</a>
          <a href="/" onClick={(e) => { e.preventDefault(); setMobileMenuOpen(false); navigate('/') }}>{t('search_papers.nav.generate')}</a>
          <a href="/#pricing" onClick={(e) => { e.preventDefault(); setMobileMenuOpen(false); navigate('/#pricing') }}>{t('search_papers.nav.pricing')}</a>
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

      <div className="matrix-container">
        {/* Header */}
        <header className="matrix-header">
          <div className="header-content">
            <button className="back-button" onClick={() => navigate(-1)}>
              ← {t('comparison_matrix_page.back')}
            </button>
            <div className="header-title">
              <h1>{t('comparison_matrix_page.title')}</h1>
              <p className="matrix-topic">{matrixData.topic}</p>
            </div>
          </div>
        </header>

        {/* Statistics Bar */}
        <div className="matrix-stats">
          <div className="stat-item">
            <span className="stat-label">{t('comparison_matrix_page.papers_used')}</span>
            <span className="stat-value">{matrixData.statistics.papers_used} {t('comparison_matrix_page.papers_unit')}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">{t('comparison_matrix_page.time_used')}</span>
            <span className="stat-value">{matrixData.statistics.total_time_seconds} {t('comparison_matrix_page.time_unit')}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">{t('comparison_matrix_page.generated_at')}</span>
            <span className="stat-value">
              {new Date(matrixData.statistics.generated_at).toLocaleString()}
            </span>
          </div>
        </div>

        {/* Matrix Content */}
        <div className="matrix-content">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              table: ({ ...props }) => (
                <div className="table-wrapper">
                  <table {...props} />
                </div>
              ),
              th: ({ ...props }) => <th {...props} />,
              td: ({ ...props }) => <td {...props} />
            }}
          >
            {matrixData.comparison_matrix}
          </ReactMarkdown>
        </div>

        {/* Actions */}
        <div className="matrix-actions">
          <button
            className="action-btn action-btn-primary"
            onClick={() => alert(t('comparison_matrix_page.coming_soon'))}
          >
            {t('comparison_matrix_page.export_markdown')}
          </button>
          <button
            className="action-btn"
            onClick={() => navigate('/search-papers')}
          >
            {t('comparison_matrix_page.continue_search')}
          </button>
        </div>
      </div>

      {/* Login Modal */}
      {showLoginModal && (
        <LoginModal
          onClose={() => setShowLoginModal(false)}
          onLoginSuccess={handleLoginSuccess}
        />
      )}

      {/* Generate Comparison Matrix Modal */}
      <GenerateComparisonModal
        isOpen={showGenerateModal}
        onClose={() => setShowGenerateModal(false)}
        onSubmit={handleGenerateSubmit}
        loading={generateLoading}
        t={t}
      />
    </div>
  )
}
