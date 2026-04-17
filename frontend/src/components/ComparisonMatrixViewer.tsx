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
  const [activeTab, setActiveTab] = useState<TabType>('matrix')
  const [isGeneratingReview, setIsGeneratingReview] = useState(false)
  const [showPaymentModal, setShowPaymentModal] = useState<string | false>(false)
  const [showCreditConfirm, setShowCreditConfirm] = useState(false)

  useEffect(() => {
    loadMatrixData(taskId)
  }, [taskId])

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

  const handleGenerateReview = async () => {
    if (!checkLoggedIn()) {
      setShowLoginModal(true)
      return
    }

    // Check credits
    try {
      const creditsData = await api.getCredits()
      setCredits(creditsData.credits)
      if (creditsData.credits < 1) {
        setShowPaymentModal('starter')
        return
      }
    } catch { /* proceed anyway */ }

    // Confirm credit deduction
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
          Comparison Matrix
        </button>
        <button
          className={`segmented-tab ${activeTab === 'references' ? 'active' : ''}`}
          onClick={() => setActiveTab('references')}
        >
          References
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
        <button className="stats-action-btn" onClick={handleExportMarkdown}>
          {t('comparison_matrix_page.export_markdown')}
        </button>
        <button className="stats-action-btn" onClick={() => navigate('/comparison-matrix')}>
          {t('comparison_matrix_page.continue_search')}
        </button>
      </div>
    </div>
  )

  const LoginModalComponent = isChineseSite ? LoginModal : LoginModalInternational

  const creditConfirmMessage = isChineseSite
    ? `您有 ${credits} 个积分。\n生成文献综述将消耗 1 个积分，是否继续？`
    : `You have ${credits} credits.\nGenerate a Literature Summary will use 1 credit. Continue?`
  const creditConfirmBtn = isChineseSite ? '生成' : 'Generate'
  const creditCancelBtn = isChineseSite ? '取消' : 'Cancel'

  const renderModals = () => (
    <>
      {showLoginModal && <LoginModalComponent onClose={() => setShowLoginModal(false)} onLoginSuccess={handleLoginSuccess} />}
      {showCreditConfirm && isChineseSite && (
        <ConfirmModal
          title="确认扣除积分"
          message={creditConfirmMessage}
          confirmText={creditConfirmBtn}
          cancelText={creditCancelBtn}
          onConfirm={() => { setShowCreditConfirm(false); doGenerateReview() }}
          onCancel={() => setShowCreditConfirm(false)}
          type="warning"
        />
      )}
      {showCreditConfirm && !isChineseSite && (
        <ConfirmModalInternational
          message={creditConfirmMessage}
          confirmText={creditConfirmBtn}
          cancelText={creditCancelBtn}
          onConfirm={() => { setShowCreditConfirm(false); doGenerateReview() }}
          onCancel={() => setShowCreditConfirm(false)}
          type="warning"
        />
      )}
      {showPaymentModal && !isChineseSite && (
        <PayPalPaymentModal
          onClose={() => setShowPaymentModal(false)}
          onPaymentSuccess={handlePaymentSuccess}
          planType={showPaymentModal}
        />
      )}
    </>
  )

  // ========== Loading ==========
  if (matrixLoading) {
    return (
      <div className="comparison-matrix-page">
        {renderCompactHeader()}
        <div className="loading-container" style={{ marginTop: 80 }}>
          <div className="progress-bar-container">
            <div className="progress-bar" style={{ width: `${progress}%` }}></div>
          </div>
          <p>{matrixLoadingMsg || t('comparison_matrix_page.loading')}</p>
        </div>
        {renderModals()}
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
            <p className="matrix-topic" style={{ fontSize: '1.05rem', color: '#1f2937', fontWeight: 600, margin: '0 0 0.75rem', lineHeight: 1.4 }}>
              {matrixData.topic}
            </p>
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
      </div>
    )
  }

  return null
}
