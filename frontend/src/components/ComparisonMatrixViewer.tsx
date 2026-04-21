/**
 * ComparisonMatrixViewer - 对比矩阵详情页
 * URL: /comparison-matrix?task_id=xxx
 * 紧凑导航栏 + 矩阵展示，参考 ReviewPage 风格
 */
import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { api } from '../api'
import { isLoggedIn as checkLoggedIn } from '../authApi'
import { LoginModal } from './LoginModal'
import { LoginModalInternational } from './LoginModalInternational'
import { PayPalPaymentModal } from './PayPalPaymentModal'
import { ConfirmModalInternational } from './ConfirmModalInternational'
import { ConfirmModal } from './ConfirmModal'
import { useMatrixAuth, ComparisonMatrixData, TabType } from './ComparisonMatrixShared'
import { ExportFormatModal, ExportFormat } from './ExportFormatModal'
import './ComparisonMatrixPage.css'

export function ComparisonMatrixViewer({ taskId }: { taskId: string }) {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const { isChineseSite, showLoginModal, setShowLoginModal, handleLoginSuccess, credits, setCredits } = useMatrixAuth()

  const [matrixData, setMatrixData] = useState<ComparisonMatrixData | null>(null)
  const [matrixLoading, setMatrixLoading] = useState(true)
  const [matrixLoadingMsg, setMatrixLoadingMsg] = useState('')
  const [matrixError, setMatrixError] = useState('')
  const [progress, setProgress] = useState(0)
  const [matrixSearchTaskId, setMatrixSearchTaskId] = useState('')
  const [pendingPapers, setPendingPapers] = useState<any[]>([])
  const [activeTab, setActiveTab] = useState<TabType>('matrix')
  const [isGeneratingReview, setIsGeneratingReview] = useState(false)
  const [showPaymentModal, setShowPaymentModal] = useState<string | false>(false)
  const [showCreditConfirm, setShowCreditConfirm] = useState(false)
  const [showExportModal, setShowExportModal] = useState(false)
  const [exportFormat, setExportFormat] = useState<ExportFormat>('bibtex')
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [exportingRef, setExportingRef] = useState(false)
  const [showMatrixExportModal, setShowMatrixExportModal] = useState(false)
  const [matrixExportFormat, setMatrixExportFormat] = useState<'markdown' | 'word'>('markdown')
  const [exportingMatrix, setExportingMatrix] = useState(false)
  const [shareCopied, setShareCopied] = useState(false)

  useEffect(() => {
    loadMatrixData(taskId)
  }, [taskId])

  // When pendingPapers is empty but we have the search task ID, fetch papers from the search task
  useEffect(() => {
    if (pendingPapers.length > 0 || !matrixSearchTaskId || !matrixLoading) return
    let cancelled = false
    api.getTaskStatus(matrixSearchTaskId).then(res => {
      if (cancelled) return
      if (!res.success || !res.data) return
      const d = res.data as any
      const papers = d.progress?.papers || d.result?.papers || d.params?.papers || []
      if (papers.length) setPendingPapers(papers)
    }).catch(() => {})
    return () => { cancelled = true }
  }, [matrixSearchTaskId, matrixLoading, pendingPapers.length])

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

            if (taskData.params?.reuse_task_id) {
              setMatrixSearchTaskId(taskData.params.reuse_task_id)
            }

            if (task.status === 'completed') {
              if (task.result) {
                setMatrixData({
                  topic: task.result.topic || task.topic,
                  comparison_matrix: task.result.comparison_matrix,
                  statistics: task.result.statistics,
                  papers: task.result.papers || taskData.params?.papers || []
                })
                setProgress(100)
                setMatrixLoading(false)
                return
              }

              const params = (taskData as any).params || {}
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
            if (task.progress?.papers && task.progress.papers.length > 0) {
              setPendingPapers(task.progress.papers)
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

  const handleShare = async () => {
    if (!taskId) return
    try {
      await api.shareSearchResult(taskId)
      const url = `${window.location.origin}/comparison-matrix?task_id=${taskId}`
      await navigator.clipboard.writeText(url)
      setShareCopied(true)
      setTimeout(() => setShareCopied(false), 2000)
    } catch (err) {
      console.error('Share failed:', err)
    }
  }

  const handleGenerateReview = async () => {
    if (!checkLoggedIn()) {
      setShowLoginModal(true)
      return
    }

    // Check credits first
    try {
      const creditsData = await api.getCredits()
      setCredits(creditsData.credits)
    } catch { /* proceed */ }
    setShowCreditConfirm(true)
  }

  const doGenerateReview = async () => {
    if (!matrixSearchTaskId || !matrixData?.topic) return

    // Check concurrent tasks
    try {
      const activeTask = await api.getActiveTask()
      if (activeTask.active) {
        alert(t('comparison_matrix_page.active_task'))
        return
      }
    } catch { /* don't block */ }

    setIsGeneratingReview(true)
    try {
      const response = await api.submitReviewTask(matrixData.topic, {
        language: isChineseSite ? 'zh' : 'en',
        reuseTaskId: matrixSearchTaskId,
      })
      if (response.success && response.data?.task_id) {
        navigate(`/generate?task_id=${response.data.task_id}`)
      } else {
        const msg = response.message || ''
        if (msg.includes('credits') || msg.includes('积分')) {
          setShowPaymentModal('starter')
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

  const handlePaymentSuccess = async () => {
    setShowPaymentModal(false)
    api.getCredits().then(data => setCredits(data.credits)).catch(() => {})
  }

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

  const handleMatrixExport = async () => {
    if (!matrixData) return
    setExportingMatrix(true)
    try {
      const safeName = (matrixData.topic || 'comparison-matrix').replace(/[\/\\:]/g, '-').substring(0, 50)
      if (matrixExportFormat === 'markdown') {
        handleExportMarkdown()
      } else {
        const { Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType, Table, TableRow, TableCell, WidthType } = await import('docx')
        const lines = matrixData.comparison_matrix.split('\n')
        const children: any[] = []
        children.push(new Paragraph({ text: matrixData.topic, heading: HeadingLevel.TITLE, alignment: AlignmentType.CENTER, spacing: { after: 400 } }))

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
            const cells = trimmed.split('|').filter((c: string) => c.trim()).map((c: string) => c.trim())
            if (cells.every((c: string) => /^[-:\s]+$/.test(c))) continue
            children.push(new Table({
              rows: [new TableRow({
                children: cells.map((cell: string) => new TableCell({
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
      setShowMatrixExportModal(false)
    } catch (err) {
      console.error('Matrix export failed:', err)
    } finally {
      setExportingMatrix(false)
    }
  }

  const getPapersForExport = () => {
    return matrixData?.papers || pendingPapers || []
  }

  const generateBibTeX = (papers: any[]): string => {
    return papers.map((paper, i) => {
      const key = (paper.authors?.[0]?.split(' ').pop()?.toLowerCase() || 'unknown')
        + (paper.year || '') + '_' + (i + 1)
      const authors = paper.authors?.join(' and ') || 'Unknown'
      let entry = `@article{${key},\n`
      entry += `  title = {${paper.title}},\n`
      entry += `  author = {${authors}},\n`
      if (paper.year) entry += `  year = {${paper.year}},\n`
      if (paper.doi) entry += `  doi = {${paper.doi}},\n`
      if (paper.journal) entry += `  journal = {${paper.journal}},\n`
      entry += `}`
      return entry
    }).join('\n\n')
  }

  const generateRIS = (papers: any[]): string => {
    return papers.map(paper => {
      let ris = `TY  - JOUR\n`
      ris += `TI  - ${paper.title}\n`
      if (paper.authors) {
        paper.authors.forEach((a: string) => { ris += `AU  - ${a}\n` })
      }
      if (paper.year) ris += `PY  - ${paper.year}\n`
      if (paper.doi) ris += `DO  - ${paper.doi}\n`
      if (paper.journal) ris += `JO  - ${paper.journal}\n`
      ris += `ER  - \n`
      return ris
    }).join('\n')
  }

  const handleExportReferences = async () => {
    const papers = getPapersForExport()
    if (papers.length === 0) return

    setExportingRef(true)
    try {
      const safeName = (matrixData?.topic || 'references').replace(/[\/\\:]/g, '-').substring(0, 50)
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
        const { Document, Packer, Paragraph, TextRun } = await import('docx')
        const children: any[] = [
          new Paragraph({ text: matrixData?.topic || 'References', heading: 'Heading1' as any }),
          new Paragraph({ text: '' }),
        ]
        papers.forEach((paper: any, i: number) => {
          const authors = paper.authors?.slice(0, 3).join(', ') + (paper.authors?.length > 3 ? ' et al.' : '')
          children.push(new Paragraph({
            children: [
              new TextRun({ text: `[${i + 1}] `, bold: true }),
              new TextRun({ text: `${paper.title}. ${authors}. ${paper.year || ''} ${paper.doi ? `DOI: ${paper.doi}` : ''}` }),
            ],
            spacing: { after: 200 },
          }))
        })
        const doc = new Document({ sections: [{ children }] })
        const blob = await Packer.toBlob(doc)
        saveAs(blob, `${safeName}.docx`)
      }
    } finally {
      setExportingRef(false)
      setShowExportModal(false)
    }
  }

  const renderCompactHeader = () => (
    <div className="review-page-header" style={{ position: 'fixed', top: 0, left: 0, right: 0, zIndex: 100, background: '#fff', borderBottom: '1px solid #e5e7eb' }}>
      <button className="back-button" onClick={() => navigate('/comparison-matrix', { replace: true })}>
        ←
      </button>
      <div className="review-segmented-tabs">
        <button
          className={`segmented-tab ${activeTab === 'matrix' ? 'active' : ''}`}
          onClick={() => setActiveTab('matrix')}
        >
          {isChineseSite ? '对比矩阵' : 'Comparison Matrix'}
        </button>
        <button
          className={`segmented-tab ${activeTab === 'references' ? 'active' : ''}`}
          onClick={() => setActiveTab('references')}
        >
          {isChineseSite ? '参考文献' : 'References'}
        </button>
      </div>
      <div className="header-actions">
        <button
          className="stats-action-btn stats-action-btn-primary"
          onClick={handleGenerateReview}
          disabled={!matrixSearchTaskId || isGeneratingReview}
          title={!matrixSearchTaskId ? t('comparison_matrix_page.generate_review_disabled_hint') : undefined}
        >
          {isGeneratingReview ? t('comparison_matrix_page.generating') : t('comparison_matrix_page.generate_review')}
        </button>
        <button className="stats-action-btn" onClick={() => setShowMatrixExportModal(true)}>
          {isChineseSite ? '导出矩阵' : 'Export'}
        </button>
        <button className="stats-action-btn" onClick={handleShare}>
          {shareCopied ? (isChineseSite ? '已复制' : 'Copied') : (isChineseSite ? '分享' : 'Share')}
        </button>
      </div>
      <button
        className="mobile-menu-toggle review-mobile-toggle"
        onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
        style={{
          display: 'flex',
          minWidth: '44px',
          height: '44px',
          fontSize: '1.5rem',
          color: '#1A1A1A',
          background: 'transparent',
          border: 'none',
          cursor: 'pointer',
          borderRadius: '8px',
          padding: '0.5rem',
          flexShrink: 0,
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 2000
        }}
      >
        ☰
      </button>
    </div>
  )

  const LoginModalComponent = isChineseSite ? LoginModal : LoginModalInternational

  const renderModals = () => (
    <>
      {showLoginModal && <LoginModalComponent onClose={() => setShowLoginModal(false)} onLoginSuccess={handleLoginSuccess} />}
      {showCreditConfirm && (() => {
        const hasCredits = credits >= 1
        const msg = isChineseSite
          ? hasCredits
            ? `您有 ${credits} 个积分。\n生成文献综述将消耗 1 个积分，是否继续？`
            : `您有 ${credits} 个积分，不足以生成文献综述（需 1 个积分）。`
          : hasCredits
            ? `You have ${credits} credits.\nGenerate a Literature Summary will use 1 credit. Continue?`
            : `You have ${credits} credits, which is not enough to generate a review (1 credit required).`
        return (
          <ConfirmModalInternational
            message={msg}
            confirmText={hasCredits ? (isChineseSite ? '生成' : 'Generate') : (isChineseSite ? '去购买积分' : 'Buy Credits')}
            cancelText={isChineseSite ? '取消' : 'Cancel'}
            onConfirm={() => {
              setShowCreditConfirm(false)
              if (hasCredits) doGenerateReview()
              else navigate('/')
            }}
            onCancel={() => setShowCreditConfirm(false)}
            type={hasCredits ? 'warning' : 'danger'}
          />
        )
      })()}
      {showPaymentModal && !isChineseSite && (
        <PayPalPaymentModal
          onClose={() => setShowPaymentModal(false)}
          onPaymentSuccess={handlePaymentSuccess}
          planType={showPaymentModal}
        />
      )}
      {showExportModal && (
        <ExportFormatModal
          selectedFormat={exportFormat}
          onSelectFormat={setExportFormat}
          onConfirm={handleExportReferences}
          onCancel={() => setShowExportModal(false)}
          loading={exportingRef}
        />
      )}
      {showMatrixExportModal && (
        <div className="confirm-modal-overlay" onClick={() => setShowMatrixExportModal(false)}>
          <div className="confirm-modal" onClick={e => e.stopPropagation()}>
            <button className="confirm-modal-close" onClick={() => setShowMatrixExportModal(false)}>&times;</button>
            <div className="confirm-modal-header">
              <span className="confirm-modal-icon">📊</span>
              <h2 className="confirm-modal-title">{isChineseSite ? '导出对比矩阵' : 'Export Comparison Matrix'}</h2>
            </div>
            <div className="confirm-modal-body">
              <div className="export-format-options">
                {([
                  { key: 'markdown' as const, icon: '📝', name: 'Markdown', desc: isChineseSite ? '导出为 .md 文件，保留表格格式' : 'Export as .md file with table format' },
                  { key: 'word' as const, icon: '📄', name: 'Word', desc: isChineseSite ? '导出为 .docx 文件，方便编辑分享' : 'Export as .docx file for editing' },
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
              <button className="confirm-modal-btn confirm-modal-btn-cancel" onClick={() => setShowMatrixExportModal(false)} disabled={exportingMatrix}>{isChineseSite ? '取消' : 'Cancel'}</button>
              <button className="confirm-modal-btn confirm-modal-btn-primary" onClick={handleMatrixExport} disabled={exportingMatrix}>
                {exportingMatrix && <span className="confirm-modal-spinner" />}
                {exportingMatrix ? (isChineseSite ? '导出中...' : 'Exporting...') : (isChineseSite ? '确认导出' : 'Export')}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )

  // ========== Loading ==========
  if (matrixLoading) {
    return (
      <div className="comparison-matrix-page">
        {renderCompactHeader()}
        <div style={{ marginTop: 80, padding: '0 2rem', maxWidth: 900, margin: '80px auto 0' }}>
          {activeTab === 'matrix' ? (
            <div className="loading-container">
              <div className="progress-bar-container">
                <div className="progress-bar" style={{ width: `${progress}%` }}></div>
              </div>
              <p style={{ color: '#6b7280', marginTop: '1rem' }}>{matrixLoadingMsg || t('comparison_matrix_page.loading')}</p>
            </div>
          ) : (
            <div className="matrix-references">
              {pendingPapers.length > 0 ? (
                <>
                  <h2>References</h2>
                  <p className="references-summary">{pendingPapers.length} papers found</p>
                  <div className="references-list">
                    {pendingPapers.map((paper: any, index: number) => (
                      <div key={paper.id || index} className="reference-item">
                        <div className="reference-number">{index + 1}</div>
                        <div className="reference-content">
                          <div className="reference-title">{paper.title}</div>
                          <div className="reference-meta">
                            {paper.authors?.slice(0, 3).join(', ')}{paper.authors?.length > 3 ? ' et al.' : ''}
                            {paper.year && ` · ${paper.year}`}
                            {paper.cited_by_count >= 0 && ` · ${paper.cited_by_count} citations`}
                          </div>
                          {paper.doi && (
                            <a href={`https://doi.org/${paper.doi}`} target="_blank" rel="noopener noreferrer" className="reference-doi">
                              DOI: {paper.doi}
                            </a>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </>
              ) : (
                <div className="loading-container">
                  <div className="progress-bar-container">
                    <div className="progress-bar" style={{ width: `${progress}%` }}></div>
                  </div>
                  <p style={{ color: '#6b7280', marginTop: '1rem' }}>{matrixLoadingMsg || t('comparison_matrix_page.loading')}</p>
                </div>
              )}
            </div>
          )}
        </div>
        {renderModals()}

        {/* 移动端侧边栏遮罩 */}
        {mobileMenuOpen && (
          <div className="mobile-sidebar-overlay" onClick={() => setMobileMenuOpen(false)} />
        )}

        {/* 移动端侧边栏 */}
        <aside className={`mobile-sidebar ${mobileMenuOpen ? 'sidebar-open' : ''}`}>
          <div className="sidebar-header">
            <span className="sidebar-header-title">{isChineseSite ? '操作' : 'Actions'}</span>
            <button className="sidebar-close" onClick={() => setMobileMenuOpen(false)}>&times;</button>
          </div>
          <div className="sidebar-actions">
            <button
              className="sidebar-action-btn sidebar-action-primary"
              onClick={() => {
                setMobileMenuOpen(false)
                handleGenerateReview()
              }}
              disabled={!matrixSearchTaskId || isGeneratingReview}
            >
              {isGeneratingReview
                ? (isChineseSite ? '生成中...' : 'Generating...')
                : t('comparison_matrix_page.generate_review')}
            </button>
            <button
              className="sidebar-action-btn sidebar-action-secondary"
              onClick={() => {
                setMobileMenuOpen(false)
                setShowMatrixExportModal(true)
              }}
            >
              {isChineseSite ? '导出矩阵' : 'Export'}
            </button>
            <button
              className="sidebar-action-btn sidebar-action-secondary"
              onClick={() => {
                setMobileMenuOpen(false)
                setShowExportModal(true)
              }}
              disabled={getPapersForExport().length === 0}
            >
              {t('comparison_matrix_page.export_references')}
            </button>
          </div>
          <div className="sidebar-bottom">
            <button
              className="sidebar-user-btn"
              onClick={() => {
                setMobileMenuOpen(false)
                navigate('/profile')
              }}
            >
              <span>👤</span>
              <span>{isChineseSite ? '我的账户' : 'My Account'}</span>
            </button>
          </div>
        </aside>
      </div>
    )
  }

  // ========== Error ==========
  if (matrixError) {
    return (
      <div className="comparison-matrix-page">
        {renderCompactHeader()}
        <div className="error-container" style={{ marginTop: 80 }}>
          <p>{matrixError}</p>
          <button onClick={() => navigate('/comparison-matrix', { replace: true })} className="back-btn">
            {t('comparison_matrix_page.go_search')}
          </button>
        </div>
        {renderModals()}

        {/* 移动端侧边栏遮罩 */}
        {mobileMenuOpen && (
          <div className="mobile-sidebar-overlay" onClick={() => setMobileMenuOpen(false)} />
        )}

        {/* 移动端侧边栏 */}
        <aside className={`mobile-sidebar ${mobileMenuOpen ? 'sidebar-open' : ''}`}>
          <div className="sidebar-header">
            <span className="sidebar-header-title">{isChineseSite ? '操作' : 'Actions'}</span>
            <button className="sidebar-close" onClick={() => setMobileMenuOpen(false)}>&times;</button>
          </div>
          <div className="sidebar-actions">
            <button
              className="sidebar-action-btn sidebar-action-primary"
              onClick={() => {
                setMobileMenuOpen(false)
                handleGenerateReview()
              }}
              disabled={!matrixSearchTaskId || isGeneratingReview}
            >
              {isGeneratingReview
                ? (isChineseSite ? '生成中...' : 'Generating...')
                : t('comparison_matrix_page.generate_review')}
            </button>
            <button
              className="sidebar-action-btn sidebar-action-secondary"
              onClick={() => {
                setMobileMenuOpen(false)
                setShowMatrixExportModal(true)
              }}
            >
              {isChineseSite ? '导出矩阵' : 'Export'}
            </button>
            <button
              className="sidebar-action-btn sidebar-action-secondary"
              onClick={() => {
                setMobileMenuOpen(false)
                setShowExportModal(true)
              }}
              disabled={getPapersForExport().length === 0}
            >
              {t('comparison_matrix_page.export_references')}
            </button>
          </div>
          <div className="sidebar-bottom">
            <button
              className="sidebar-user-btn"
              onClick={() => {
                setMobileMenuOpen(false)
                navigate('/profile')
              }}
            >
              <span>👤</span>
              <span>{isChineseSite ? '我的账户' : 'My Account'}</span>
            </button>
          </div>
        </aside>
      </div>
    )
  }

  // ========== Matrix display ==========
  if (matrixData) {
    return (
      <div className="comparison-matrix-page">
        {renderCompactHeader()}

        <div className="matrix-container" style={{ marginTop: 60 }}>
          <div className="matrix-stats">
            <div className="matrix-stats-header">
              <p className="matrix-topic" style={{ fontSize: '1.05rem', color: '#1f2937', fontWeight: 600, margin: 0, lineHeight: 1.4 }}>
                {matrixData.topic}
              </p>
              <button className="stats-action-btn" onClick={() => setShowExportModal(true)} disabled={getPapersForExport().length === 0}>
                {t('comparison_matrix_page.export_references')}
              </button>
            </div>
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

        {renderModals()}

        {/* 移动端侧边栏遮罩 */}
        {mobileMenuOpen && (
          <div className="mobile-sidebar-overlay" onClick={() => setMobileMenuOpen(false)} />
        )}

        {/* 移动端侧边栏 */}
        <aside className={`mobile-sidebar ${mobileMenuOpen ? 'sidebar-open' : ''}`}>
          <div className="sidebar-header">
            <span className="sidebar-header-title">{isChineseSite ? '操作' : 'Actions'}</span>
            <button className="sidebar-close" onClick={() => setMobileMenuOpen(false)}>&times;</button>
          </div>
          <div className="sidebar-actions">
            <button
              className="sidebar-action-btn sidebar-action-primary"
              onClick={() => {
                setMobileMenuOpen(false)
                handleGenerateReview()
              }}
              disabled={!matrixSearchTaskId || isGeneratingReview}
            >
              {isGeneratingReview
                ? (isChineseSite ? '生成中...' : 'Generating...')
                : t('comparison_matrix_page.generate_review')}
            </button>
            <button
              className="sidebar-action-btn sidebar-action-secondary"
              onClick={() => {
                setMobileMenuOpen(false)
                setShowMatrixExportModal(true)
              }}
            >
              {isChineseSite ? '导出矩阵' : 'Export'}
            </button>
            <button
              className="sidebar-action-btn sidebar-action-secondary"
              onClick={() => {
                setMobileMenuOpen(false)
                setShowExportModal(true)
              }}
              disabled={getPapersForExport().length === 0}
            >
              {t('comparison_matrix_page.export_references')}
            </button>
          </div>
          <div className="sidebar-bottom">
            <button
              className="sidebar-user-btn"
              onClick={() => {
                setMobileMenuOpen(false)
                navigate('/profile')
              }}
            >
              <span>👤</span>
              <span>{isChineseSite ? '我的账户' : 'My Account'}</span>
            </button>
          </div>
        </aside>
      </div>
    )
  }

  return null
}
