/**
 * ProfilePage Component - International Academic Version
 * Designed for overseas market with clean, professional academic style
 */
import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { api } from '../api'
import { getLocalUserInfo, isLoggedIn } from '../authApi'
import { PaddlePaymentModal } from './PaddlePaymentModal'
import { ConfirmModalInternational } from './ConfirmModalInternational'
import type { ReviewRecord } from '../types'
import './ProfilePageInternational.css'

export function ProfilePageInternational() {
  const { i18n } = useTranslation()
  const navigate = useNavigate()
  const [records, setRecords] = useState<ReviewRecord[]>([])
  const [loading, setLoading] = useState(false)
  const [userInfo, setUserInfo] = useState<any>(null)
  const [credits, setCredits] = useState<number>(0)
  const [freeCredits, setFreeCredits] = useState<number>(0)
  const [showPayModal, setShowPayModal] = useState(false)
  const [pendingExportRecordId, setPendingExportRecordId] = useState<number | null>(null)
  const [exportingId, setExportingId] = useState<number | null>(null)
  const [unlockMode, setUnlockMode] = useState(false)  // true=single unlock, false=purchase plan
  const [showCreditConfirmModal, setShowCreditConfirmModal] = useState(false)
  const [confirmRecordId, setConfirmRecordId] = useState<number | null>(null)
  const [showCloseAccountModal, setShowCloseAccountModal] = useState(false)
  const [closeAccountEmail, setCloseAccountEmail] = useState('')
  const [showEditProfileModal, setShowEditProfileModal] = useState(false)
  const [editNickname, setEditNickname] = useState('')

  useEffect(() => {
    if (!isLoggedIn()) {
      navigate('/login')
      return
    }
    setUserInfo(getLocalUserInfo())
    loadRecords()
    api.getCredits().then(data => {
      setCredits(data.credits)
      setFreeCredits(data.free_credits)
    }).catch(err => console.error('Failed to fetch credits:', err))
  }, [navigate])

  const loadRecords = async () => {
    setLoading(true)
    try {
      const response = await api.getRecords()
      if (response.success) {
        setRecords(response.records)
      }
    } catch (err) {
      console.error('Failed to load history:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleViewRecord = (record: ReviewRecord) => {
    if (record.status === 'processing' || record.status === 'failed') {
      // Processing or failed tasks, guide to regenerate
      sessionStorage.setItem('pending_topic', record.topic)
      navigate('/')
      return
    }
    if (record.task_id) {
      navigate(`/review?task_id=${record.task_id}`)
    } else if (record.id) {
      navigate('/review', {
        state: {
          title: record.topic,
          content: record.review,
          papers: record.papers,
          recordId: record.id,
          isPaid: record.is_paid ?? false,
        }
      })
    }
  }

  const handleExportRecord = async (id: number, event: React.MouseEvent) => {
    event.stopPropagation()
    const record = records.find(r => r.id === id)
    if (!record) return

    // Paid reviews, export directly
    if (record.is_paid) {
      await doExport(id, record)
      return
    }

    // Free reviews, check if has paid credits
    if (credits > 0) {
      // Has credits, show confirmation
      setConfirmRecordId(id)
      setShowCreditConfirmModal(true)
      return
    }

    // No credits, show payment modal
    setUnlockMode(true)
    setPendingExportRecordId(id)
    setShowPayModal(true)
  }

  const doExport = async (id: number, record: ReviewRecord) => {
    setExportingId(id)
    try {
      const blob = await api.exportReview(id)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      const filename = record.topic.replace(/[\/\\:]/g, '-')
      a.download = `${filename}.docx`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } catch (err) {
      console.error('Export failed:', err)
      alert('Export failed, please try again later')
    } finally {
      setExportingId(null)
    }
  }

  const handleConfirmUseCredit = async () => {
    if (confirmRecordId === null) return
    const record = records.find(r => r.id === confirmRecordId)
    if (!record) return

    setShowCreditConfirmModal(false)
    setExportingId(confirmRecordId)

    try {
      const result = await api.unlockRecordWithCredit(confirmRecordId)
      if (result.success) {
        // Refresh records and credits
        await loadRecords()
        const creditsData = await api.getCredits()
        setCredits(creditsData.credits)

        // Export directly
        await doExport(confirmRecordId, record)
      } else {
        alert(result.message || 'Unlock failed, please try again later')
      }
    } catch (err) {
      console.error('Unlock failed:', err)
      alert('Unlock failed, please try again later')
    } finally {
      setExportingId(null)
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
      alert('Failed to close account. Please contact support@snappicker.com')
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
      <nav className="profile-nav">
        <div className="nav-logo" onClick={() => navigate('/')} style={{ cursor: 'pointer' }}>
          <span className="logo-icon">📚</span>
          <span className="logo-text">AutoOverview</span>
        </div>
        <div className="nav-actions">
          <button className="nav-btn nav-btn-home" onClick={() => navigate('/')}>
            Home
          </button>
          <button className="nav-btn nav-btn-logout" onClick={handleLogout}>
            Logout
          </button>
        </div>
      </nav>

      <div className="profile-container">
        {/* User Info Section */}
        <div className="profile-header">
          <div className="user-avatar-large">👤</div>
          <div className="user-info-section">
            <div className="user-info-row">
              <h1 className="user-name">{userInfo?.nickname || 'User'}</h1>
              <button className="edit-profile-button" onClick={handleEditProfile}>
                ✏️ Edit
              </button>
              <button className="close-account-button" onClick={() => { setShowCloseAccountModal(true); setCloseAccountEmail(''); }}>
                Close Account
              </button>
            </div>
            <p className="user-email">{userInfo?.email || ''}</p>
          </div>
        </div>

        {/* Stats */}
        <div className="profile-stats">
          <div className="stat-card">
            <div className="stat-number">{records.length}</div>
            <div className="stat-label">Reviews</div>
          </div>
          <div className="stat-card stat-card-free">
            <div className="stat-number">{freeCredits}</div>
            <div className="stat-label">Free Credits</div>
          </div>
          <div className="stat-card stat-card-paid">
            <div className="stat-number">{credits - freeCredits}</div>
            <div className="stat-label">Plan Credits</div>
          </div>
        </div>

        {/* History List */}
        <div className="profile-history">
          <h2 className="history-title">📖 My Reviews</h2>

          {loading ? (
            <div className="history-loading">
              <div className="spinner"></div>
              <p>Loading history...</p>
            </div>
          ) : records.length === 0 ? (
            <div className="history-empty">
              <div className="empty-icon">📝</div>
              <p className="empty-title">No reviews yet</p>
              <p className="empty-desc">Enter a research topic and AI will automatically search papers and generate a professional review</p>
              <button className="empty-button" onClick={() => navigate('/')}>
                Generate Your First Review
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
                          className={`export-button ${!record.is_paid ? 'export-word-premium' : ''}`}
                          onClick={(e) => handleExportRecord(record.id, e)}
                          disabled={exportingId === record.id}
                        >
                          {exportingId === record.id ? 'Exporting...' :
                           record.is_paid ? 'Export Word' :
                           '🔓 Unlock Export'}
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Footer */}
      <footer className="profile-footer">
        <div className="footer-content">
          <p className="footer-copyright">© 2026 AutoOverview. All rights reserved.</p>
          <div className="footer-links">
            <a href="/terms-and-conditions" className="footer-link">Terms & Conditions</a>
            <span className="footer-separator">•</span>
            <a href="/privacy-policy" className="footer-link">Privacy Policy</a>
            <span className="footer-separator">•</span>
            <a href="/refund-policy" className="footer-link">Refund Policy</a>
          </div>
        </div>
      </footer>

      {/* Payment Modal */}
      {showPayModal && unlockMode && pendingExportRecordId !== null && (
        <PaddlePaymentModal
          onClose={() => {
            setShowPayModal(false)
            setUnlockMode(false)
            setPendingExportRecordId(null)
          }}
          onPaymentSuccess={async () => {
            setShowPayModal(false)
            setUnlockMode(false)
            // Refresh records
            await loadRecords()
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
        <PaddlePaymentModal
          onClose={() => {
            setShowPayModal(false)
            setPendingExportRecordId(null)
          }}
          onPaymentSuccess={async () => {
            setShowPayModal(false)
            // Refresh user status and records
            const creditsData = await api.getCredits()
            setCredits(creditsData.credits)
            setFreeCredits(creditsData.free_credits)
            await loadRecords()
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
