/**
 * ComparisonMatrixPage - 文献对比矩阵页面
 * 支持两种模式：
 * 1. 搜索模式：输入 topic → 搜索文献 → 展示结果 → 生成对比矩阵
 * 2. 查看模式：URL 带 task_id → 直接展示矩阵结果
 */
import { useState, useEffect, useCallback } from 'react'
import { useNavigate, useSearchParams, useLocation } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { api } from '../api'
import { isLoggedIn as checkLoggedIn } from '../authApi'
import { LoginModal } from './LoginModal'
import { LoginModalInternational } from './LoginModalInternational'
import { PayPalPaymentModal } from './PayPalPaymentModal'
import './ComparisonMatrixPage.css'
import './SearchPapersPage.css'

interface Paper {
  id: string
  title: string
  authors: string[]
  year: number | null
  cited_by_count: number
  abstract: string | null
  doi: string | null
  is_english: boolean
}

interface Statistics {
  total: number
  recent_count: number
  recent_ratio: number
  english_count: number
  english_ratio: number
  total_citations: number
  avg_citations: number
}

interface ComparisonMatrixData {
  topic: string
  comparison_matrix: string
  statistics: {
    papers_used: number
    total_time_seconds: number
    generated_at: string
  }
  papers: Paper[]
}

type TabType = 'matrix' | 'references'

type SortMode = 'citations' | 'year'
type CombinedPhase = 'idle' | 'searching' | 'generating_matrix'

export function ComparisonMatrixPage() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const location = useLocation()
  const [searchParams] = useSearchParams()
  const taskId = searchParams.get('task_id') || ''

  // Site & auth
  const [isChineseSite, setIsChineseSite] = useState(false)
  const [loggedIn, setLoggedIn] = useState(checkLoggedIn())
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [showLoginModal, setShowLoginModal] = useState(false)
  const [showPaymentModal, setShowPaymentModal] = useState<string | false>(false)
  const [plans, setPlans] = useState<any[]>([])
  const [plansLoading, setPlansLoading] = useState(true)
  const [credits, setCredits] = useState<number>(0)

  // Search state
  const [topic, setTopic] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [papers, setPapers] = useState<Paper[]>([])
  const [statistics, setStatistics] = useState<Statistics | null>(null)
  const [searchError, setSearchError] = useState('')
  const [sortMode, setSortMode] = useState<SortMode>('citations')
  const [hasSearched, setHasSearched] = useState(false)
  const [searchTaskId, setSearchTaskId] = useState<string>('')

  // Matrix generation state
  const [isGeneratingReview, setIsGeneratingReview] = useState(false)

  // Pending generation state (for continuing after payment)
  const [pendingTopic, setPendingTopic] = useState<string>('')

  // Combined flow state (一键生成)
  const [combinedPhase, setCombinedPhase] = useState<CombinedPhase>('idle')
  const [combinedProgress, setCombinedProgress] = useState(0)
  const [combinedMessage, setCombinedMessage] = useState('')

  // Matrix display state
  const [matrixData, setMatrixData] = useState<ComparisonMatrixData | null>(null)
  const [matrixLoading, setMatrixLoading] = useState(false)
  const [matrixLoadingMsg, setMatrixLoadingMsg] = useState('')
  const [matrixError, setMatrixError] = useState('')
  const [progress, setProgress] = useState(0)
  const [matrixSearchTaskId, setMatrixSearchTaskId] = useState<string>('')
  const [activeTab, setActiveTab] = useState<TabType>('matrix')

  useEffect(() => {
    setIsChineseSite(!document.documentElement.classList.contains('intl'))
  }, [])

  // Load plans and credits on mount
  useEffect(() => {
    api.getSubscriptionPlans().then(data => {
      setPlans(data.plans)
      setPlansLoading(false)
    }).catch(() => {
      setPlansLoading(false)
    })

    if (checkLoggedIn()) {
      api.getCredits().then(data => {
        setCredits(data.credits)
      }).catch(() => {})
    }
  }, [])

  // If URL has task_id, load matrix directly
  useEffect(() => {
    if (taskId) {
      loadMatrixData(taskId)
    }
  }, [taskId])

  // Restore search state from localStorage
  useEffect(() => {
    const savedTopic = localStorage.getItem('cm_topic')
    const savedPapers = localStorage.getItem('cm_papers')
    const savedStats = localStorage.getItem('cm_statistics')
    const savedTaskId = localStorage.getItem('cm_search_task_id')
    const savedHasSearched = localStorage.getItem('cm_has_searched')
    if (savedTopic) setTopic(savedTopic)
    if (savedPapers) setPapers(JSON.parse(savedPapers))
    if (savedStats) setStatistics(JSON.parse(savedStats))
    if (savedTaskId) setSearchTaskId(savedTaskId)
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

  // === Poll matrix task result (shared by handleGenerateAll and restore) ===
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

          // 检查是否完成（优先从 task.result 获取数据）
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

  // === Combined: Search + Generate Matrix (一键生成) ===
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
    setSearchTaskId('')
    localStorage.setItem('cm_topic', topic)

    // --- Phase 1: Search papers ---
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
        setSearchTaskId(tid)
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
      if (err.code === 'ECONNABORTED' || err.message?.includes('timeout')) {
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

    // --- Phase 2: Generate comparison matrix ---
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

      // Save to localStorage so we can resume if user navigates away
      localStorage.setItem('cm_matrix_task_id', matrixTaskId)

      // Poll for matrix result
      await pollMatrixResult(matrixTaskId)
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || t('comparison_matrix_page.error')
      // Check if error is about insufficient credits
      if (errorMsg.toLowerCase().includes('credit') || errorMsg.toLowerCase().includes('额度')) {
        setPendingTopic(topic)
        setSearchError('')
        setCombinedPhase('idle')
        localStorage.removeItem('cm_matrix_task_id')
        // Show payment modal
        setShowPaymentModal('starter') // Default to starter plan
      } else {
        setSearchError(errorMsg)
        setCombinedPhase('idle')
        localStorage.removeItem('cm_matrix_task_id')
      }
    }
  }, [topic, t, isChineseSite, navigate])

  // Handle payment success and continue generation
  const handlePaymentSuccess = async () => {
    setShowPaymentModal(false)
    // Refresh credits
    api.getCredits().then(data => {
      setCredits(data.credits)
    }).catch(() => {})
    // If there's a pending topic, continue generating
    if (pendingTopic) {
      const topicToGenerate = pendingTopic
      setPendingTopic('')
      setTopic(topicToGenerate)
      await handleGenerateAll()
    }
  }

  // Keep handleSearch for error retry
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
    setSearchTaskId('')
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
        setSearchTaskId(tid)

        localStorage.setItem('cm_papers', JSON.stringify(foundPapers))
        localStorage.setItem('cm_statistics', JSON.stringify(stats))
        localStorage.setItem('cm_search_task_id', tid)
        localStorage.setItem('cm_has_searched', 'true')
      } else {
        setSearchError(response.message || t('comparison_matrix_page.error'))
      }
    } catch (err: any) {
      if (err.code === 'ECONNABORTED' || err.message?.includes('timeout')) {
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

  // === Load Matrix Data (polling) ===
  const loadMatrixData = async (id: string) => {
    try {
      setMatrixLoading(true)
      setMatrixLoadingMsg(t('comparison_matrix_page.loading'))
      setMatrixError('')
      setProgress(10)

      let attempts = 0
      const maxAttempts = 120

      while (attempts < maxAttempts) {
        attempts++
        setProgress(Math.min(10 + (attempts / maxAttempts) * 80, 90))

        try {
          const taskResult = await api.getTaskStatus(id)
          if (taskResult.success && taskResult.data) {
            const task = taskResult.data
            const taskData: any = task

            // 获取 reuse_task_id
            if (taskData.params?.reuse_task_id) {
              setMatrixSearchTaskId(taskData.params.reuse_task_id)
            }

            // 检查任务状态
            if (task.status === 'completed') {
              // 优先从 task.result 获取数据
              if (task.result) {
                setMatrixData({
                  topic: task.result.topic || task.topic,
                  comparison_matrix: task.result.comparison_matrix,
                  statistics: task.result.statistics,
                  papers: task.result.papers || task.params?.papers || []
                })
                setProgress(100)
                setMatrixLoading(false)
                return
              }

              // 备用：从 params 获取数据（数据库已保存）
              const params = task.params || {}
              if (params.comparison_matrix) {
                setMatrixData({
                  topic: task.topic,
                  comparison_matrix: params.comparison_matrix,
                  statistics: params.statistics || {},
                  papers: params.papers || []
                })
                setProgress(100)
                setMatrixLoading(false)
                return
              }

              // completed 但无数据 → 保存可能失败，停止轮询
              setMatrixError(t('comparison_matrix_page.error'))
              setMatrixLoading(false)
              return
            } else if (task.status === 'failed') {
              setMatrixError(task.error || t('comparison_matrix_page.error'))
              setMatrixLoading(false)
              return
            } else if (task.progress?.message) {
              setMatrixLoadingMsg(task.progress.message)
            }
          }
        } catch (err: any) {
          if (err.response?.status !== 404) throw err
        }

        await new Promise(resolve => setTimeout(resolve, 5000))
      }

      setMatrixError(t('comparison_matrix_page.error'))
      setMatrixLoading(false)
    } catch (err: any) {
      setMatrixError(err.message || t('comparison_matrix_page.error'))
      setMatrixLoading(false)
    }
  }

  // === Generate Review from Matrix ===
  const handleGenerateReview = async () => {
    if (!checkLoggedIn()) {
      setShowLoginModal(true)
      return
    }
    const reuseId = matrixSearchTaskId || searchTaskId
    if (!reuseId || !matrixData?.topic) return

    try {
      const activeTask = await api.getActiveTask()
      if (activeTask.active) {
        alert(t('comparison_matrix_page.error'))
        return
      }
    } catch { /* don't block */ }

    setIsGeneratingReview(true)
    try {
      const response = await api.submitReviewTask(matrixData.topic, {
        language: isChineseSite ? 'zh' : 'en',
        reuseTaskId: reuseId,
      })
      if (response.success && response.data?.task_id) {
        navigate(`/?task_id=${response.data.task_id}#generate`)
      } else {
        const msg = response.message || ''
        if (msg.includes('credits') || msg.includes('额度')) {
          navigate(`/?reuse_task_id=${reuseId}&topic=${encodeURIComponent(matrixData.topic)}#pricing`)
        } else {
          alert(msg || t('comparison_matrix_page.error'))
        }
      }
    } catch (err: any) {
      alert(err.message || t('comparison_matrix_page.error'))
    } finally {
      setIsGeneratingReview(false)
    }
  }

  const handleLoginSuccess = () => {
    setShowLoginModal(false)
    setLoggedIn(true)
    // Refresh credits after login
    api.getCredits().then(data => {
      setCredits(data.credits)
    }).catch(() => {})
  }

  // === Export Markdown ===
  const handleExportMarkdown = () => {
    if (!matrixData) return
    const content = `# ${matrixData.topic}\n\n${matrixData.comparison_matrix}`
    const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `comparison-matrix-${matrixData.topic.slice(0, 20).replace(/[^a-zA-Z0-9\u4e00-\u9fff]/g, '_')}.md`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
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

  // Shared nav (used in all views)
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
        <a href="/generate" className={location.pathname === '/generate' ? 'active' : ''} onClick={(e) => { e.preventDefault(); navigate('/generate') }}>{t('search_papers.nav.generate')}</a>
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
          <span className="logo-text">AutoOverview</span>
          <button className="sidebar-close" onClick={() => setMobileMenuOpen(false)}>&times;</button>
        </div>
        <nav className="sidebar-links">
          <a href="/" className={location.pathname === '/' ? 'active' : ''} onClick={(e) => { e.preventDefault(); setMobileMenuOpen(false); navigate('/') }}>{t('nav.home')}</a>
          <a href="/search-papers" className={location.pathname === '/search-papers' ? 'active' : ''} onClick={(e) => { e.preventDefault(); setMobileMenuOpen(false); navigate('/search-papers') }}>{t('search_papers.nav.search')}</a>
          <a href="/comparison-matrix" className={location.pathname === '/comparison-matrix' ? 'active' : ''} onClick={(e) => { e.preventDefault(); setMobileMenuOpen(false) }}>{t('search_papers.nav.comparison_matrix')}</a>
          <a href="/generate" className={location.pathname === '/generate' ? 'active' : ''} onClick={(e) => { e.preventDefault(); setMobileMenuOpen(false); navigate('/generate') }}>{t('search_papers.nav.generate')}</a>
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

  // ========== VIEW 1: Matrix loading ==========
  if (matrixLoading) {
    return (
      <div className="comparison-matrix-page">
        {renderNav()}
        {renderMobileSidebar()}
        <div className="loading-container">
          <div className="progress-bar-container">
            <div className="progress-bar" style={{ width: `${progress}%` }}></div>
          </div>
          <p>{matrixLoadingMsg || t('comparison_matrix_page.loading')}</p>
        </div>
        {showLoginModal && <LoginModal onClose={() => setShowLoginModal(false)} onLoginSuccess={handleLoginSuccess} />}
      </div>
    )
  }

  // ========== VIEW 2: Matrix error ==========
  if (matrixError && taskId) {
    return (
      <div className="comparison-matrix-page">
        {renderNav()}
        {renderMobileSidebar()}
        <div className="error-container">
          <p>{matrixError}</p>
          <button onClick={() => { setMatrixData(null); setMatrixError(''); navigate('/comparison-matrix', { replace: true }) }} className="back-btn">
            {t('comparison_matrix_page.go_search')}
          </button>
        </div>
        {showLoginModal && <LoginModal onClose={() => setShowLoginModal(false)} onLoginSuccess={handleLoginSuccess} />}
      </div>
    )
  }

  // ========== VIEW 3: Matrix display ==========
  if (matrixData) {
    return (
      <div className="comparison-matrix-page">
        {renderNav()}
        {renderMobileSidebar()}

        <div className="matrix-container">
          <header className="matrix-header">
            <div className="header-content">
              <button className="back-button" onClick={() => { setMatrixData(null); setMatrixError(''); setMatrixLoading(false); navigate('/comparison-matrix', { replace: true }) }}>
                ←
              </button>
              <div className="header-title">
                <h1>{t('comparison_matrix_page.title')}</h1>
                <p className="matrix-topic">{matrixData.topic}</p>
              </div>
            </div>
          </header>

          <div className="matrix-stats">
            <div className="stats-left">
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
            <div className="stats-actions">
              <button
                className="stats-action-btn stats-action-btn-primary"
                onClick={handleGenerateReview}
                disabled={!matrixSearchTaskId || isGeneratingReview}
                title={!matrixSearchTaskId ? t('comparison_matrix_page.generate_review_disabled_hint') : undefined}
              >
                {isGeneratingReview ? t('comparison_matrix_page.generating') : t('comparison_matrix_page.generate_review')}
              </button>
              <button
                className="stats-action-btn"
                onClick={handleExportMarkdown}
              >
                {t('comparison_matrix_page.export_markdown')}
              </button>
              <button
                className="stats-action-btn"
                onClick={() => navigate('/comparison-matrix')}
              >
                {t('comparison_matrix_page.continue_search')}
              </button>
            </div>
          </div>

          <div className="matrix-segmented-tabs">
            <button
              className={`segmented-tab ${activeTab === 'matrix' ? 'active' : ''}`}
              onClick={() => setActiveTab('matrix')}
            >
              Comparison Matrix
            </button>
            <button
              className={`segmented-tab ${activeTab === 'references' ? 'active' : ''}`}
              onClick={() => setActiveTab('references')}
            >
              References
            </button>
          </div>

          {activeTab === 'matrix' ? (
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
          ) : (
            <div className="matrix-references">
              <h2>References</h2>
              <p className="references-summary">
                {matrixData.papers?.length || 0} papers total
                {(() => {
                  const currentYear = new Date().getFullYear()
                  const recentCount = (matrixData.papers || []).filter((p: any) => p.year && p.year >= currentYear - 5).length
                  const englishCount = (matrixData.papers || []).filter((p: any) => p.is_english).length
                  return (
                    <>
                      {matrixData.papers?.length > 0 && (
                        <>
                          {' · '}
                          <span>{recentCount} recent (last 5 years)</span>
                          {' · '}
                          <span>{englishCount} English papers</span>
                        </>
                      )}
                    </>
                  )
                })()}
              </p>
              <div className="references-list">
                {(matrixData.papers || []).map((paper: any, index: number) => (
                  <div key={paper.id || index} className="reference-item">
                    <div className="reference-number">{index + 1}</div>
                    <div className="reference-content">
                      <div className="reference-title">
                        {paper.title}
                      </div>
                      <div className="reference-meta">
                        {paper.authors?.slice(0, 3).join(', ')}{paper.authors?.length > 3 ? ' et al.' : ''}
                        {paper.year && ` · ${paper.year}`}
                        {paper.cited_by_count >= 0 && ` · ${paper.cited_by_count} citations`}
                      </div>
                      {paper.doi && (
                        <a
                          href={`https://doi.org/${paper.doi}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="reference-doi"
                        >
                          DOI: {paper.doi}
                        </a>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {showLoginModal && <LoginModal onClose={() => setShowLoginModal(false)} onLoginSuccess={handleLoginSuccess} />}
      </div>
    )
  }

  // ========== VIEW 4: Search + Generate (default landing) ==========
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
          <p className="sp-search-helper">{t('search_papers.input.helper')}</p>
        </div>
      </div>

      {/* Combined progress bar (shown during search + matrix generation) */}
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

      {/* Pending generation - show continue button */}
      {pendingTopic && !searchError && (
        <div className="sp-error">
          <div className="sp-error-card">
            <p className="sp-error-message">
              You need credits to generate the comparison matrix. Purchase credits and then continue.
            </p>
            <div style={{ display: 'flex', gap: '12px', justifyContent: 'center' }}>
              <button
                className="sp-error-retry"
                onClick={() => setShowPaymentModal('starter')}
              >
                Purchase Credits
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
                Continue Generation
              </button>
            </div>
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

      {/* Results - show during matrix generation phase too */}
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
        <p className="sp-footer-copy">&copy; {new Date().getFullYear()} AutoOverview. {t('search_papers.footer.rights')}</p>
      </footer>

      {showLoginModal && (
        <>
          {isChineseSite ? (
            <LoginModal onClose={() => setShowLoginModal(false)} onLoginSuccess={handleLoginSuccess} />
          ) : (
            <LoginModalInternational onClose={() => setShowLoginModal(false)} onLoginSuccess={handleLoginSuccess} />
          )}
        </>
      )}

      {showPaymentModal && (
        <PayPalPaymentModal
          onClose={() => setShowPaymentModal(false)}
          onPaymentSuccess={handlePaymentSuccess}
          planType={showPaymentModal}
        />
      )}
    </div>
  )
}
