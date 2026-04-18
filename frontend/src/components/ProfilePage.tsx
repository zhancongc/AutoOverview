import { useState, useEffect } from 'react'
import { useNavigate, useSearchParams, useLocation } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { api } from '../api'
import { getLocalUserInfo, isLoggedIn } from '../authApi'
import { PaymentModal } from './PaymentModal'
import { ConfirmModal } from './ConfirmModal'
import { ExportFormatModal, type ExportFormat } from './ExportFormatModal'
import type { ReviewRecord } from '../types'
import './SimpleApp.css'
import './ProfilePage.css'

type ProfileTab = 'reviews' | 'searches' | 'matrices'

export function ProfilePage() {
  const { i18n } = useTranslation()
  const navigate = useNavigate()
  const location = useLocation()
  const [searchParams] = useSearchParams()
  const tabParam = searchParams.get('tab') as ProfileTab | null
  const [activeTab, setActiveTab] = useState<ProfileTab>(
    tabParam && ['searches', 'matrices', 'reviews'].includes(tabParam) ? tabParam : 'searches'
  )
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  const [records, setRecords] = useState<ReviewRecord[]>([])
  const [searches, setSearches] = useState<any[]>([])
  const [matrices, setMatrices] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [userInfo, setUserInfo] = useState<any>(null)
  const [credits, setCredits] = useState<number>(0)
  const [showPayModal, setShowPayModal] = useState(false)
  const [pendingExportRecordId, setPendingExportRecordId] = useState<number | null>(null)
  const [unlockMode, setUnlockMode] = useState(false)  // true=单次解锁, false=购买套餐
  const [showCreditConfirmModal, setShowCreditConfirmModal] = useState(false)
  const [confirmRecordId, setConfirmRecordId] = useState<number | null>(null)
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
    }).catch(err => console.error('获取积分失败:', err))
  }, [])

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
      console.error('加载历史记录失败:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleViewSearch = (search: any) => {
    // 将搜索结果保存到 localStorage，然后跳转到搜索页面
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

  // 文献导出相关
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
        children.push(new Paragraph({ children: [new TextRun({ text: `共 ${papers.length} 篇文献`, bold: true })], alignment: AlignmentType.CENTER, spacing: { after: 400 } }))
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

  // 矩阵导出
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
            // table row
            const cells = trimmed.split('|').filter(c => c.trim()).map(c => c.trim())
            if (cells.every(c => /^[-:\s]+$/.test(c))) continue // skip separator
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

  const handleViewRecord = (record: ReviewRecord) => {
    if (record.status === 'processing' || record.status === 'failed') {
      // 生成中或失败的任务，引导重新生成
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

  const doExportReview = async () => {
    if (!exportModalReview) return
    setExportingReview(true)
    try {
      const res = await api.getRecordReview(exportModalReview.id)
      const { topic, review, papers } = res.data
      const safeName = topic.replace(/[\/\\:]/g, '-').substring(0, 50)

      if (reviewExportFormat === 'markdown') {
        let content = `# ${topic}\n\n${review}\n\n## 参考文献\n\n`
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
        // 添加参考文献
        if (papers?.length > 0) {
          children.push(new Paragraph({ text: '参考文献', heading: HeadingLevel.HEADING_2, spacing: { before: 400 } }))
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
        // 弹出格式选择
        setExportModalReview({ id: record.id, topic: record.topic })
      } else {
        alert(result.message || '解锁失败，请稍后重试')
      }
    } catch (err) {
      console.error('解锁失败:', err)
      alert('解锁失败，请稍后重试')
    } finally {
      setConfirmRecordId(null)
    }
  }

  const handleLogout = () => {
    localStorage.removeItem('auth_token')
    localStorage.removeItem('user_info')
    navigate('/')
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
    <div className="profile-page">
      {/* 顶部导航栏 */}
      <nav className="home-nav">
        <div className="nav-logo" onClick={() => navigate('/')} style={{ cursor: 'pointer' }}>
          <span className="logo-icon">📚</span>
          <span className="logo-text">澹墨学术</span>
        </div>
        <div className="nav-links">
          <a href="/" className={location.pathname === '/' ? 'active' : ''} onClick={(e) => { e.preventDefault(); navigate('/') }}>首页</a>
          <a href="/search-papers" className={location.pathname === '/search-papers' ? 'active' : ''} onClick={(e) => { e.preventDefault(); navigate('/search-papers') }}>搜索文献</a>
          <a href="/comparison-matrix" className={location.pathname === '/comparison-matrix' ? 'active' : ''} onClick={(e) => { e.preventDefault(); navigate('/comparison-matrix') }}>对比矩阵</a>
          <a href="/generate" className={location.pathname === '/generate' ? 'active' : ''} onClick={(e) => { e.preventDefault(); navigate('/generate') }}>生成综述</a>
          <a href="/#pricing" onClick={(e) => { e.preventDefault(); navigate('/#pricing') }}>定价</a>
        </div>
        <div className="nav-actions"></div>
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
          <span className="logo-text">澹墨学术</span>
          <button className="sidebar-close" onClick={() => setMobileMenuOpen(false)}>&times;</button>
        </div>
        <nav className="sidebar-links">
          <a href="/" onClick={(e) => { e.preventDefault(); setMobileMenuOpen(false); navigate('/') }}>首页</a>
          <a href="/search-papers" onClick={(e) => { e.preventDefault(); setMobileMenuOpen(false); navigate('/search-papers') }}>搜索文献</a>
          <a href="/comparison-matrix" onClick={(e) => { e.preventDefault(); setMobileMenuOpen(false); navigate('/comparison-matrix') }}>对比矩阵</a>
          <a href="/generate" onClick={(e) => { e.preventDefault(); setMobileMenuOpen(false); navigate('/generate') }}>生成综述</a>
          <a href="/#pricing" onClick={(e) => { e.preventDefault(); setMobileMenuOpen(false); navigate('/#pricing') }}>定价</a>
        </nav>
      </aside>

      <div className="profile-container">
        {/* 用户信息区域 */}
        <div className="profile-header">
          <div className="user-avatar-large">👤</div>
          <div className="user-info-section">
            <h1 className="user-name">{userInfo?.nickname || '用户'}</h1>
            <p className="user-email">{userInfo?.email || ''}</p>
          </div>
          <button className="nav-btn nav-btn-logout" onClick={handleLogout}>
            退出登录
          </button>
        </div>

        {/* 统计信息 */}
        <div className="profile-stats-inline">
          <div className="stat-item">
            <span className="stat-value">{searches.length}</span>
            <span className="stat-label">查询次数</span>
          </div>
          <div className="stat-divider" />
          <div className="stat-item">
            <span className="stat-value">{matrices.length}</span>
            <span className="stat-label">矩阵数量</span>
          </div>
          <div className="stat-divider" />
          <div className="stat-item">
            <span className="stat-value">{records.length}</span>
            <span className="stat-label">综述数量</span>
          </div>
          <div className="stat-divider" />
          <div className="stat-item stat-item-credits">
            <span className="stat-value">{credits}</span>
            <span className="stat-label">积分</span>
          </div>
        </div>

        {/* Tab 切换 */}
        <div className="profile-tabs">
          <button
            className={`profile-tab ${activeTab === 'searches' ? 'active' : ''}`}
            onClick={() => { setActiveTab('searches'); navigate('/profile?tab=searches', { replace: true }) }}
          >
            🔍 文献查询
          </button>
          <button
            className={`profile-tab ${activeTab === 'matrices' ? 'active' : ''}`}
            onClick={() => { setActiveTab('matrices'); navigate('/profile?tab=matrices', { replace: true }) }}
          >
            📊 对比矩阵
          </button>
          <button
            className={`profile-tab ${activeTab === 'reviews' ? 'active' : ''}`}
            onClick={() => { setActiveTab('reviews'); navigate('/profile?tab=reviews', { replace: true }) }}
          >
            📖 我的综述
          </button>
        </div>

        {/* 历史记录列表 */}
        <div className="profile-history">
          {activeTab === 'reviews' ? (
            <>
              {loading ? (
                <div className="history-loading">
                  <div className="spinner"></div>
                  <p>加载历史记录中...</p>
                </div>
              ) : records.length === 0 ? (
                <div className="history-empty">
                  <div className="empty-icon">📝</div>
                  <p className="empty-title">还没有生成过综述</p>
                  <p className="empty-desc">输入研究主题，AI 为您自动搜索文献并生成专业综述</p>
                  <button className="empty-button" onClick={() => navigate('/')}>
                    去生成第一篇综述
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
                            <span className="status-success">✓ 已完成</span>
                          ) : record.status === 'failed' ? (
                            <span className="status-failed">✗ 失败</span>
                          ) : (
                            <span className="status-processing">⏳ 进行中</span>
                          )}
                        </div>
                        <div className="record-bottom">
                          <div className="record-meta">
                            <span className="record-time">{formatDate(record.created_at)}</span>
                            {record.statistics && (
                              <span className="record-stats-inline">📄 {record.statistics.total || 0} 篇文献</span>
                            )}
                          </div>
                          {record.status === 'success' && (
                            <button
                              className="export-button"
                              onClick={(e) => handleExportRecord(record.id, e)}
                            >
                              导出综述
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </>
          ) : activeTab === 'matrices' ? (
            <>
              {loading ? (
                <div className="history-loading">
                  <div className="spinner"></div>
                  <p>加载对比矩阵中...</p>
                </div>
              ) : matrices.length === 0 ? (
                <div className="history-empty">
                  <div className="empty-icon">📊</div>
                  <p className="empty-title">还没有对比矩阵</p>
                  <p className="empty-desc">选择文献，生成对比矩阵</p>
                  <button className="empty-button" onClick={() => navigate('/comparison-matrix')}>
                    去生成对比矩阵
                  </button>
                </div>
              ) : (
                <div className="records-list">
                  {matrices.map((matrix) => (
                    <div
                      key={matrix.id}
                      className={`record-item ${matrix.status === 'processing' || matrix.status === 'failed' ? 'record-item-disabled' : ''}`}
                      onClick={() => handleViewMatrix(matrix)}
                    >
                      <div className="record-main">
                        <div className="record-top">
                          <h3 className="record-topic">{matrix.topic || '对比矩阵'}</h3>
                          {matrix.status === 'success' ? (
                            <span className="status-success">✓ 已完成</span>
                          ) : matrix.status === 'failed' ? (
                            <span className="status-failed">✗ 失败</span>
                          ) : (
                            <span className="status-processing">⏳ 进行中</span>
                          )}
                        </div>
                        <div className="record-bottom">
                          <div className="record-meta">
                            <span className="record-time">{formatDate(matrix.created_at)}</span>
                            {matrix.papers && (
                              <span className="record-stats-inline">📄 {matrix.papers.length} 篇文献</span>
                            )}
                          </div>
                          {matrix.status === 'success' && (
                            <button className="export-button" onClick={(e) => { e.stopPropagation(); setExportModalMatrix(matrix) }}>
                              导出矩阵
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </>
          ) : (
            <>
              {loading ? (
                <div className="history-loading">
                  <div className="spinner"></div>
                  <p>加载搜索历史中...</p>
                </div>
              ) : searches.length === 0 ? (
                <div className="history-empty">
                  <div className="empty-icon">🔍</div>
                  <p className="empty-title">还没有搜索记录</p>
                  <p className="empty-desc">搜索文献，找到相关研究</p>
                  <button className="empty-button" onClick={() => navigate('/search-papers')}>
                    去搜索文献
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
                          <span className="status-success">✓ 已完成</span>
                        </div>
                        <div className="record-bottom">
                          <div className="record-meta">
                            <span className="record-time">{formatDate(search.created_at)}</span>
                            {search.papers_count && (
                              <span className="record-stats-inline">📄 {search.papers_count} 篇文献</span>
                            )}
                          </div>
                          <button className="export-button" onClick={(e) => { e.stopPropagation(); setExportModalSearch(search) }}>
                            导出文献
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

      {/* 页脚 */}
      <footer className="profile-footer">
        <div className="footer-content">
          <p className="footer-copyright">© 2026 Danmo Scholar. All rights reserved.</p>
          <a href="https://beian.miit.gov.cn/" target="_blank" rel="noopener noreferrer" className="footer-icp">
            沪ICP备2023018158号
          </a>
        </div>
      </footer>

      {/* 文献导出弹窗 */}
      {exportModalSearch && (
        <ExportFormatModal
          selectedFormat={exportFormat}
          onSelectFormat={setExportFormat}
          onConfirm={handleExportSearch}
          onCancel={() => setExportModalSearch(null)}
          loading={exportingSearch}
        />
      )}

      {/* 综述导出弹窗 */}
      {exportModalReview && (
        <div className="confirm-modal-overlay" onClick={() => setExportModalReview(null)}>
          <div className="confirm-modal" onClick={e => e.stopPropagation()}>
            <button className="confirm-modal-close" onClick={() => setExportModalReview(null)}>&times;</button>
            <div className="confirm-modal-header">
              <span className="confirm-modal-icon">📄</span>
              <h2 className="confirm-modal-title">导出综述</h2>
            </div>
            <div className="confirm-modal-body">
              <div className="export-format-options">
                {([
                  { key: 'markdown' as const, icon: '📝', name: 'Markdown', desc: '导出为 .md 文件，保留原始格式' },
                  { key: 'word' as const, icon: '📄', name: 'Word', desc: '导出为 .docx 文件，方便编辑分享' },
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
              <button className="confirm-modal-btn confirm-modal-btn-cancel" onClick={() => setExportModalReview(null)} disabled={exportingReview}>取消</button>
              <button className="confirm-modal-btn confirm-modal-btn-primary" onClick={doExportReview} disabled={exportingReview}>
                {exportingReview && <span className="confirm-modal-spinner" />}
                {exportingReview ? '导出中...' : '确认导出'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 矩阵导出弹窗 */}
      {exportModalMatrix && (
        <div className="confirm-modal-overlay" onClick={() => setExportModalMatrix(null)}>
          <div className="confirm-modal" onClick={e => e.stopPropagation()}>
            <button className="confirm-modal-close" onClick={() => setExportModalMatrix(null)}>&times;</button>
            <div className="confirm-modal-header">
              <span className="confirm-modal-icon">📊</span>
              <h2 className="confirm-modal-title">导出对比矩阵</h2>
            </div>
            <div className="confirm-modal-body">
              <div className="export-format-options">
                {([
                  { key: 'markdown' as const, icon: '📝', name: 'Markdown', desc: '导出为 .md 文件，保留表格格式' },
                  { key: 'word' as const, icon: '📄', name: 'Word', desc: '导出为 .docx 文件，方便编辑分享' },
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
              <button className="confirm-modal-btn confirm-modal-btn-cancel" onClick={() => setExportModalMatrix(null)} disabled={exportingMatrix}>取消</button>
              <button className="confirm-modal-btn confirm-modal-btn-primary" onClick={handleExportMatrix} disabled={exportingMatrix}>
                {exportingMatrix && <span className="confirm-modal-spinner" />}
                {exportingMatrix ? '导出中...' : '确认导出'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 支付弹窗 */}
      {showPayModal && unlockMode && pendingExportRecordId !== null && (
        <PaymentModal
          onClose={() => {
            setShowPayModal(false)
            setUnlockMode(false)
            setPendingExportRecordId(null)
          }}
          onPaymentSuccess={async () => {
            setShowPayModal(false)
            setUnlockMode(false)
            await loadAllRecords()
            if (pendingExportRecordId !== null) {
              const record = records.find(r => r.id === pendingExportRecordId)
              if (record) setExportModalReview({ id: record.id, topic: record.topic })
              setPendingExportRecordId(null)
            }
          }}
          planType="unlock"
          recordId={pendingExportRecordId}
        />
      )}
      {showPayModal && !unlockMode && (
        <PaymentModal
          onClose={() => {
            setShowPayModal(false)
            setPendingExportRecordId(null)
          }}
          onPaymentSuccess={async () => {
            setShowPayModal(false)
            const creditsData = await api.getCredits()
            setCredits(creditsData.credits)
            await loadAllRecords()
            if (pendingExportRecordId !== null) {
              const record = records.find(r => r.id === pendingExportRecordId)
              if (record) setExportModalReview({ id: record.id, topic: record.topic })
              setPendingExportRecordId(null)
            }
          }}
          planType="single"
        />
      )}

      {/* 使用积分确认弹窗 */}
      {showCreditConfirmModal && confirmRecordId !== null && (
        <ConfirmModal
          title="使用积分解锁"
          message={`您有 ${credits} 个积分。\n是否使用 1 个积分解锁此综述并导出 Word？`}
          confirmText="使用积分解锁"
          cancelText="取消"
          onConfirm={handleConfirmUseCredit}
          onCancel={() => {
            setShowCreditConfirmModal(false)
            setConfirmRecordId(null)
          }}
          type="warning"
        />
      )}
    </div>
  )
}
