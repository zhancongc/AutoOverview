/**
 * DavidApprovePage - 分享截图审核页面
 * URL: /david/approve
 * 展示待审核的分享截图，支持通过/拒绝操作
 */
import React, { useState, useEffect } from 'react'

interface ShareProof {
  filename: string
  user_email: string
  user_id: number
  task_id: string
  created_at: string
}

export const DavidApprovePage: React.FC = () => {
  const [proofs, setProofs] = useState<ShareProof[]>([])
  const [loading, setLoading] = useState(true)
  const [processing, setProcessing] = useState<string | null>(null)

  const fetchProofs = async () => {
    try {
      const token = localStorage.getItem('auth_token')
      const headers: Record<string, string> = {}
      if (token) headers.Authorization = `Bearer ${token}`

      const res = await fetch('/api/david/share-proofs', { headers })
      const data = await res.json()
      if (data.success) {
        setProofs(data.proofs)
      }
    } catch (err) {
      console.error('Failed to fetch proofs:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchProofs()
  }, [])

  const handleAction = async (filename: string, action: 'approve' | 'reject') => {
    setProcessing(filename)
    try {
      const token = localStorage.getItem('auth_token')
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      }
      if (token) headers.Authorization = `Bearer ${token}`

      const res = await fetch(`/api/david/share-proofs/${filename}/${action}`, {
        method: 'POST',
        headers,
      })
      const data = await res.json()
      if (data.success) {
        setProofs(prev => prev.filter(p => p.filename !== filename))
      } else {
        alert(data.detail || '操作失败')
      }
    } catch (err) {
      console.error('Action failed:', err)
      alert('操作失败')
    } finally {
      setProcessing(null)
    }
  }

  return (
    <div className="david-page">
      <div className="david-container">
        <header className="david-header">
          <div className="david-header-row">
            <div>
              <h1>分享截图审核</h1>
              <p className="david-subtitle">审核用户分享截图，通过后发放 2 积分</p>
            </div>
            <a href="/#/david" style={{ color: '#636E72', textDecoration: 'none', fontSize: '14px' }}>
              ← 返回数据统计
            </a>
          </div>
        </header>

        {loading ? (
          <p style={{ textAlign: 'center', padding: '4rem', color: '#636E72' }}>加载中...</p>
        ) : proofs.length === 0 ? (
          <section className="david-section">
            <div style={{ textAlign: 'center', padding: '3rem', color: '#636E72' }}>
              <p style={{ fontSize: '1.2rem', marginBottom: '0.5rem' }}>暂无待审核截图</p>
              <p style={{ fontSize: '0.9rem' }}>所有分享截图已审核完毕</p>
            </div>
          </section>
        ) : (
          <section className="david-section">
            <div style={{ marginBottom: '1rem', color: '#636E72', fontSize: '14px' }}>
              共 {proofs.length} 条待审核
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {proofs.map(proof => (
                <div key={proof.filename} style={{
                  display: 'flex', gap: '20px', padding: '16px',
                  background: '#fff', borderRadius: '12px',
                  border: '1px solid #E8ECEF', alignItems: 'flex-start',
                }}>
                  <a
                    href={`/share-proofs/${proof.filename}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{ flexShrink: 0 }}
                  >
                    <img
                      src={`/share-proofs/${proof.filename}`}
                      alt="分享截图"
                      style={{
                        width: '160px', height: '160px', objectFit: 'cover',
                        borderRadius: '8px', border: '1px solid #E8ECEF',
                      }}
                    />
                  </a>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: '14px', color: '#2D3436', marginBottom: '6px' }}>
                      <strong>{proof.user_email}</strong>
                    </div>
                    <div style={{ fontSize: '13px', color: '#636E72', marginBottom: '4px' }}>
                      Task ID: {proof.task_id || '-'}
                    </div>
                    <div style={{ fontSize: '13px', color: '#636E72', marginBottom: '12px' }}>
                      提交时间: {proof.created_at ? new Date(proof.created_at).toLocaleString() : '-'}
                    </div>
                    <div style={{ display: 'flex', gap: '10px' }}>
                      <button
                        onClick={() => handleAction(proof.filename, 'approve')}
                        disabled={processing === proof.filename}
                        style={{
                          padding: '8px 20px', borderRadius: '8px', border: 'none',
                          background: '#22c55e', color: '#fff', fontWeight: 600,
                          cursor: processing === proof.filename ? 'not-allowed' : 'pointer',
                          opacity: processing === proof.filename ? 0.6 : 1,
                          fontSize: '14px',
                        }}
                      >
                        {processing === proof.filename ? '处理中...' : '通过'}
                      </button>
                      <button
                        onClick={() => handleAction(proof.filename, 'reject')}
                        disabled={processing === proof.filename}
                        style={{
                          padding: '8px 20px', borderRadius: '8px', border: 'none',
                          background: '#ef4444', color: '#fff', fontWeight: 600,
                          cursor: processing === proof.filename ? 'not-allowed' : 'pointer',
                          opacity: processing === proof.filename ? 0.6 : 1,
                          fontSize: '14px',
                        }}
                      >
                        拒绝
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}
      </div>
    </div>
  )
}
