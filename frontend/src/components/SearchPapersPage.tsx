/**
 * SearchPapersPage - Free paper search tool (lead generation)
 * English-only, no login required
 */
import { useState, useEffect, useRef, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { api } from '../api'
import { isLoggedIn as checkLoggedIn } from '../authApi'
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

type SortMode = 'default' | 'year' | 'citations'

export function SearchPapersPage() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const [topic, setTopic] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [papers, setPapers] = useState<Paper[]>([])
  const [statistics, setStatistics] = useState<Statistics | null>(null)
  const [error, setError] = useState('')
  const [sortMode, setSortMode] = useState<SortMode>('default')
  const [statusIndex, setStatusIndex] = useState(0)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [hasSearched, setHasSearched] = useState(false)
  const [searchTaskId, setSearchTaskId] = useState<string | null>(null)
  const [isGenerating, setIsGenerating] = useState(false)
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

  const handleSearch = useCallback(async () => {
    if (!topic.trim()) return

    setIsLoading(true)
    setError('')
    setPapers([])
    setStatistics(null)
    setHasSearched(true)
    setSortMode('default')
    setSearchTaskId(null)

    try {
      const response = await api.searchPapersOnly(topic, {
        targetCount: 30,
        searchYears: 10
      })

      if (response.success && response.data) {
        setPapers(response.data.all_papers || [])
        setStatistics(response.data.statistics || null)
        setSearchTaskId(response.data.task_id || null)
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

  const handleGenerateFromSearch = async () => {
    if (!searchTaskId || !topic.trim()) return

    const loggedIn = checkLoggedIn()
    if (!loggedIn) {
      // 未登录：跳转首页，带上复用参数，登录后自动继续
      navigate(`/?reuse_task_id=${searchTaskId}&topic=${encodeURIComponent(topic)}`)
      return
    }

    setIsGenerating(true)
    try {
      const response = await api.submitReviewTask(topic, {
        language: 'en',
        reuseTaskId: searchTaskId,
      })

      if (response.success && response.data?.task_id) {
        navigate(`/review?task_id=${response.data.task_id}`)
      } else {
        const msg = response.message || ''
        if (msg.includes('credits') || msg.includes('额度')) {
          // 额度不足，跳转首页购买
          navigate(`/?reuse_task_id=${searchTaskId}&topic=${encodeURIComponent(topic)}`)
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
    } else if (mode === 'citations') {
      sorted.sort((a, b) => (b.cited_by_count || 0) - (a.cited_by_count || 0))
    }
    return sorted
  }, [])

  const sortedPapers = sortPapers(papers, sortMode)
  const loggedIn = checkLoggedIn()

  const statusMessages = [
    t('search_papers.loading.status_1'),
    t('search_papers.loading.status_2'),
    t('search_papers.loading.status_3'),
    t('search_papers.loading.status_4'),
  ]

  return (
    <div className="search-papers-page">
      {/* Navigation */}
      <nav className="sp-nav">
        <a className="sp-nav-logo" href="/" onClick={(e) => { e.preventDefault(); navigate('/') }}>
          <span className="logo-icon">📚</span>
          <span className="logo-text">AutoOverview</span>
        </a>
        <div className="sp-nav-links">
          <a href="/search-papers" className="active">{t('search_papers.nav.search')}</a>
          <a href="/" onClick={(e) => { e.preventDefault(); navigate('/') }}>{t('search_papers.nav.generate')}</a>
          <a href="/#pricing" onClick={(e) => { e.preventDefault(); navigate('/#pricing') }}>{t('search_papers.nav.pricing')}</a>
        </div>
        <div className="sp-nav-actions">
          {loggedIn ? (
            <button className="sp-nav-btn sp-nav-btn-primary" onClick={() => navigate('/profile')}>
              {t('home.nav.profile')}
            </button>
          ) : (
            <button className="sp-nav-btn sp-nav-btn-primary" onClick={() => navigate('/login')}>
              {t('home.nav.login_register')}
            </button>
          )}
        </div>
        <button className="sp-mobile-toggle" onClick={() => setMobileMenuOpen(!mobileMenuOpen)}>
          <span className="hamburger" />
        </button>
      </nav>

      {/* Mobile sidebar */}
      <div
        className={`sp-sidebar-overlay ${mobileMenuOpen ? 'sp-sidebar-overlay-open' : ''}`}
        onClick={() => setMobileMenuOpen(false)}
      />
      <aside className={`sp-sidebar ${mobileMenuOpen ? 'sp-sidebar-open' : ''}`}>
        <div className="sp-sidebar-header">
          <span className="logo-icon">📚</span>
          <span className="logo-text">AutoOverview</span>
          <button className="sp-sidebar-close" onClick={() => setMobileMenuOpen(false)}>&times;</button>
        </div>
        <nav className="sp-sidebar-nav">
          <a href="/search-papers" onClick={(e) => { e.preventDefault(); setMobileMenuOpen(false) }}>{t('search_papers.nav.search')}</a>
          <a href="/" onClick={(e) => { e.preventDefault(); setMobileMenuOpen(false); navigate('/') }}>{t('search_papers.nav.generate')}</a>
          <a href="/#pricing" onClick={(e) => { e.preventDefault(); setMobileMenuOpen(false); navigate('/#pricing') }}>{t('search_papers.nav.pricing')}</a>
          {loggedIn ? (
            <a href="/profile" onClick={(e) => { e.preventDefault(); setMobileMenuOpen(false); navigate('/profile') }}>{t('home.nav.profile')}</a>
          ) : (
            <a href="/login" onClick={(e) => { e.preventDefault(); setMobileMenuOpen(false); navigate('/login') }}>{t('home.nav.login_register')}</a>
          )}
        </nav>
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
        </div>
      </div>

      {/* Data Sources */}
      <div className="sp-sources">
        <p className="sp-sources-title">{t('home.sources.title')}</p>
        <div className="sp-sources-logos">
          <span className="sp-source-logo">Web of Science</span>
          <span className="sp-source-logo">IEEE Xplore</span>
          <span className="sp-source-logo">CrossRef</span>
          <span className="sp-source-logo">Semantic Scholar</span>
        </div>
      </div>

      {/* Loading */}
      {isLoading && (
        <div className="sp-loading">
          <div className="sp-loading-card">
            <p className="sp-loading-title">{t('search_papers.loading.title')}</p>
            <div className="sp-progress-bar">
              <div className="sp-progress-fill" />
            </div>
            <p className="sp-loading-status">{statusMessages[statusIndex]}</p>
            <p className="sp-loading-estimate">{t('search_papers.loading.estimate')}</p>
          </div>
        </div>
      )}

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
            <span className="sp-stat-badge sp-stat-badge-primary">
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
      {!isLoading && papers.length > 0 && (
        <div className="sp-results">
          <div className="sp-results-header">
            <div className="sp-sort-controls">
              <span>{t('search_papers.results.sort_by')}:</span>
              {(['default', 'year', 'citations'] as SortMode[]).map(mode => (
                <button
                  key={mode}
                  className={`sp-sort-btn ${sortMode === mode ? 'active' : ''}`}
                  onClick={() => setSortMode(mode)}
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
      {hasSearched && !isLoading && papers.length === 0 && !error && (
        <div className="sp-no-results">
          <div className="sp-no-results-card">
            <div className="sp-no-results-icon">🔍</div>
            <p className="sp-no-results-text">{t('search_papers.results.no_results')}</p>
          </div>
        </div>
      )}

      {/* CTA Funnel */}
      {hasSearched && !isLoading && (
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
      </footer>
    </div>
  )
}
