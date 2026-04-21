/**
 * ProfilePage Component - International Academic Version
 * Designed for overseas market with clean, professional academic style
 */
import { useState, useEffect } from 'react'
import { useNavigate, useLocation, useSearchParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { api } from '../api'
import { getLocalUserInfo, isLoggedIn } from '../authApi'

import { PayPalPaymentModal } from './PayPalPaymentModal'
import { ConfirmModalInternational } from './ConfirmModalInternational'
import { ExportFormatModal, type ExportFormat } from './ExportFormatModal'
import type { ReviewRecord } from '../types'
import './SimpleAppInternational.css'
import './ProfilePageInternational.css'

type ProfileTab = 'reviews' | 'searches' | 'matrices'

export function ProfilePageInternational() {
  const { i18n } = useTranslation()
  const navigate = useNavigate()
  const location = useLocation()
  const [searchParams] = useSearchParams()
  const tabParam = searchParams.get('tab') as ProfileTab | null
  const activeTab: ProfileTab = tabParam && ['searches', 'matrices', 'reviews'].includes(tabParam) ? tabParam : 'searches'
  const setActiveTab = (tab: ProfileTab) => {
    navigate(`/profile?tab=${tab}`, { replace: true })
  }
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [records, setRecords] = useState<ReviewRecord[]>([])
  const [searches, setSearches] = useState<any[]>([])
  const [matrices, setMatrices] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [userInfo, setUserInfo] = useState<any>(null)
  const [credits, setCredits] = useState<number>(0)
  const [showPayModal, setShowPayModal] = useState(false)
  const [pendingExportRecordId, setPendingExportRecordId] = useState<number | null>(null)
  const [unlockMode, setUnlockMode] = useState(false)  // true=single unlock, false=purchase plan
  const [showCreditConfirmModal, setShowCreditConfirmModal] = useState(false)
  const [confirmRecordId, setConfirmRecordId] = useState<number | null>(null)
  const [showCloseAccountModal, setShowCloseAccountModal] = useState(false)
  const [closeAccountEmail, setCloseAccountEmail] = useState('')
  const [showEditProfileModal, setShowEditProfileModal] = useState(false)
  const [editNickname, setEditNickname] = useState('')
  const [exportModalSearch, setExportModalSearch] = useState<any | null>(null)
  const [exportFormat, setExportFormat] = useState<ExportFormat>('bibtex')
  const [exportingSearch, setExportingSearch] = useState(false)
  const [exportModalMatrix, setExportModalMatrix] = useState<any | null>(null)
  const [matrixExportFormat, setMatrixExportFormat] = useState<'markdown' | 'word'>('markdown')
  const [exportingMatrix, setExportingMatrix] = useState(false)
  const [exportModalReview, setExportModalReview] = useState<{ id: number; topic: string } | null>(null)
  const [reviewExportFormat, setReviewExportFormat] = useState<'markdown' | 'word'>('markdown')
  const [exportingReview, setExportingReview] = useState(false)

  useEffect(() => {
    if (!isLoggedIn()) {
      navigate('/login')
      return
    }
    setUserInfo(getLocalUserInfo())
    loadAllRecords()
    api.getCredits().then(data => {
      setCredits(data.credits)
    }).catch(err => console.error('Failed to fetch credits:', err))
  }, [navigate])

  const loadAllRecords = async () => {
    setLoading(true)
    try {
      const [recordsRes, searchesRes] = await Promise.all([
        api.getRecords(),
        api.getSearchHistory()
      ])
      if (recordsRes.success) {
        const all = recordsRes.records
        setRecords(all.filter((r: any) => r.task_type !== 'comparison_matrix'))
        setMatrices(all.filter((r: any) => r.task_type === 'comparison_matrix'))
      }
      if (searchesRes.success) {
        setSearches(searchesRes.searches)
      }
    } catch (err) {
      console.error('Failed to load records:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleViewSearch = (search: any) => {
    localStorage.setItem('search_papers_topic', search.topic)
    if (search.papers_sample) {
      localStorage.setItem('search_papers_papers', JSON.stringify(search.papers_sample))
    }
    if (search.papers_summary) {
      localStorage.setItem('search_papers_statistics', JSON.stringify(search.papers_summary))
    }
    localStorage.setItem('search_papers_task_id', search.id)
    localStorage.setItem('search_papers_has_searched', 'true')
    localStorage.setItem('search_papers_scroll_to_results', 'true')
    navigate('/search-papers')
  }

  const handleViewMatrix = (matrix: any) => {
    if (matrix.task_id) {
      navigate(`/comparison-matrix?task_id=${matrix.task_id}`)
    }
  }

  const generateBibTeX = (paperList: any[]): string => {
    return paperList.map((paper, i) => {
      const key = (paper.authors?.[0]?.split(' ').pop()?.toLowerCase() || 'unknown')
        + (paper.year || '') + '_' + (i + 1)
      const authors = paper.authors?.map((a: string) => a).join(' and ') || 'Unknown'
      let entry = `@article{${key},\n`
      entry += `  title={${paper.title}},\n`
      entry += `  author={${authors}},\n`
      if (paper.year) entry += `  year={${paper.year}},\n`
      if (paper.doi) entry += `  doi={${paper.doi}},\n`
      if (paper.abstract) entry += `  abstract={${paper.abstract}},\n`
      entry += `}`
      return entry
    }).join('\n\n')
  }

  const generateRIS = (paperList: any[]): string => {
    return paperList.map(paper => {
      let ris = `TY  - JOUR\n`
      ris += `TI  - ${paper.title}\n`
      if (paper.authors) {
        paper.authors.forEach((a: string) => { ris += `AU  - ${a}\n` })
      }
      if (paper.year) ris += `PY  - ${paper.year}\n`
      if (paper.doi) ris += `DO  - ${paper.doi}\n`
      if (paper.abstract) ris += `AB  - ${paper.abstract}\n`
      ris += `ER  - \n`
      return ris
    }).join('\n')
  }

  const handleExportSearch = async () => {
    if (!exportModalSearch) return
    setExportingSearch(true)
    try {
      const detailRes = await api.getSearchHistoryDetail(exportModalSearch.id)
      const papers = detailRes.search?.papers_sample || []
      if (papers.length === 0) return
      const safeName = exportModalSearch.topic.replace(/[\/\\:]/g, '-').substring(0, 50)
      const { saveAs } = await import('file-saver')

      if (exportFormat === 'bibtex') {
        const content = generateBibTeX(papers)
        const blob = new Blob([content], { type: 'application/x-bibtex;charset=utf-8' })
        saveAs(blob, `${safeName}.bib`)
      } else if (exportFormat === 'ris') {
        const content = generateRIS(papers)
        const blob = new Blob([content], { type: 'application/x-research-info-systems;charset=utf-8' })
        saveAs(blob, `${safeName}.ris`)
      } else {
        const { Document, Packer, Paragraph, TextRun, AlignmentType, HeadingLevel } = await import('docx')
        const children: any[] = []
        children.push(new Paragraph({ text: exportModalSearch.topic, heading: HeadingLevel.TITLE, alignment: AlignmentType.CENTER }))
        children.push(new Paragraph({ children: [new TextRun({ text: `${papers.length} papers found`, bold: true })], alignment: AlignmentType.CENTER, spacing: { after: 400 } }))
        for (let i = 0; i < papers.length; i++) {
          const paper = papers[i]
          children.push(new Paragraph({ children: [new TextRun({ text: `[${i + 1}] ${paper.title}`, bold: true })], spacing: { before: 200 } }))
          if (paper.authors?.length > 0) {
            children.push(new Paragraph({ children: [new TextRun({ text: `    Authors: ${paper.authors.slice(0, 5).join(', ')}${paper.authors.length > 5 ? ' et al.' : ''}`, size: 20 })] }))
          }
          const meta: string[] = []
          if (paper.year) meta.push(`Year: ${paper.year}`)
          if (paper.doi) meta.push(`DOI: ${paper.doi}`)
          if (meta.length > 0) children.push(new Paragraph({ children: [new TextRun({ text: `    ${meta.join(' | ')}`, size: 20 })] }))
        }
        const doc = new Document({ sections: [{ children }] })
        const blob = await Packer.toBlob(doc)
        saveAs(blob, `${safeName}.docx`)
      }
      setExportModalSearch(null)
    } catch (err) {
      console.error('Export failed:', err)
    } finally {
      setExportingSearch(false)
    }
  }

  const handleExportMatrix = async () => {
    if (!exportModalMatrix) return
    setExportingMatrix(true)
    try {
      const res = await api.getComparisonMatrix(exportModalMatrix.task_id)
      const { topic, comparison_matrix } = res.data
      if (!comparison_matrix) return
      const safeName = topic.replace(/[\/\\:]/g, '-').substring(0, 50)

      if (matrixExportFormat === 'markdown') {
        const content = `# ${topic}\n\n${comparison_matrix}`
        const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' })
        const { saveAs } = await import('file-saver')
        saveAs(blob, `${safeName}.md`)
      } else {
        const { Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType, Table, TableRow, TableCell, WidthType } = await import('docx')
        const lines = comparison_matrix.split('\n')
        const children: any[] = []
        children.push(new Paragraph({ text: topic, heading: HeadingLevel.TITLE, alignment: AlignmentType.CENTER, spacing: { after: 400 } }))

        for (const line of lines) {
          const trimmed = line.trim()
          if (!trimmed) { children.push(new Paragraph({})); continue }
          if (trimmed.startsWith('### ')) {
            children.push(new Paragraph({ text: trimmed.replace('### ', ''), heading: HeadingLevel.HEADING_3, spacing: { before: 300 } }))
          } else if (trimmed.startsWith('## ')) {
            children.push(new Paragraph({ text: trimmed.replace('## ', ''), heading: HeadingLevel.HEADING_2, spacing: { before: 300 } }))
          } else if (trimmed.startsWith('# ')) {
            children.push(new Paragraph({ text: trimmed.replace('# ', ''), heading: HeadingLevel.HEADING_1, spacing: { before: 300 } }))
          } else if (trimmed.startsWith('|') && trimmed.endsWith('|')) {
            const cells = trimmed.split('|').filter(c => c.trim()).map(c => c.trim())
            if (cells.every(c => /^[-:\s]+$/.test(c))) continue
            children.push(new Table({
              rows: [new TableRow({
                children: cells.map(cell => new TableCell({
                  children: [new Paragraph({ children: [new TextRun({ text: cell.replace(/\*\*/g, ''), bold: cell.includes('**') })] })],
                  width: { size: Math.floor(100 / cells.length), type: WidthType.PERCENTAGE },
                }))
              })],
              width: { size: 100, type: WidthType.PERCENTAGE },
            }))
          } else if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
            children.push(new Paragraph({ children: [new TextRun({ text: trimmed.replace(/^[-*]\s*/, '') })], bullet: { level: 0 } }))
          } else {
            children.push(new Paragraph({ children: [new TextRun({ text: trimmed.replace(/\*\*/g, '') })] }))
          }
        }
        const doc = new Document({ sections: [{ children }] })
        const blob = await Packer.toBlob(doc)
        const { saveAs } = await import('file-saver')
        saveAs(blob, `${safeName}.docx`)
      }
      setExportModalMatrix(null)
    } catch (err) {
      console.error('Matrix export failed:', err)
    } finally {
      setExportingMatrix(false)
    }
  }

  const doExportReview = async () => {
    if (!exportModalReview) return
    setExportingReview(true)
    try {
      const res = await api.getRecordReview(exportModalReview.id)
      const { topic, review, papers } = res.data
      const safeName = topic.replace(/[\/\\:]/g, '-').substring(0, 50)

      if (reviewExportFormat === 'markdown') {
        let content = `# ${topic}\n\n${review}\n\n## References\n\n`
        ;(papers || []).forEach((p: any, i: number) => {
          content += `[${i + 1}] ${p.authors?.join(', ') || ''}. (${p.year || ''}). ${p.title}.\n`
        })
        const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' })
        const { saveAs } = await import('file-saver')
        saveAs(blob, `${safeName}.md`)
      } else {
        const { Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType } = await import('docx')
        const lines = review.split('\n')
        const children: any[] = []
        children.push(new Paragraph({ text: topic, heading: HeadingLevel.TITLE, alignment: AlignmentType.CENTER, spacing: { after: 400 } }))
        for (const line of lines) {
          const trimmed = line.trim()
          if (!trimmed) { children.push(new Paragraph({})); continue }
          if (trimmed.startsWith('#### ')) {
            children.push(new Paragraph({ text: trimmed.replace('#### ', ''), heading: HeadingLevel.HEADING_4, spacing: { before: 300 } }))
          } else if (trimmed.startsWith('### ')) {
            children.push(new Paragraph({ text: trimmed.replace('### ', ''), heading: HeadingLevel.HEADING_3, spacing: { before: 300 } }))
          } else if (trimmed.startsWith('## ')) {
            children.push(new Paragraph({ text: trimmed.replace('## ', ''), heading: HeadingLevel.HEADING_2, spacing: { before: 300 } }))
          } else if (trimmed.startsWith('# ')) {
            children.push(new Paragraph({ text: trimmed.replace('# ', ''), heading: HeadingLevel.HEADING_1, spacing: { before: 300 } }))
          } else if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
            children.push(new Paragraph({ children: [new TextRun({ text: trimmed.replace(/^[-*]\s*/, '') })], bullet: { level: 0 } }))
          } else {
            children.push(new Paragraph({ children: [new TextRun({ text: trimmed.replace(/\*\*/g, '') })] }))
          }
        }
        if (papers?.length > 0) {
          children.push(new Paragraph({ text: 'References', heading: HeadingLevel.HEADING_2, spacing: { before: 400 } }))
          papers.forEach((p: any, i: number) => {
            children.push(new Paragraph({
              children: [new TextRun({ text: `[${i + 1}] ${p.authors?.join(', ') || ''}. (${p.year || ''}). ${p.title}.` })],
              spacing: { before: 100 },
            }))
          })
        }
        const doc = new Document({ sections: [{ children }] })
        const blob = await Packer.toBlob(doc)
        const { saveAs } = await import('file-saver')
        saveAs(blob, `${safeName}.docx`)
      }
      setExportModalReview(null)
    } catch (err) {
      console.error('Export review failed:', err)
    } finally {
      setExportingReview(false)
    }
  }

  const handleViewRecord = (record: ReviewRecord) => {
    if (record.status === 'processing' || record.status === 'failed') {
      // Processing or failed tasks, guide to regenerate
      sessionStorage.setItem('pending_topic', record.topic)
      navigate('/')
      return
    }
    // 优先使用 record_id，因为所有记录都有 id，而 task_id 可能为 null
    if (record.id) {
      navigate(`/review?record_id=${record.id}`)
    } else if (record.task_id) {
      navigate(`/review?task_id=${record.task_id}`)
    }
  }

  const handleExportRecord = (id: number, event: React.MouseEvent) => {
    event.stopPropagation()
    const record = records.find(r => r.id === id)
    if (!record) return
    setExportModalReview({ id: record.id, topic: record.topic })
  }

  const handleConfirmUseCredit = async () => {
    if (confirmRecordId === null) return
    const record = records.find(r => r.id === confirmRecordId)
    if (!record) return

    setShowCreditConfirmModal(false)

    try {
      const result = await api.unlockRecordWithCredit(confirmRecordId)
      if (result.success) {
        await loadAllRecords()
        const creditsData = await api.getCredits()
        setCredits(creditsData.credits)
        setExportModalReview({ id: record.id, topic: record.topic })
      } else {
        alert(result.message || 'Unlock failed, please try again later')
      }
    } catch (err) {
      console.error('Unlock failed:', err)
      alert('Unlock failed, please try again later')
    } finally {
      setConfirmRecordId(null)
    }
  }

  const handleLogout = () => {
    localStorage.removeItem('auth_token')
    localStorage.removeItem('user_info')
    navigate('/')
  }

  const handleCloseAccount = async () => {
    try {
      const token = localStorage.getItem('auth_token')
      const response = await fetch('/api/account/close', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        }
      })
      const data = await response.json()
      if (data.success) {
        // Logout and redirect
        localStorage.removeItem('auth_token')
        localStorage.removeItem('user_info')
        alert('Your account has been closed successfully.')
        navigate('/')
      } else {
        alert(data.message || 'Failed to close account. Please try again.')
      }
    } catch (err) {
      console.error('Close account error:', err)
      alert('Failed to close account. Please contact scholar@danmo.tech')
    }
  }

  const handleEditProfile = () => {
    setEditNickname(userInfo?.nickname || '')
    setShowEditProfileModal(true)
  }

  const handleSaveProfile = async () => {
    if (!editNickname.trim()) {
      alert('Nickname cannot be empty')
      return
    }
    try {
      const token = localStorage.getItem('auth_token')
      const response = await fetch('/api/user/profile', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ nickname: editNickname.trim() })
      })
      const data = await response.json()
      if (data.success) {
        // Update local storage and state
        const updatedUserInfo = { ...userInfo, nickname: editNickname.trim() }
        localStorage.setItem('user_info', JSON.stringify(updatedUserInfo))
        setUserInfo(updatedUserInfo)
        setShowEditProfileModal(false)
        alert('Profile updated successfully')
      } else {
        alert(data.message || 'Failed to update profile')
      }
    } catch (err) {
      console.error('Update profile error:', err)
      alert('Failed to update profile. Please try again.')
    }
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    const locale = i18n.language === 'zh' ? 'zh-CN' : 'en-US'
    return date.toLocaleString(locale, {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  return (
    <div className="profile-page-international">
      {/* Top Navigation */}
      <nav className="home-nav">
        <div className="nav-logo" onClick={() => navigate('/')} style={{ cursor: 'pointer' }}>
          <span className="logo-icon">📚</span>
          <span className="logo-text">Danmo Scholar</span>
        </div>
        <div className="nav-links">
          <a href="/" className={location.pathname === '/' ? 'active' : ''} onClick={(e) => { e.preventDefault(); navigate('/') }}>Home</a>
          <a href="/search-papers" className={location.pathname === '/search-papers' ? 'active' : ''} onClick={(e) => { e.preventDefault(); navigate('/search-papers') }}>Search Papers</a>
          <a href="/comparison-matrix" className={location.pathname === '/comparison-matrix' ? 'active' : ''} onClick={(e) => { e.preventDefault(); navigate('/comparison-matrix') }}>Comparison Matrix</a>
          <a href="/generate" className={location.pathname === '/generate' ? 'active' : ''} onClick={(e) => { e.preventDefault(); navigate('/generate') }}>Literature Review</a>
          <a href="/#pricing" onClick={(e) => { e.preventDefault(); navigate('/#pricing') }}>Pricing</a>
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
          <button className="sidebar-close" onClick={() => setMobileMenuOpen(false)}>&times;</button>
        </div>
        <nav className="sidebar-links">
          <a href="/" className={location.pathname === '/' ? 'active' : ''} onClick={(e) => { e.preventDefault(); setMobileMenuOpen(false); navigate('/') }}>Home</a>
          <a href="/search-papers" className={location.pathname === '/search-papers' ? 'active' : ''} onClick={(e) => { e.preventDefault(); setMobileMenuOpen(false); navigate('/search-papers') }}>Search Papers</a>
          <a href="/comparison-matrix" className={location.pathname === '/comparison-matrix' ? 'active' : ''} onClick={(e) => { e.preventDefault(); setMobileMenuOpen(false); navigate('/comparison-matrix') }}>Comparison Matrix</a>
          <a href="/generate" className={location.pathname === '/generate' ? 'active' : ''} onClick={(e) => { e.preventDefault(); setMobileMenuOpen(false); navigate('/generate') }}>Literature Review</a>
          <a href="/#pricing" onClick={(e) => { e.preventDefault(); setMobileMenuOpen(false); navigate('/#pricing') }}>Pricing</a>
        </nav>
      </aside>

      <div className="profile-container">
        {/* User Info Section */}
        <div className="profile-header">
          <div className="user-avatar-large">👤</div>
          <div className="user-info-section">
            <h1 className="user-name">{userInfo?.nickname || 'User'}</h1>
            <p className="user-email">{userInfo?.email || ''}</p>
            <div className="user-actions">
              <button className="edit-profile-button" onClick={handleEditProfile}>
                ✏️ Edit Profile
              </button>
              <button className="nav-btn nav-btn-logout" onClick={handleLogout}>
                Logout
              </button>
            </div>
          </div>
        </div>

        {/* Stats */}
        <div className="profile-stats-inline">
          <div className="stat-item">
            <span className="stat-value">{records.length}</span>
            <span className="stat-label">Reviews</span>
          </div>
          <div className="stat-divider" />
          <div className="stat-item">
            <span className="stat-value">{searches.length}</span>
            <span className="stat-label">Searches</span>
          </div>
          <div className="stat-divider" />
          <div className="stat-item">
            <span className="stat-value">{matrices.length}</span>
            <span className="stat-label">Matrices</span>
          </div>
          <div className="stat-divider" />
          <div className="stat-item stat-item-credits">
            <span className="stat-value">{credits}</span>
            <span className="stat-label">Credits</span>
          </div>
        </div>

        {/* Tab Switcher */}
        <div className="profile-tabs">
          <button
            className={`profile-tab ${activeTab === 'searches' ? 'active' : ''}`}
            onClick={() => setActiveTab('searches')}
          >
            🔍 My Searches
          </button>
          <button
            className={`profile-tab ${activeTab === 'matrices' ? 'active' : ''}`}
            onClick={() => setActiveTab('matrices')}
          >
            📊 Comparison Matrices
          </button>
          <button
            className={`profile-tab ${activeTab === 'reviews' ? 'active' : ''}`}
            onClick={() => setActiveTab('reviews')}
          >
            📖 My Reviews
          </button>
        </div>

        {/* History List */}
        <div className="profile-history">
          {activeTab === 'reviews' && (
            <>
              {loading ? (
                <div className="history-loading">
                  <div className="spinner"></div>
                  <p>Loading reviews...</p>
                </div>
              ) : records.length === 0 ? (
                <div className="history-empty">
                  <div className="empty-icon">📝</div>
                  <p className="empty-title">No reviews yet</p>
                  <p className="empty-desc">Enter a research topic and AI will create a structured literature summary</p>
                  <button className="empty-button" onClick={() => navigate('/')}>
                    Create Your First Summary
                  </button>
                </div>
              ) : (
                <div className="records-list">
                  {records.map((record) => (
                    <div
                      key={record.id}
                      className={`record-item ${record.status === 'processing' || record.status === 'failed' ? 'record-item-disabled' : ''}`}
                      onClick={() => handleViewRecord(record)}
                    >
                      <div className="record-main">
                        <div className="record-top">
                          <h3 className="record-topic">{record.topic}</h3>
                          {record.status === 'success' ? (
                            <span className="status-success">✓ Complete</span>
                          ) : record.status === 'failed' ? (
                            <span className="status-failed">✗ Failed</span>
                          ) : (
                            <span className="status-processing">⏳ Processing</span>
                          )}
                        </div>
                        <div className="record-bottom">
                          <div className="record-meta">
                            <span className="record-time">{formatDate(record.created_at)}</span>
                            {record.statistics && (
                              <span className="record-stats-inline">📄 {record.statistics.total || 0} papers</span>
                            )}
                          </div>
                          {record.status === 'success' && (
                            <button
                              className="export-button"
                              onClick={(e) => handleExportRecord(record.id, e)}
                            >
                              Export Summary
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </>
          )}

          {activeTab === 'searches' && (
            <>
              {loading ? (
                <div className="history-loading">
                  <div className="spinner"></div>
                  <p>Loading searches...</p>
                </div>
              ) : searches.length === 0 ? (
                <div className="history-empty">
                  <div className="empty-icon">🔍</div>
                  <p className="empty-title">No searches yet</p>
                  <p className="empty-desc">Search academic papers to find related research</p>
                  <button className="empty-button" onClick={() => navigate('/search-papers')}>
                    Search Papers
                  </button>
                </div>
              ) : (
                <div className="records-list">
                  {searches.map((search) => (
                    <div
                      key={search.id}
                      className="record-item"
                      onClick={() => handleViewSearch(search)}
                    >
                      <div className="record-main">
                        <div className="record-top">
                          <h3 className="record-topic">{search.topic}</h3>
                          <span className="status-success">✓ Complete</span>
                        </div>
                        <div className="record-bottom">
                          <div className="record-meta">
                            <span className="record-time">{formatDate(search.created_at)}</span>
                            {search.papers_count && (
                              <span className="record-stats-inline">📄 {search.papers_count} papers</span>
                            )}
                          </div>
                          <button className="export-button" onClick={(e) => { e.stopPropagation(); setExportModalSearch(search) }}>
                            Export Papers
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </>
          )}

          {activeTab === 'matrices' && (
            <>
              {loading ? (
                <div className="history-loading">
                  <div className="spinner"></div>
                  <p>Loading matrices...</p>
                </div>
              ) : matrices.length === 0 ? (
                <div className="history-empty">
                  <div className="empty-icon">📊</div>
                  <p className="empty-title">No comparison matrices yet</p>
                  <p className="empty-desc">Generate a comparison matrix to compare research perspectives</p>
                  <button className="empty-button" onClick={() => navigate('/comparison-matrix')}>
                    Create Comparison Matrix
                  </button>
                </div>
              ) : (
                <div className="records-list">
                  {matrices.map((matrix, idx) => (
                    <div
                      key={matrix.task_id || `matrix-${idx}`}
                      className="record-item"
                      onClick={() => handleViewMatrix(matrix)}
                    >
                      <div className="record-main">
                        <div className="record-top">
                          <h3 className="record-topic">{matrix.topic}</h3>
                          {matrix.status === 'success' ? (
                            <span className="status-success">✓ Complete</span>
                          ) : matrix.status === 'failed' ? (
                            <span className="status-failed">✗ Failed</span>
                          ) : (
                            <span className="status-processing">⏳ Processing</span>
                          )}
                        </div>
                        <div className="record-bottom">
                          <div className="record-meta">
                            <span className="record-time">{formatDate(matrix.created_at)}</span>
                          </div>
                          <button className="export-button" onClick={(e) => { e.stopPropagation(); setExportModalMatrix(matrix) }}>
                            Export Matrix
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </>
          )}
        </div>
      </div>

      {/* Close Account - bottom of page */}
      <div className="close-account-wrapper">
        <button className="close-account-button" onClick={() => { setShowCloseAccountModal(true); setCloseAccountEmail(''); }}>
          Close Account
        </button>
      </div>

      {/* Footer */}
      <footer className="profile-footer">
        <div className="footer-content">
          <p className="footer-copyright">© 2026 Danmo Scholar. All rights reserved.</p>
          <div className="footer-links">
            <a href="/terms-and-conditions" className="footer-link">Terms & Conditions</a>
            <span className="footer-separator">•</span>
            <a href="/privacy-policy" className="footer-link">Privacy Policy</a>
            <span className="footer-separator">•</span>
            <a href="/refund-policy" className="footer-link">Refund Policy</a>
          </div>
        </div>
      </footer>

      {/* Export Papers Modal */}
      {exportModalSearch && (
        <ExportFormatModal
          selectedFormat={exportFormat}
          onSelectFormat={setExportFormat}
          onConfirm={handleExportSearch}
          onCancel={() => setExportModalSearch(null)}
          loading={exportingSearch}
        />
      )}

      {/* Export Review Modal */}
      {exportModalReview && (
        <div className="confirm-modal-overlay" onClick={() => setExportModalReview(null)}>
          <div className="confirm-modal" onClick={e => e.stopPropagation()}>
            <button className="confirm-modal-close" onClick={() => setExportModalReview(null)}>&times;</button>
            <div className="confirm-modal-header">
              <span className="confirm-modal-icon">📄</span>
              <h2 className="confirm-modal-title">Export Summary</h2>
            </div>
            <div className="confirm-modal-body">
              <div className="export-format-options">
                {([
                  { key: 'markdown' as const, icon: '📝', name: 'Markdown', desc: 'Export as .md file with original format' },
                  { key: 'word' as const, icon: '📄', name: 'Word', desc: 'Export as .docx file for editing' },
                ]).map(fmt => (
                  <label key={fmt.key} className={`export-format-option ${reviewExportFormat === fmt.key ? 'active' : ''}`}>
                    <input type="radio" name="review-export-format" value={fmt.key} checked={reviewExportFormat === fmt.key} onChange={() => setReviewExportFormat(fmt.key)} />
                    <span className="export-format-icon">{fmt.icon}</span>
                    <span className="export-format-info">
                      <span className="export-format-name">{fmt.name}</span>
                      <span className="export-format-desc">{fmt.desc}</span>
                    </span>
                  </label>
                ))}
              </div>
            </div>
            <div className="confirm-modal-footer">
              <button className="confirm-modal-btn confirm-modal-btn-cancel" onClick={() => setExportModalReview(null)} disabled={exportingReview}>Cancel</button>
              <button className="confirm-modal-btn confirm-modal-btn-primary" onClick={doExportReview} disabled={exportingReview}>
                {exportingReview && <span className="confirm-modal-spinner" />}
                {exportingReview ? 'Exporting...' : 'Export'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Export Matrix Modal */}
      {exportModalMatrix && (
        <div className="confirm-modal-overlay" onClick={() => setExportModalMatrix(null)}>
          <div className="confirm-modal" onClick={e => e.stopPropagation()}>
            <button className="confirm-modal-close" onClick={() => setExportModalMatrix(null)}>&times;</button>
            <div className="confirm-modal-header">
              <span className="confirm-modal-icon">📊</span>
              <h2 className="confirm-modal-title">Export Comparison Matrix</h2>
            </div>
            <div className="confirm-modal-body">
              <div className="export-format-options">
                {([
                  { key: 'markdown' as const, icon: '📝', name: 'Markdown', desc: 'Export as .md file with table format' },
                  { key: 'word' as const, icon: '📄', name: 'Word', desc: 'Export as .docx file for editing' },
                ]).map(fmt => (
                  <label key={fmt.key} className={`export-format-option ${matrixExportFormat === fmt.key ? 'active' : ''}`}>
                    <input type="radio" name="matrix-export-format" value={fmt.key} checked={matrixExportFormat === fmt.key} onChange={() => setMatrixExportFormat(fmt.key)} />
                    <span className="export-format-icon">{fmt.icon}</span>
                    <span className="export-format-info">
                      <span className="export-format-name">{fmt.name}</span>
                      <span className="export-format-desc">{fmt.desc}</span>
                    </span>
                  </label>
                ))}
              </div>
            </div>
            <div className="confirm-modal-footer">
              <button className="confirm-modal-btn confirm-modal-btn-cancel" onClick={() => setExportModalMatrix(null)} disabled={exportingMatrix}>Cancel</button>
              <button className="confirm-modal-btn confirm-modal-btn-primary" onClick={handleExportMatrix} disabled={exportingMatrix}>
                {exportingMatrix && <span className="confirm-modal-spinner" />}
                {exportingMatrix ? 'Exporting...' : 'Export'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Payment Modal */}
      {showPayModal && unlockMode && pendingExportRecordId !== null && (
        <PayPalPaymentModal
          onClose={() => {
            setShowPayModal(false)
            setUnlockMode(false)
            setPendingExportRecordId(null)
          }}
          onPaymentSuccess={async () => {
            setShowPayModal(false)
            setUnlockMode(false)
            // Refresh records
            await loadAllRecords()
            // Continue export
            if (pendingExportRecordId !== null) {
              handleExportRecord(pendingExportRecordId, { stopPropagation: () => {} } as React.MouseEvent)
              setPendingExportRecordId(null)
            }
          }}
          planType="unlock"
          recordId={pendingExportRecordId}
        />
      )}
      {showPayModal && !unlockMode && (
        <PayPalPaymentModal
          onClose={() => {
            setShowPayModal(false)
            setPendingExportRecordId(null)
          }}
          onPaymentSuccess={async () => {
            setShowPayModal(false)
            // Refresh user status and records
            const creditsData = await api.getCredits()
            setCredits(creditsData.credits)
            await loadAllRecords()
            // If has pending export, continue
            if (pendingExportRecordId !== null) {
              handleExportRecord(pendingExportRecordId, { stopPropagation: () => {} } as React.MouseEvent)
              setPendingExportRecordId(null)
            }
          }}
          planType="single"
        />
      )}

      {/* Credit Confirmation Modal */}
      {showCreditConfirmModal && confirmRecordId !== null && (
        <ConfirmModalInternational
          message={`You have ${credits} paid credits.\nUse 1 credit to unlock this review and export Word?`}
          confirmText="Unlock with Credit"
          cancelText="Cancel"
          onConfirm={handleConfirmUseCredit}
          onCancel={() => {
            setShowCreditConfirmModal(false)
            setConfirmRecordId(null)
          }}
          type="warning"
        />
      )}

      {/* Close Account Confirmation Modal */}
      {showCloseAccountModal && (
        <div className="modal-overlay" onClick={() => setShowCloseAccountModal(false)}>
          <div className="close-account-modal" onClick={e => e.stopPropagation()}>
            <div className="close-account-header">
              <h2>Close Account</h2>
              <button className="modal-close-btn" onClick={() => setShowCloseAccountModal(false)}>×</button>
            </div>
            <div className="close-account-body">
              <p className="close-account-warning">⚠️ These actions are irreversible. Please be careful.</p>
              <ul className="close-account-consequences">
                <li>You will lose access to all your reviews</li>
                <li>Your credits will be forfeited</li>
                <li>Your data will be deleted within 30 days</li>
              </ul>
              <label className="close-account-label">
                Type your email <strong>{userInfo?.email}</strong> to confirm:
              </label>
              <input
                type="email"
                className="close-account-input"
                value={closeAccountEmail}
                onChange={e => setCloseAccountEmail(e.target.value)}
                placeholder="Enter your email"
                autoFocus
              />
            </div>
            <div className="close-account-footer">
              <button
                className="close-account-btn close-account-btn-cancel"
                onClick={() => setShowCloseAccountModal(false)}
              >
                Cancel
              </button>
              <button
                className="close-account-btn close-account-btn-confirm"
                onClick={handleCloseAccount}
                disabled={closeAccountEmail !== userInfo?.email}
              >
                Close Account
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Profile Modal */}
      {showEditProfileModal && (
        <div className="modal-overlay" onClick={() => setShowEditProfileModal(false)}>
          <div className="edit-profile-modal" onClick={e => e.stopPropagation()}>
            <div className="edit-profile-header">
              <h2>Edit Profile</h2>
              <button className="modal-close-btn" onClick={() => setShowEditProfileModal(false)}>
                ×
              </button>
            </div>
            <div className="edit-profile-body">
              <label className="edit-profile-label">Nickname</label>
              <input
                type="text"
                className="edit-profile-input"
                value={editNickname}
                onChange={e => setEditNickname(e.target.value)}
                placeholder="Enter your nickname"
                maxLength={50}
              />
            </div>
            <div className="edit-profile-footer">
              <button
                className="edit-profile-btn edit-profile-btn-cancel"
                onClick={() => setShowEditProfileModal(false)}
              >
                Cancel
              </button>
              <button
                className="edit-profile-btn edit-profile-btn-save"
                onClick={handleSaveProfile}
              >
                Save
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
