import { useState, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import { api } from './api'
import type {
  Paper,
  Statistics,
  ReviewRecord,
  ThreeCirclesAnalysis,
  CircleSummary,
  GapAnalysis,
  ReviewFramework
} from './types'
import './App.css'

function App() {
  const [topic, setTopic] = useState('')
  const [loading, setLoading] = useState(false)
  const [analyzing, setAnalyzing] = useState(false)
  const [review, setReview] = useState('')
  const [papers, setPapers] = useState<Paper[]>([])
  const [statistics, setStatistics] = useState<Statistics | null>(null)
  const [error, setError] = useState('')
  const [activeTab, setActiveTab] = useState<'review' | 'papers' | 'history' | 'analysis'>('review')
  const [currentRecordId, setCurrentRecordId] = useState<number | null>(null)

  // 三圈分析数据
  const [threeCirclesAnalysis, setThreeCirclesAnalysis] = useState<ThreeCirclesAnalysis | null>(null)
  const [circles, setCircles] = useState<CircleSummary[]>([])
  const [gapAnalysis, setGapAnalysis] = useState<GapAnalysis | null>(null)
  const [framework, setFramework] = useState<ReviewFramework | null>(null)

  // 历史记录
  const [records, setRecords] = useState<ReviewRecord[]>([])
  const [loadingHistory, setLoadingHistory] = useState(false)

  // 生成模式
  const [generateMode, setGenerateMode] = useState<'standard' | 'three-circles'>('three-circles')

  // 加载历史记录
  useEffect(() => {
    loadRecords()
  }, [])

  const loadRecords = async () => {
    setLoadingHistory(true)
    try {
      const response = await api.getRecords()
      if (response.success) {
        setRecords(response.records)
      }
    } catch (err) {
      console.error('加载历史记录失败:', err)
    } finally {
      setLoadingHistory(false)
    }
  }

  const handleAnalyze = async () => {
    if (!topic.trim()) {
      setError('请输入论文题目')
      return
    }

    setAnalyzing(true)
    setError('')
    setActiveTab('analysis')

    try {
      const response = await api.analyzeThreeCircles(topic)
      if (response.success && response.data) {
        setThreeCirclesAnalysis(response.data.analysis)
        setCircles([
          {
            circle: 'A',
            name: response.data.review_framework.sections[0].title,
            count: response.data.review_framework.sections[0].paper_count
          },
          {
            circle: 'B',
            name: response.data.review_framework.sections[1].title,
            count: response.data.review_framework.sections[1].paper_count
          },
          {
            circle: 'C',
            name: response.data.review_framework.sections[2].title,
            count: response.data.review_framework.sections[2].paper_count
          }
        ])
        setGapAnalysis(response.data.gap_analysis)
        setFramework(response.data.review_framework)
      }
    } catch (err) {
      setError('分析失败，请检查后端服务')
      console.error(err)
    } finally {
      setAnalyzing(false)
    }
  }

  const handleGenerate = async () => {
    if (!topic.trim()) {
      setError('请输入论文题目')
      return
    }

    setLoading(true)
    setError('')
    setReview('')
    setPapers([])
    setStatistics(null)
    setActiveTab('review')

    try {
      let response
      if (generateMode === 'three-circles') {
        response = await api.generateThreeCirclesReview(topic)
        if (response.success && response.data) {
          if (response.data.analysis) setThreeCirclesAnalysis(response.data.analysis)
          if (response.data.circles) setCircles(response.data.circles)
          if (response.data.gap_analysis) setGapAnalysis(response.data.gap_analysis)
          if (response.data.framework) setFramework(response.data.framework)
        }
      } else {
        response = await api.generateReview(topic)
      }

      if (response.success && response.data) {
        setReview(response.data.review)
        setPapers(response.data.papers)
        setStatistics(response.data.statistics)
        if (response.data.id) {
          setCurrentRecordId(response.data.id)
        }
        loadRecords()
      } else {
        setError(response.message)
      }
    } catch (err) {
      setError('生成失败，请检查后端服务是否正常运行')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const handleLoadRecord = async (id: number) => {
    try {
      const response = await api.getRecord(id)
      if (response.success && response.record) {
        const record = response.record
        setTopic(record.topic)
        setReview(record.review)
        setPapers(record.papers)
        setStatistics(record.statistics)
        setCurrentRecordId(record.id)
        setActiveTab('review')
      }
    } catch (err) {
      setError('加载记录失败')
      console.error(err)
    }
  }

  const handleDeleteRecord = async (id: number, event: React.MouseEvent) => {
    event.stopPropagation()
    if (!confirm('确定删除这条记录吗？')) return

    try {
      await api.deleteRecord(id)
      setRecords(records.filter(r => r.id !== id))
    } catch (err) {
      console.error('删除失败:', err)
    }
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  return (
    <div className="app">
      <header className="header">
        <h1>论文综述生成器</h1>
        <p>输入论文题目，基于「三圈交集」方法构建文献体系并生成综述</p>
      </header>

      <main className="main">
        <div className="mode-selector">
          <button
            className={`mode-btn ${generateMode === 'three-circles' ? 'active' : ''}`}
            onClick={() => setGenerateMode('three-circles')}
          >
            三圈分析模式（推荐）
          </button>
          <button
            className={`mode-btn ${generateMode === 'standard' ? 'active' : ''}`}
            onClick={() => setGenerateMode('standard')}
          >
            标准模式
          </button>
        </div>

        <div className="input-section">
          <input
            type="text"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder="请输入论文题目，例如：基于DMAIC的智能座舱软件持续交付流程优化研究"
            className="topic-input"
            onKeyDown={(e) => e.key === 'Enter' && handleGenerate()}
            disabled={loading || analyzing}
          />
          {generateMode === 'three-circles' && (
            <button
              onClick={handleAnalyze}
              disabled={analyzing || loading || !topic.trim()}
              className="analyze-btn"
            >
              {analyzing ? '分析中...' : '先分析题目'}
            </button>
          )}
          <button
            onClick={handleGenerate}
            disabled={loading || analyzing || !topic.trim()}
            className="generate-btn"
          >
            {loading ? '生成中...' : '生成综述'}
          </button>
        </div>

        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

        {(loading || analyzing) && (
          <div className="loading">
            <div className="spinner"></div>
            <p>{analyzing ? '正在分析题目结构...' : '正在检索文献并生成综述，请稍候...'}</p>
          </div>
        )}

        {statistics && (
          <div className="statistics">
            <div className="stat-item">
              <span className="stat-label">文献总数</span>
              <span className="stat-value">{statistics.total}篇</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">近5年</span>
              <span className="stat-value">{(statistics.recent_ratio * 100).toFixed(0)}%</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">英文文献</span>
              <span className="stat-value">{(statistics.english_ratio * 100).toFixed(0)}%</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">总被引量</span>
              <span className="stat-value">{statistics.total_citations}</span>
            </div>
          </div>
        )}

        {(review || threeCirclesAnalysis || records.length > 0) && (
          <div className="results">
            <div className="tabs">
              {threeCirclesAnalysis && (
                <button
                  className={`tab ${activeTab === 'analysis' ? 'active' : ''}`}
                  onClick={() => setActiveTab('analysis')}
                >
                  三圈分析
                </button>
              )}
              <button
                className={`tab ${activeTab === 'review' ? 'active' : ''}`}
                onClick={() => setActiveTab('review')}
                disabled={!review}
              >
                文献综述
              </button>
              <button
                className={`tab ${activeTab === 'papers' ? 'active' : ''}`}
                onClick={() => setActiveTab('papers')}
                disabled={!review}
              >
                参考文献列表 {papers.length > 0 && `(${papers.length})`}
              </button>
              <button
                className={`tab ${activeTab === 'history' ? 'active' : ''}`}
                onClick={() => setActiveTab('history')}
              >
                历史记录 {records.length > 0 && `(${records.length})`}
              </button>
            </div>

            <div className="tab-content">
              {activeTab === 'analysis' && threeCirclesAnalysis ? (
                <div className="analysis-content">
                  <div className="analysis-section">
                    <h2>📊 题目解析</h2>
                    <div className="analysis-grid">
                      <div className="analysis-card circle-a">
                        <div className="circle-label">圈 A：研究对象</div>
                        <div className="circle-value">{threeCirclesAnalysis.domain}</div>
                      </div>
                      <div className="analysis-card circle-b">
                        <div className="circle-label">圈 B：优化目标</div>
                        <div className="circle-value">{threeCirclesAnalysis.optimization}</div>
                      </div>
                      <div className="analysis-card circle-c">
                        <div className="circle-label">圈 C：方法论</div>
                        <div className="circle-value">{threeCirclesAnalysis.methodology}</div>
                      </div>
                    </div>
                  </div>

                  {circles.length > 0 && (
                    <div className="analysis-section">
                      <h2>🔍 三圈文献检索</h2>
                      <div className="circles-list">
                        {circles.map((circle) => (
                          <div key={circle.circle} className={`circle-item circle-${circle.circle.toLowerCase()}`}>
                            <div className="circle-header">
                              <span className="circle-badge">{circle.circle}</span>
                              <span className="circle-name">{circle.name}</span>
                            </div>
                            <div className="circle-count">检索到 {circle.count} 篇相关文献</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {gapAnalysis && (
                    <div className="analysis-section">
                      <h2>🎯 研究缺口分析</h2>
                      <div className="gap-card">
                        <div className="gap-description">{gapAnalysis.gap_description}</div>
                        <div className="gap-opportunity">
                          <strong>研究机会：</strong>{gapAnalysis.research_opportunity}
                        </div>
                        <div className="gap-suggestions">
                          <strong>建议方向：</strong>
                          <ul>
                            {gapAnalysis.suggestions.map((s, i) => (
                              <li key={i}>{s}</li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    </div>
                  )}

                  {framework && (
                    <div className="analysis-section">
                      <h2>📝 综述框架</h2>
                      <div className="framework-list">
                        {framework.sections.map((section, index) => (
                          <div key={index} className="framework-item">
                            <h4>{section.title}</h4>
                            <p className="framework-desc">{section.description}</p>
                            <ul className="framework-points">
                              {section.key_points.map((point, i) => (
                                <li key={i}>{point}</li>
                              ))}
                            </ul>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ) : activeTab === 'history' ? (
                <div className="history-content">
                  {loadingHistory ? (
                    <div className="loading-small">加载中...</div>
                  ) : records.length === 0 ? (
                    <div className="empty-state">暂无历史记录</div>
                  ) : (
                    <div className="records-list">
                      {records.map(record => (
                        <div
                          key={record.id}
                          className="record-item"
                          onClick={() => handleLoadRecord(record.id)}
                        >
                          <div className="record-header">
                            <h3 className="record-topic">{record.topic}</h3>
                            <button
                              className="delete-btn"
                              onClick={(e) => handleDeleteRecord(record.id, e)}
                            >
                              删除
                            </button>
                          </div>
                          <div className="record-meta">
                            <span className="record-date">{formatDate(record.created_at)}</span>
                            <span className="record-papers">{record.statistics?.total || 0} 篇文献</span>
                            <span className={`record-status ${record.status}`}>
                              {record.status === 'success' ? '成功' : '失败'}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ) : activeTab === 'review' && review ? (
                <div className="review-content">
                  <ReactMarkdown>{review}</ReactMarkdown>
                </div>
              ) : activeTab === 'papers' && papers.length > 0 ? (
                <div className="papers-list">
                  {papers.map((paper, index) => (
                    <div key={paper.id} className="paper-item">
                      <div className="paper-number">[{index + 1}]</div>
                      <div className="paper-info">
                        <h3 className="paper-title">{paper.title}</h3>
                        <div className="paper-meta">
                          <span className="paper-authors">
                            {paper.authors.slice(0, 3).join(', ')}
                            {paper.authors.length > 3 && ' 等'}
                          </span>
                          <span className="paper-year">{paper.year}</span>
                          <span className="paper-citations">
                            被引 {paper.cited_by_count} 次
                          </span>
                          {paper.is_english && <span className="paper-lang">英文</span>}
                        </div>
                        {paper.doi && (
                          <a
                            href={`https://doi.org/${paper.doi}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="paper-doi"
                          >
                            DOI: {paper.doi}
                          </a>
                        )}
                        {paper.concepts.length > 0 && (
                          <div className="paper-concepts">
                            {paper.concepts.map((concept) => (
                              <span key={concept} className="concept-tag">
                                {concept}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="empty-state">
                  {threeCirclesAnalysis ? '点击「生成综述」开始生成' : '请先分析题目或生成综述'}
                </div>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  )
}

export default App
