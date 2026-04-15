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
  const [error, setError] = useState('')

  useEffect(() => {
    if (taskId) {
      loadMatrixData(taskId)
    }
  }, [taskId])

  const loadMatrixData = async (id: string) => {
    try {
      setLoading(true)
      setError('')

      // TODO: 调用后端 API 获取对比矩阵数据
      // const data = await api.getComparisonMatrix(id)
      // setMatrixData(data)

      // 模拟数据
      setTimeout(() => {
        setMatrixData({
          topic: '深度学习在图像识别中的应用',
          comparison_matrix: `## 文献对比矩阵

### 1. 观点对比

#### 观点组 1：深度学习 vs 传统方法
- **支持深度学习**：[1] [2] [3] 认为深度学习在大规模数据集上表现优异，能够自动学习特征
- **支持传统方法**：[4] [5] 认为传统方法在小样本场景下更稳定，可解释性更强

#### 观点组 2：CNN vs Transformer
- **支持 CNN**：[1] [3] 指出 CNN 在局部特征提取方面具有天然优势
- **支持 Transformer**：[6] [7] 认为 Transformer 的自注意力机制能够捕获长距离依赖

### 2. 分歧原因分析

#### 观点组 1 分歧原因
这种分歧可能源于：
- **样本差异**：研究使用的数据集规模差异显著（10万 vs 1千）
- **方法差异**：深度学习方法需要大量标注数据，而传统方法依赖手工特征工程
- **情境差异**：不同研究针对的应用场景不同（工业应用 vs 学术研究）

### 3. 对比表格

| 研究者 | 年份 | 样本 | 核心观点 | 方法 | 可能的分歧原因 |
|---------|------|------|----------|------|----------------|
| Zhang 等 | 2023 | 10万 | 深度学习优于传统方法 | CNN | 样本量差异、应用场景不同 |
| Wang 等 | 2022 | 5万 | Transformer 表现最佳 | ViT | 模型架构差异 |
| Li 等 | 2021 | 1千 | 传统方法更稳定 | SIFT + SVM | 样本量小、对可解释性要求高 |
| Chen 等 | 2020 | 2千 | 两者结合效果最好 | CNN + Transformer | 折中方案 |
`,
          statistics: {
            papers_used: 10,
            total_time_seconds: 8.5,
            generated_at: new Date().toISOString()
          }
        })
        setLoading(false)
      }, 1000)

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
          <p>{t('comparison_matrix_page.loading')}</p>
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

      <style>{`
        .comparison-matrix-page {
          min-height: 100vh;
          background: linear-gradient(135deg, #fef5e7 0%, #fff8e1 100%);
          padding: 40px 20px;
        }

        .matrix-container {
          max-width: 900px;
          margin: 0 auto;
        }

        .matrix-header {
          background: white;
          border-radius: 16px;
          padding: 24px;
          margin-bottom: 20px;
          box-shadow: 0 4px 16px rgba(0,0,0,0.08);
        }

        .header-content {
          display: flex;
          align-items: flex-start;
          gap: 16px;
        }

        .back-button {
          background: #f5f5f5;
          border: none;
          padding: 8px 16px;
          border-radius: 8px;
          cursor: pointer;
          font-size: 0.9rem;
          color: #666;
          transition: all 0.2s;
          flex-shrink: 0;
        }

        .back-button:hover {
          background: #e0e0e0;
          color: #333;
        }

        .header-title {
          flex: 1;
        }

        .header-title h1 {
          margin: 0 0 8px;
          font-size: 1.75rem;
          color: #d35400;
        }

        .matrix-topic {
          margin: 0;
          font-size: 1.1rem;
          color: #666;
        }

        .matrix-stats {
          display: flex;
          gap: 16px;
          background: white;
          border-radius: 12px;
          padding: 16px 24px;
          margin-bottom: 20px;
          box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        }

        .stat-item {
          display: flex;
          flex-direction: column;
          gap: 4px;
        }

        .stat-label {
          font-size: 0.8rem;
          color: #999;
        }

        .stat-value {
          font-size: 1.1rem;
          font-weight: 600;
          color: #333;
        }

        .matrix-content {
          background: white;
          border-radius: 16px;
          padding: 32px;
          margin-bottom: 20px;
          box-shadow: 0 4px 16px rgba(0,0,0,0.08);
        }

        .matrix-content h1 {
          font-size: 1.5rem;
          color: #d35400;
          margin-top: 0;
          margin-bottom: 20px;
          border-bottom: 2px solid #f39c12;
          padding-bottom: 12px;
        }

        .matrix-content h2 {
          font-size: 1.25rem;
          color: #e67e22;
          margin-top: 28px;
          margin-bottom: 16px;
        }

        .matrix-content h3 {
          font-size: 1.1rem;
          color: #d35400;
          margin-top: 20px;
          margin-bottom: 12px;
        }

        .matrix-content p {
          color: #444;
          line-height: 1.8;
          margin-bottom: 12px;
        }

        .matrix-content ul,
        .matrix-content ol {
          color: #444;
          line-height: 1.8;
          margin-bottom: 12px;
          padding-left: 24px;
        }

        .matrix-content li {
          margin-bottom: 8px;
        }

        .table-wrapper {
          overflow-x: auto;
          margin: 20px 0;
        }

        .matrix-content table {
          width: 100%;
          border-collapse: collapse;
          font-size: 0.9rem;
        }

        .matrix-content th,
        .matrix-content td {
          border: 1px solid #ddd;
          padding: 12px;
          text-align: left;
        }

        .matrix-content th {
          background: #fef5e7;
          color: #d35400;
          font-weight: 600;
        }

        .matrix-content tr:nth-child(even) {
          background: #fffdf5;
        }

        .matrix-content tr:hover {
          background: #fff8e1;
        }

        .matrix-actions {
          display: flex;
          gap: 12px;
          justify-content: center;
        }

        .action-btn {
          background: white;
          color: #e67e22;
          border: 2px solid #e67e22;
          padding: 12px 28px;
          border-radius: 10px;
          font-size: 1rem;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s;
        }

        .action-btn:hover {
          background: #fff8e1;
        }

        .action-btn-primary {
          background: #e67e22;
          color: white;
          border: 2px solid #e67e22;
        }

        .action-btn-primary:hover {
          background: #d35400;
          border-color: #d35400;
        }

        .loading-container,
        .error-container {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          min-height: 400px;
        }

        .loading-container p,
        .error-container p {
          color: #d35400;
          font-size: 1.1rem;
          margin-bottom: 20px;
        }

        .spinner {
          width: 50px;
          height: 50px;
          border: 4px solid rgba(230, 126, 34, 0.3);
          border-top-color: #e67e22;
          border-radius: 50%;
          animation: spin 1s linear infinite;
        }

        @keyframes spin {
          to { transform: rotate(360deg); }
        }

        .back-btn {
          background: #e67e22;
          color: white;
          border: none;
          padding: 12px 28px;
          border-radius: 10px;
          font-size: 1rem;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s;
        }

        .back-btn:hover {
          background: #d35400;
        }

        @media (max-width: 768px) {
          .comparison-matrix-page {
            padding: 20px 12px;
          }

          .matrix-header {
            padding: 16px;
          }

          .header-content {
            flex-direction: column;
          }

          .header-title h1 {
            font-size: 1.4rem;
          }

          .matrix-topic {
            font-size: 1rem;
          }

          .matrix-stats {
            flex-wrap: wrap;
            padding: 12px 16px;
          }

          .matrix-content {
            padding: 20px 16px;
          }

          .matrix-actions {
            flex-direction: column;
          }

          .action-btn {
            width: 100%;
          }
        }
      `}</style>
    </div>
  )
}
