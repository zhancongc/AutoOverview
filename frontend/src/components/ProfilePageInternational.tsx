/**
 * ProfilePage Component - International Academic Version
 * Designed for overseas market with clean, professional academic style
 */
import { useState, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { api } from '../api'
import { getLocalUserInfo, isLoggedIn } from '../authApi'

import { PayPalPaymentModal } from './PayPalPaymentModal'
import { ConfirmModalInternational } from './ConfirmModalInternational'
import type { ReviewRecord } from '../types'
import './SimpleAppInternational.css'
import './ProfilePageInternational.css'

type ProfileTab = 'reviews' | 'searches' | 'matrices'

export function ProfilePageInternational() {
  const { i18n } = useTranslation()
  const navigate = useNavigate()
  const location = useLocation()
  const [activeTab, setActiveTab] = useState<ProfileTab>('reviews')
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [records, setRecords] = useState<ReviewRecord[]>([])
  const [searches, setSearches] = useState<any[]>([])
  const [matrices, setMatrices] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [userInfo, setUserInfo] = useState<any>(null)
  const [credits, setCredits] = useState<number>(0)
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
        await loadAllRecords()
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
      <nav className="home-nav">
        <div className="nav-logo" onClick={() => navigate('/')} style={{ cursor: 'pointer' }}>
          <span className="logo-icon">📚</span>
          <span className="logo-text">AutoOverview</span>
        </div>
        <div className="nav-links">
          <a href="/" className={location.pathname === '/' ? 'active' : ''} onClick={(e) => { e.preventDefault(); navigate('/') }}>Home</a>
          <a href="/search-papers" className={location.pathname === '/search-papers' ? 'active' : ''} onClick={(e) => { e.preventDefault(); navigate('/search-papers') }}>Search Papers</a>
          <a href="/comparison-matrix" className={location.pathname === '/comparison-matrix' ? 'active' : ''} onClick={(e) => { e.preventDefault(); navigate('/comparison-matrix') }}>Comparison Matrix</a>
          <a href="/generate" className={location.pathname === '/generate' ? 'active' : ''} onClick={(e) => { e.preventDefault(); navigate('/generate') }}>Literature Summary</a>
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
          <span className="logo-text">AutoOverview</span>
          <button className="sidebar-close" onClick={() => setMobileMenuOpen(false)}>&times;</button>
        </div>
        <nav className="sidebar-links">
          <a href="/" className={location.pathname === '/' ? 'active' : ''} onClick={(e) => { e.preventDefault(); setMobileMenuOpen(false); navigate('/') }}>Home</a>
          <a href="/search-papers" className={location.pathname === '/search-papers' ? 'active' : ''} onClick={(e) => { e.preventDefault(); setMobileMenuOpen(false); navigate('/search-papers') }}>Search Papers</a>
          <a href="/comparison-matrix" className={location.pathname === '/comparison-matrix' ? 'active' : ''} onClick={(e) => { e.preventDefault(); setMobileMenuOpen(false); navigate('/comparison-matrix') }}>Comparison Matrix</a>
          <a href="/generate" className={location.pathname === '/generate' ? 'active' : ''} onClick={(e) => { e.preventDefault(); setMobileMenuOpen(false); navigate('/generate') }}>Literature Summary</a>
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
            className={`profile-tab ${activeTab === 'reviews' ? 'active' : ''}`}
            onClick={() => setActiveTab('reviews')}
          >
            📖 My Reviews
          </button>
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
                          <button className="export-button">
                            View Results
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
                  {matrices.map((matrix) => (
                    <div
                      key={matrix.id}
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
                          <button className="export-button">
                            View Matrix
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
