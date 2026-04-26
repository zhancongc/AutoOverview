import { useState, useEffect, useRef } from 'react'
import { useTranslation } from 'react-i18next'
import { api } from '../api'
import './ShareRewardModal.css'

interface ShareRewardModalProps {
  taskId: string
  onClose: () => void
}

export function ShareRewardModal({ taskId, onClose }: ShareRewardModalProps) {
  const { t } = useTranslation()
  const isChineseSite = !document.documentElement.classList.contains('intl')
  const [uploading, setUploading] = useState(false)
  const [uploaded, setUploaded] = useState(false)
  const [error, setError] = useState('')
  const [credits, setCredits] = useState<number | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', handleEscape)
    return () => document.removeEventListener('keydown', handleEscape)
  }, [onClose])

  const handleUpload = async (file: File) => {
    if (uploading || uploaded) return
    setUploading(true)
    setError('')

    try {
      const res = await api.uploadShareProof(taskId, file)
      if (res.success) {
        setUploaded(true)
        setCredits(res.credits ?? null)
      } else {
        setError(res.message || t('share_reward.upload_failed'))
      }
    } catch (e: any) {
      const msg = e?.response?.data?.detail || t('share_reward.upload_failed')
      setError(msg)
    } finally {
      setUploading(false)
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) handleUpload(file)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    const file = e.dataTransfer.files?.[0]
    if (file) handleUpload(file)
  }

  return (
    <div className="share-reward-overlay" onClick={onClose}>
      <div className="share-reward-modal" onClick={e => e.stopPropagation()}>
        <button className="share-reward-close" onClick={onClose}>&times;</button>

        <div className="share-reward-header">
          <span className="share-reward-icon">🎉</span>
          <h2 className="share-reward-title">
            {isChineseSite ? '分享你的综述，免费领积分！' : 'Share Your Review, Earn Free Credits!'}
          </h2>
        </div>

        <div className="share-reward-body">
          {/* 路径一：加微信 / Follow X */}
          <div className="share-reward-path">
            <h3 className="share-reward-path-title">
              {isChineseSite
                ? '路径一：加微信领积分 + 进硕博群'
                : 'Share on X (Twitter)'}
            </h3>
            {isChineseSite ? (
              <>
                <div className="share-reward-qr-wrapper">
                  <img
                    src="/wechat-qr.jpg"
                    alt="WeChat QR"
                    className="share-reward-qr"
                  />
                </div>
                <p className="share-reward-desc">
                  添加开发者微信，发送分享截图，即可领取 2 积分并加入专属硕博交流群
                </p>
              </>
            ) : (
              <div style={{ textAlign: 'center' }}>
                <a
                  href="https://x.com/JadeZhan0822"
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{
                    display: 'inline-flex', alignItems: 'center', gap: '8px',
                    padding: '12px 24px', borderRadius: '12px',
                    background: '#000', color: '#fff', textDecoration: 'none',
                    fontWeight: 600, fontSize: '15px', transition: 'all 0.2s',
                  }}
                >
                  𝕏 @JadeZhan0822
                </a>
                <p className="share-reward-desc" style={{ marginTop: '12px' }}>
                  Post about Danmo Scholar on X and tag <strong>@JadeZhan0822</strong>, then upload the screenshot below to earn 2 free credits!
                </p>
              </div>
            )}
          </div>

          {/* 分隔线 */}
          {isChineseSite && (
            <div className="share-reward-divider">
              <span>或</span>
            </div>
          )}

          {/* 路径二：上传截图 */}
          {isChineseSite && (
          <div className="share-reward-path">
            <h3 className="share-reward-path-title">
              路径二：上传分享截图
            </h3>
            <p className="share-reward-desc">
              在小红书/朋友圈分享后，上传截图，系统自动发放 2 积分
            </p>

            {uploaded ? (
              <div className="share-reward-success">
                <span className="share-reward-success-icon">✓</span>
                <span>
                  {credits !== null ? `已领取 2 积分，当前余额 ${credits} 积分` : '已领取 2 积分'}
                </span>
              </div>
            ) : (
              <>
                <div
                  className="share-reward-upload-area"
                  onClick={() => fileInputRef.current?.click()}
                  onDragOver={e => e.preventDefault()}
                  onDrop={handleDrop}
                >
                  <span className="share-reward-upload-icon">📸</span>
                  <span className="share-reward-upload-text">
                    点击上传或拖拽图片
                  </span>
                </div>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  onChange={handleFileChange}
                  style={{ display: 'none' }}
                />
                {uploading && (
                  <div className="share-reward-uploading">
                    <span className="share-reward-spinner" />
                    上传中...
                  </div>
                )}
                {error && (
                  <p className="share-reward-error">{error}</p>
                )}
              </>
            )}
          </div>
          )}

          {/* 英文站：上传截图 */}
          {!isChineseSite && (
          <div className="share-reward-path">
            {uploaded ? (
              <div className="share-reward-success">
                <span className="share-reward-success-icon">✓</span>
                <span>
                  {credits !== null ? `2 credits claimed, balance: ${credits}` : '2 credits claimed'}
                </span>
              </div>
            ) : (
              <>
                <div
                  className="share-reward-upload-area"
                  onClick={() => fileInputRef.current?.click()}
                  onDragOver={e => e.preventDefault()}
                  onDrop={handleDrop}
                >
                  <span className="share-reward-upload-icon">📸</span>
                  <span className="share-reward-upload-text">
                    Click to upload or drag & drop
                  </span>
                </div>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  onChange={handleFileChange}
                  style={{ display: 'none' }}
                />
                {uploading && (
                  <div className="share-reward-uploading">
                    <span className="share-reward-spinner" />
                    Uploading...
                  </div>
                )}
                {error && (
                  <p className="share-reward-error">{error}</p>
                )}
              </>
            )}
          </div>
          )}
        </div>
      </div>
    </div>
  )
}
