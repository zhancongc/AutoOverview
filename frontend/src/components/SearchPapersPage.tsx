/**
 * SearchPapersPage - Free paper search tool (lead generation)
 * English-only, no login required
 */
import { useState, useEffect, useRef, useCallback } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { api } from '../api'
import { isLoggedIn as checkLoggedIn } from '../authApi'
import { LoginModal } from './LoginModal'
import './SimpleApp.css'
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

type SortMode = 'citations' | 'year'

export function SearchPapersPage() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const location = useLocation()
  const [topic, setTopic] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [papers, setPapers] = useState<Paper[]>([])
  const [statistics, setStatistics] = useState<Statistics | null>(null)
  const [error, setError] = useState('')
  const [sortMode, setSortMode] = useState<SortMode>('citations')
  const [statusIndex, setStatusIndex] = useState(0)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [hasSearched, setHasSearched] = useState(false)
  const [searchTaskId, setSearchTaskId] = useState<string | null>(null)
  const [isChineseSite, setIsChineseSite] = useState(false)
  const [isGenerating, setIsGenerating] = useState(false)
  const [isExporting, setIsExporting] = useState(false)
  const [showLoginModal, setShowLoginModal] = useState(false)
  const [pendingSearchTopic, setPendingSearchTopic] = useState('')
  const [shouldScrollToResults, setShouldScrollToResults] = useState(false)
  const statusIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  // SEO meta tags
  useEffect(() => {
    document.title = t('search_papers.meta.title')
    const existing = document.querySelector('meta[name="description"]')
    const desc = t('search_papers.meta.description')
    if (existing) {
      existing.setAttribute('content', desc)
    } else {
      const meta = document.createElement('meta')
      meta.name = 'description'
      meta.content = desc
      document.head.appendChild(meta)
    }
    // Check if Chinese site
    setIsChineseSite(!document.documentElement.classList.contains('intl'))
    return () => {
      document.title = 'AutoOverview - AI Literature Review Generator'
    }
  }, [t])

  // Cycling status messages during loading
  useEffect(() => {
    if (isLoading) {
      setStatusIndex(0)
      statusIntervalRef.current = setInterval(() => {
        setStatusIndex(prev => (prev + 1) % 4)
      }, 5000)
    } else {
      if (statusIntervalRef.current) {
        clearInterval(statusIntervalRef.current)
        statusIntervalRef.current = null
      }
    }
    return () => {
      if (statusIntervalRef.current) clearInterval(statusIntervalRef.current)
    }
  }, [isLoading])

  // 从 localStorage 恢复搜索状态
  const restoreSearchState = useCallback(() => {
    const savedTopic = localStorage.getItem('search_papers_topic')
    const savedTaskId = localStorage.getItem('search_papers_task_id')
    const savedPapers = localStorage.getItem('search_papers_papers')
    const savedStatistics = localStorage.getItem('search_papers_statistics')
    const savedHasSearched = localStorage.getItem('search_papers_has_searched')
    const savedShouldScroll = localStorage.getItem('search_papers_scroll_to_results')

    if (savedTopic) setTopic(savedTopic)
    if (savedTaskId) setSearchTaskId(savedTaskId)
    if (savedPapers) setPapers(JSON.parse(savedPapers))
    if (savedStatistics) setStatistics(JSON.parse(savedStatistics))
    if (savedHasSearched) setHasSearched(savedHasSearched === 'true')

    // 如果需要滚动到结果区域，设置状态标记并清除 localStorage 标记
    if (savedShouldScroll) {
      setShouldScrollToResults(true)
      localStorage.removeItem('search_papers_scroll_to_results')
    }
  }, [])

  // 组件首次挂载时恢复状态
  useEffect(() => {
    restoreSearchState()
  }, [restoreSearchState])

  // 监听路由变化，回到搜索页面时恢复状态（如果有的话）
  useEffect(() => {
    if (location.pathname === '/search-papers' && !isLoading) {
      restoreSearchState()
    }
  }, [location.pathname, isLoading, restoreSearchState])

  // 自动滚动到结果区域（从 profile 页面跳转时）
  useEffect(() => {
    if (shouldScrollToResults && hasSearched && papers.length > 0 && statistics) {
      // 使用 setTimeout 确保 DOM 已经渲染
      const timer = setTimeout(() => {
        const statisticsSection = document.querySelector('.sp-statistics')
        if (statisticsSection) {
          // 获取导航栏高度，调整滚动位置
          const navHeight = 60
          const elementPosition = statisticsSection.getBoundingClientRect().top + window.pageYOffset
          window.scrollTo({ top: elementPosition - navHeight, behavior: 'smooth' })
          setShouldScrollToResults(false)
        }
      }, 150)
      return () => clearTimeout(timer)
    }
  }, [shouldScrollToResults, hasSearched, papers.length, statistics])

  const handleSearch = useCallback(async () => {
    if (!topic.trim()) return

    // 搜索必须登录
    if (!checkLoggedIn()) {
      setPendingSearchTopic(topic)
      setShowLoginModal(true)
      return
    }

    setIsLoading(true)
    setError('')
    setPapers([])
    setStatistics(null)
    setHasSearched(true)
    setSortMode('citations')
    setSearchTaskId(null)

    // 保存搜索主题到 localStorage
    localStorage.setItem('search_papers_topic', topic)

    try {
      const response = await api.searchPapersOnly(topic, {
        targetCount: 30,
        searchYears: 10
      })

      if (response.success && response.data) {
        const papers = response.data.all_papers || []
        const stats = response.data.statistics || null
        const taskId = response.data.task_id || null

        setPapers(papers)
        setStatistics(stats)
        setSearchTaskId(taskId)

        // 保存搜索结果到 localStorage
        localStorage.setItem('search_papers_papers', JSON.stringify(papers))
        localStorage.setItem('search_papers_statistics', JSON.stringify(stats))
        localStorage.setItem('search_papers_task_id', taskId || '')
        localStorage.setItem('search_papers_has_searched', 'true')
      } else {
        setError(response.message || t('search_papers.error.generic'))
      }
    } catch (err: any) {
      if (err.code === 'ECONNABORTED' || err.message?.includes('timeout')) {
        setError(t('search_papers.error.timeout'))
      } else {
        setError(t('search_papers.error.generic'))
      }
    } finally {
      setIsLoading(false)
    }
  }, [topic, t])

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !isLoading && topic.trim()) {
      handleSearch()
    }
  }

  const handleExportPapers = async () => {
    if (papers.length === 0) return

    setIsExporting(true)
    try {
      const { Document, Packer, Paragraph, TextRun, AlignmentType, HeadingLevel } = await import('docx')
      const { saveAs } = await import('file-saver')

      const children: any[] = []

      // 标题
      children.push(new Paragraph({
        text: topic,
        heading: HeadingLevel.TITLE,
        alignment: AlignmentType.CENTER,
      }))

      // 统计
      children.push(new Paragraph({
        children: [new TextRun({ text: `${t('search_papers.results.found')} ${papers.length} ${t('search_papers.paper.citations')}`, bold: true })],
        alignment: AlignmentType.CENTER,
        spacing: { after: 400 },
      }))

      // 文献列表
      for (let i = 0; i < sortedPapers.length; i++) {
        const paper = sortedPapers[i]

        // [序号] 标题
        children.push(new Paragraph({
          children: [new TextRun({ text: `[${i + 1}] ${paper.title}`, bold: true })],
          spacing: { before: 200 },
        }))

        // 作者
        if (paper.authors && paper.authors.length > 0) {
          const authorText = paper.authors.slice(0, 5).join(', ') + (paper.authors.length > 5 ? ' et al.' : '')
          children.push(new Paragraph({
            children: [new TextRun({ text: `    Authors: ${authorText}`, size: 20 })],
          }))
        }

        // 元信息
        const metaParts: string[] = []
        if (paper.year) metaParts.push(`Year: ${paper.year}`)
        if (paper.cited_by_count > 0) metaParts.push(`Citations: ${paper.cited_by_count}`)
        if (paper.doi) metaParts.push(`DOI: ${paper.doi}`)
        if (metaParts.length > 0) {
          children.push(new Paragraph({
            children: [new TextRun({ text: `    ${metaParts.join(' | ')}`, size: 20 })],
          }))
        }

        // 摘要
        if (paper.abstract) {
          const abstractText = paper.abstract.length > 500 ? paper.abstract.substring(0, 500) + '...' : paper.abstract
          children.push(new Paragraph({
            children: [new TextRun({ text: `    Abstract: ${abstractText}`, size: 20, italics: true })],
          }))
        }
      }

      const doc = new Document({
        sections: [{ children }],
      })

      const blob = await Packer.toBlob(doc)
      const safeName = topic.replace(/[\/\\:]/g, '-').substring(0, 50)
      saveAs(blob, `${safeName}_papers.docx`)
    } catch (err) {
      console.error('Export failed:', err)
      setError(t('search_papers.error.generic'))
    } finally {
      setIsExporting(false)
    }
  }

  const handleGenerateFromSearch = async () => {
    if (!searchTaskId || !topic.trim()) return

    const loggedIn = checkLoggedIn()
    if (!loggedIn) {
      // 未登录：跳转首页 generate 区域，带上复用参数，登录后自动继续
      navigate(`/?reuse_task_id=${searchTaskId}&topic=${encodeURIComponent(topic)}#generate`)
      return
    }

    // 检查是否已有进行中的综述任务
    try {
      const activeTask = await api.getActiveTask()
      if (activeTask.active && activeTask.task_id) {
        // 已有活跃任务，提示后跳转到首页展示进度
        setError(t('search_papers.error.active_task', '您已有一个正在生成中的综述任务'))
        setTimeout(() => {
          navigate(`/?task_id=${activeTask.task_id}#generate`)
        }, 1500)
        return
      }
    } catch {
      // 获取失败不阻塞，继续提交
    }

    setIsGenerating(true)
    try {
      const response = await api.submitReviewTask(topic, {
        language: 'zh',
        reuseTaskId: searchTaskId,
      })

      if (response.success && response.data?.task_id) {
        // 跳转首页 generate 区域，展示进度条
        navigate(`/?task_id=${response.data.task_id}#generate`)
      } else {
        const msg = response.message || ''
        if (msg.includes('credits') || msg.includes('额度')) {
          // 额度不足，跳转首页定价区域购买
          navigate(`/?reuse_task_id=${searchTaskId}&topic=${encodeURIComponent(topic)}#pricing`)
        } else {
          setError(msg || t('search_papers.error.generic'))
        }
      }
    } catch {
      setError(t('search_papers.error.generic'))
    } finally {
      setIsGenerating(false)
    }
  }

  const sortPapers = useCallback((papers: Paper[], mode: SortMode): Paper[] => {
    const sorted = [...papers]
    if (mode === 'year') {
      sorted.sort((a, b) => (b.year || 0) - (a.year || 0))
    } else {
      sorted.sort((a, b) => (b.cited_by_count || 0) - (a.cited_by_count || 0))
    }
    return sorted
  }, [])

  const sortedPapers = sortPapers(papers, sortMode)
  const [loggedIn, setLoggedIn] = useState(checkLoggedIn())

  const handleLoginSuccess = useCallback(() => {
    setShowLoginModal(false)
    setLoggedIn(true)
    // 如果有待搜索的主题，自动继续搜索
    if (pendingSearchTopic) {
      setTopic(pendingSearchTopic)
      setPendingSearchTopic('')
      // 延迟执行搜索，等 state 更新
      setTimeout(() => {
        // 直接调用搜索 API
        const doSearch = async () => {
          setIsLoading(true)
          setError('')
          setPapers([])
          setStatistics(null)
          setHasSearched(true)
          setSortMode('citations')
          setSearchTaskId(null)
          localStorage.setItem('search_papers_topic', pendingSearchTopic)
          try {
            const response = await api.searchPapersOnly(pendingSearchTopic, {
              targetCount: 30,
              searchYears: 10
            })
            if (response.success && response.data) {
              setPapers(response.data.papers || [])
              setStatistics(response.data.statistics || null)
              setSearchTaskId(response.data.task_id || null)
            } else {
              setError(response.message || 'Search failed')
            }
          } catch (err: any) {
            setError(err.response?.data?.detail || t('search_papers.error.generic'))
          } finally {
            setIsLoading(false)
          }
        }
        doSearch()
      }, 100)
    }
  }, [pendingSearchTopic, t])

  const statusMessages = [
    t('search_papers.loading.status_1'),
    t('search_papers.loading.status_2'),
    t('search_papers.loading.status_3'),
    t('search_papers.loading.status_4'),
  ]

  return (
    <div className="search-papers-page">
      {/* Navigation */}
      <nav className="home-nav">
        <div className="nav-logo" onClick={() => navigate('/')} style={{ cursor: 'pointer' }}>
          <span className="logo-icon">📚</span>
          <span className="logo-text">AutoOverview</span>
        </div>
        <div className="nav-links">
          <a href="/search-papers" className="active">{t('search_papers.nav.search')}</a>
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

      {/* Hero */}
      <div className="sp-hero">
        <span className="sp-hero-badge">{t('search_papers.hero.badge')}</span>
        <h1>{t('search_papers.hero.title')}</h1>
        <p className="sp-hero-subtitle">{t('search_papers.hero.subtitle')}</p>
      </div>

      {/* Search Input */}
      <div className="sp-search-section">
        <div className="sp-search-card">
          <textarea
            className="sp-search-input"
            placeholder={t('search_papers.input.placeholder')}
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isLoading}
            rows={2}
          />
          <div className="sp-search-actions">
            <button
              className="sp-search-btn"
              onClick={handleSearch}
              disabled={isLoading || !topic.trim()}
            >
              {isLoading ? t('search_papers.input.button_searching') : t('search_papers.input.button')}
            </button>
          </div>
          <p className="sp-search-helper">{t('search_papers.input.helper')}</p>
          {loggedIn && (
            <div className="sp-search-history-link">
              <button
                className="sp-history-btn"
                onClick={() => navigate('/profile?tab=searches')}
              >
                {t('search_papers.history')}
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Loading */}
      {isLoading && (
        <div className="sp-loading">
          <div className="sp-loading-card">
            <div className="sp-progress-bar">
              <div className="sp-progress-fill" />
            </div>
            <p className="sp-loading-status">{statusMessages[statusIndex]}</p>
            <p className="sp-loading-estimate">{t('search_papers.loading.estimate')}</p>
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
      {error && !isLoading && (
        <div className="sp-error">
          <div className="sp-error-card">
            <p className="sp-error-message">{error}</p>
            <button className="sp-error-retry" onClick={handleSearch}>
              {t('search_papers.error.retry')}
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

      {/* Comparison Matrix CTA */}
      {!isLoading && papers.length > 0 && (
        <div className="sp-comparison-cta">
          <div className="sp-comparison-cta-card">
            <div className="sp-comparison-icon">📊</div>
            <div className="sp-comparison-content">
              <h3>生成文献对比矩阵</h3>
              <p>仅需 ¥5.00，即可获取观点对比、分歧原因分析和对比表格</p>
            </div>
            <button className="sp-comparison-btn" onClick={() => alert('文献对比矩阵功能即将上线！')}>
              立即生成 (¥5.00)
            </button>
          </div>
        </div>
      )}

      {/* Results */}
      {!isLoading && papers.length > 0 && (
        <div className="sp-results">
          <div className="sp-results-header">
            <div className="sp-sort-controls">
              <span>{t('search_papers.results.sort_by')}:</span>
              {(['citations', 'year'] as SortMode[]).map(mode => (
                <button
                  key={mode}
                  className={`sp-sort-btn ${sortMode === mode ? 'active' : ''}`}
                  onClick={() => setSortMode(mode)}
                >
                  {t(`search_papers.results.sort_${mode}`)}
                </button>
              ))}
            </div>
            <div className="sp-action-buttons">
              <button
                className="sp-btn-generate"
                onClick={handleGenerateFromSearch}
                disabled={isGenerating || !searchTaskId}
              >
                {isGenerating ? t('search_papers.cta.button') + '...' : t('search_papers.cta.button')}
              </button>
              <button
                className="sp-btn-export"
                onClick={handleExportPapers}
                disabled={isExporting}
              >
                {isExporting ? t('search_papers.results.exporting') : t('search_papers.results.export')}
              </button>
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
      {hasSearched && !isLoading && papers.length === 0 && !error && (
        <div className="sp-no-results">
          <div className="sp-no-results-card">
            <div className="sp-no-results-icon">🔍</div>
            <p className="sp-no-results-text">{t('search_papers.results.no_results')}</p>
          </div>
        </div>
      )}

      {/* CTA Funnel */}
      {hasSearched && !isLoading && papers.length > 0 && (
        <div className="sp-cta">
          <div className="sp-cta-card">
            <h2 className="sp-cta-title">{t('search_papers.cta.title')}</h2>
            <p className="sp-cta-desc">{t('search_papers.cta.description')}</p>
            <button
              className="sp-cta-btn"
              onClick={handleGenerateFromSearch}
              disabled={isGenerating || !searchTaskId}
            >
              {isGenerating ? t('home.input.button_generating') : t('search_papers.cta.button')}
            </button>
            <p className="sp-cta-badge">
              {t('search_papers.cta.badge')} <a href="/">AutoOverview</a>
            </p>
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
        {isChineseSite && (
          <a href="https://beian.miit.gov.cn/" target="_blank" rel="noopener noreferrer" className="sp-footer-icp">
            沪ICP备2023018158号-4
          </a>
        )}
      </footer>

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
