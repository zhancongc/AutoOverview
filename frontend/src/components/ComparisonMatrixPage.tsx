/**
 * ComparisonMatrixPage - 文献对比矩阵展示页面
 */
import { useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { api } from '../api'
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

export function ComparisonMatrixPage() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const taskId = searchParams.get('task_id') || ''

  const [matrixData, setMatrixData] = useState<ComparisonMatrixData | null>(null)
  const [loading, setLoading] = useState(false)
  const [loadingMessage, setLoadingMessage] = useState('')
  const [error, setError] = useState('')

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

      // 首先尝试轮询任务状态，直到完成
      let attempts = 0
      const maxAttempts = 120 // 最多轮询10分钟（每5秒一次）

      while (attempts < maxAttempts) {
        attempts++

        try {
          // 先尝试直接获取对比矩阵
          const result = await api.getComparisonMatrix(id)
          if (result.success && result.data) {
            setMatrixData({
              topic: result.data.topic,
              comparison_matrix: result.data.comparison_matrix,
              statistics: result.data.statistics
            })
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

  if (loading) {
    return (
      <div className="comparison-matrix-page">
        <div className="loading-container">
          <div className="spinner"></div>
          <p>{loadingMessage || t('comparison_matrix_page.loading')}</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="comparison-matrix-page">
        <div className="error-container">
          <p>{error}</p>
          <button onClick={() => navigate(-1)} className="back-btn">
            {t('comparison_matrix_page.back')}
          </button>
        </div>
      </div>
    )
  }

  if (!matrixData) {
    return (
      <div className="comparison-matrix-page">
        <div className="error-container">
          <p>{t('comparison_matrix_page.not_found')}</p>
          <button onClick={() => navigate('/search-papers')} className="back-btn">
            {t('comparison_matrix_page.go_search')}
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="comparison-matrix-page">
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
    </div>
  )
}
