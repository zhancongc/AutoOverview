/**
 * FeedbackFloatingButton - 用户反馈悬浮按钮 + 左侧弹窗
 * 仅登录用户可见，自动填充邮箱
 * 英文版：放在 Privacy Settings 按钮上方
 * 中文版：放在 Privacy Settings 的位置上
 */
import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { api } from '../api'
import { isLoggedIn as checkLoggedIn } from '../authApi'
import './FeedbackFloatingButton.css'

// 检测是否为英文版
const isEnglishVersion = typeof __BUILD_VERSION__ !== 'undefined' && __BUILD_VERSION__ === 'english'

export function FeedbackFloatingButton() {
  const { t } = useTranslation()
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [isOpen, setIsOpen] = useState(false)
  const [feedback, setFeedback] = useState('')
  const [email, setEmail] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [submitted, setSubmitted] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const loggedIn = checkLoggedIn()
    setIsLoggedIn(loggedIn)
    if (loggedIn) {
      // 从 profile 获取邮箱
      api.getCredits().catch(() => {})
      // 从 token 解析 email
      const token = localStorage.getItem('auth_token')
      if (token) {
        try {
          const payload = JSON.parse(atob(token.split('.')[1]))
          if (payload.email) setEmail(payload.email)
        } catch {}
      }
    }
  }, [])

  if (!isLoggedIn) return null

  const handleSubmit = async () => {
    if (!feedback.trim()) return
    setSubmitting(true)
    setError(null)
    try {
      await api.submitFeedback({ email, content: feedback.trim() })
      setSubmitted(true)
      setFeedback('')
      setTimeout(() => {
        setSubmitted(false)
        setIsOpen(false)
      }, 2000)
    } catch (err: any) {
      const detail = err?.response?.data?.detail
      if (detail?.includes('Too many')) {
        setError(isEnglishVersion
          ? 'Too many feedback submissions. Please try again tomorrow.'
          : '今日反馈次数已达上限，请明天再试。'
        )
      } else {
        setError(isEnglishVersion
          ? 'Failed to submit feedback. Please try again.'
          : '提交失败，请重试。'
        )
      }
      setTimeout(() => setError(null), 3000)
    } finally {
      setSubmitting(false)
    }
  }

  // 根据版本确定位置类名
  const positionClass = isEnglishVersion ? 'feedback-english' : 'feedback-chinese'

  return (
    <>
      {/* Floating button */}
      <div className={`feedback-float-btn ${positionClass}`} onClick={() => setIsOpen(!isOpen)}>
        <span className="feedback-float-icon">{isOpen ? '✕' : '💬'}</span>
        <span className="feedback-float-text">{t('feedback.button')}</span>
      </div>

      {/* Slide-out panel */}
      {isOpen && (
        <div className={`feedback-panel ${positionClass}`}>
          <div className="feedback-header">
            <span className="feedback-icon">💬</span>
            <h3 className="feedback-title">{t('feedback.title')}</h3>
            <button className="feedback-close" onClick={() => setIsOpen(false)}>✕</button>
          </div>
          <div className="feedback-body">
            {email && (
              <div className="feedback-email">
                <span className="feedback-email-label">{t('feedback.email')}</span>
                <span className="feedback-email-value">{email}</span>
              </div>
            )}
            {error && (
              <div className="feedback-error">
                {error}
              </div>
            )}
            <textarea
              className="feedback-textarea"
              placeholder={t('feedback.placeholder')}
              value={feedback}
              onChange={(e) => setFeedback(e.target.value)}
              rows={5}
              maxLength={1000}
            />
            <div className="feedback-footer">
              <span className="feedback-count">{feedback.length}/1000</span>
              <button
                className="feedback-submit"
                onClick={handleSubmit}
                disabled={!feedback.trim() || submitting}
              >
                {submitted ? t('feedback.submitted') : submitting ? t('feedback.submitting') : t('feedback.submit')}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
