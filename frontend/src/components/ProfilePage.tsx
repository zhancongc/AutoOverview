import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'
import { authApi, getLocalUserInfo, isLoggedIn } from '../authApi'
import type { ReviewRecord } from '../types'
import './ProfilePage.css'

export function ProfilePage() {
  const navigate = useNavigate()
  const [records, setRecords] = useState<ReviewRecord[]>([])
  const [loading, setLoading] = useState(false)
  const [userInfo, setUserInfo] = useState<any>(null)
  const [credits, setCredits] = useState<number>(0)

  useEffect(() => {
    if (!isLoggedIn()) {
      navigate('/login')
      return
    }
    setUserInfo(getLocalUserInfo())
    loadRecords()
    api.getCredits().then(data => setCredits(data.credits)).catch(() => {})
  }, [])

  const loadRecords = async () => {
    setLoading(true)
    try {
      const response = await api.getRecords()
      if (response.success) {
        setRecords(response.records)
      }
    } catch (err) {
      console.error('加载历史记录失败:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleViewRecord = (record: ReviewRecord) => {
    if (record.task_id) {
      navigate(`/review?task_id=${record.task_id}`)
    } else if (record.id) {
      navigate('/review', {
        state: {
          title: record.topic,
          content: record.review,
          papers: record.papers,
          recordId: record.id
        }
      })
    }
  }

  const handleExportRecord = async (id: number, event: React.MouseEvent) => {
    event.stopPropagation()
    try {
      const blob = await api.exportReview(id)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      const record = records.find(r => r.id === id)
      const filename = record ? record.topic.replace(/[\/\\:]/g, '-') : 'review'
      a.download = `${filename}.docx`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } catch (err) {
      console.error('导出失败:', err)
    }
  }

  const handleDeleteRecord = async (id: number, event: React.MouseEvent) => {
    event.stopPropagation()
    if (!confirm('确定要删除这条记录吗？')) {
      return
    }
    try {
      await api.deleteRecord(id)
      setRecords(records.filter(r => r.id !== id))
    } catch (err) {
      console.error('删除失败:', err)
    }
  }

  const handleLogout = () => {
    localStorage.removeItem('auth_token')
    localStorage.removeItem('user_info')
    navigate('/')
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
    <div className="profile-page">
      {/* 顶部导航栏 */}
      <nav className="profile-nav">
        <div className="nav-logo" onClick={() => navigate('/')} style={{ cursor: 'pointer' }}>
          <span className="logo-icon">📚</span>
          <span className="logo-text">AutoOverview</span>
        </div>
        <div className="nav-actions">
          <button className="nav-btn nav-btn-home" onClick={() => navigate('/')}>
            首页
          </button>
          <button className="nav-btn nav-btn-logout" onClick={handleLogout}>
            退出登录
          </button>
        </div>
      </nav>

      <div className="profile-container">
        {/* 用户信息区域 */}
        <div className="profile-header">
          <div className="user-avatar-large">👤</div>
          <div className="user-info-section">
            <h1 className="user-name">{userInfo?.nickname || '用户'}</h1>
            <p className="user-email">{userInfo?.email || ''}</p>
          </div>
        </div>

        {/* 统计信息 */}
        <div className="profile-stats">
          <div className="stat-card">
            <div className="stat-number">{records.length}</div>
            <div className="stat-label">总综述数</div>
          </div>
          <div className="stat-card stat-card-credits">
            <div className="stat-number">{credits}</div>
            <div className="stat-label">剩余额度</div>
          </div>
        </div>

        {/* 历史记录列表 */}
        <div className="profile-history">
          <h2 className="history-title">📖 我的综述</h2>

          {loading ? (
            <div className="history-loading">
              <div className="spinner"></div>
              <p>加载历史记录中...</p>
            </div>
          ) : records.length === 0 ? (
            <div className="history-empty">
              <div className="empty-icon">📝</div>
              <p>还没有生成过综述</p>
              <button className="empty-button" onClick={() => navigate('/')}>
                去生成第一篇综述
              </button>
            </div>
          ) : (
            <div className="records-list">
              {records.map((record) => (
                <div
                  key={record.id}
                  className="record-item"
                  onClick={() => handleViewRecord(record)}
                >
                  <div className="record-main">
                    <div className="record-top">
                      <h3 className="record-topic">{record.topic}</h3>
                      <div className="record-status-badge">
                        {record.status === 'success' ? (
                          <span className="status-success">✓ 完成</span>
                        ) : record.status === 'failed' ? (
                          <span className="status-failed">✗ 失败</span>
                        ) : (
                          <span className="status-processing">⏳ 进行中</span>
                        )}
                      </div>
                    </div>
                    <div className="record-info">
                      <span className="record-time">{formatDate(record.created_at)}</span>
                      {record.statistics && (
                        <div className="record-stats-inline">
                          <span>📄 {record.statistics.total || 0} 篇文献</span>
                        </div>
                      )}
                    </div>
                  </div>
                  <div className="record-actions">
                    <button
                      className="action-btn action-export"
                      onClick={(e) => handleExportRecord(record.id, e)}
                      title="导出 Word"
                    >
                      📥
                    </button>
                    <button
                      className="action-btn action-delete"
                      onClick={(e) => handleDeleteRecord(record.id, e)}
                      title="删除"
                    >
                      🗑
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* 页脚 */}
      <footer className="profile-footer">
        <div className="footer-content">
          <p className="footer-copyright">© 2026 AutoOverview. All rights reserved.</p>
          <a href="https://beian.miit.gov.cn/" target="_blank" rel="noopener noreferrer" className="footer-icp">
            沪ICP备2023018158号-4
          </a>
        </div>
      </footer>
    </div>
  )
}
