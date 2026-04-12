import { useState, useEffect, useRef } from 'react'
import { useTranslation } from 'react-i18next'
import { authApi } from '../authApi'
import './LoginModal.css'

interface LoginModalProps {
  onClose: () => void
  onLoginSuccess: () => void
  pendingTopic?: string
}

export function LoginModal({ onClose, onLoginSuccess, pendingTopic }: LoginModalProps) {
  const { t } = useTranslation()
  const modalRef = useRef<HTMLDivElement>(null)
  const [email, setEmail] = useState('')
  const [code, setCode] = useState('')

  const [loading, setLoading] = useState(false)
  const [sendingCode, setSendingCode] = useState(false)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [countdown, setCountdown] = useState(0)
  const [agreedToTerms, setAgreedToTerms] = useState(false)

  // 点击外部关闭
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (modalRef.current && !modalRef.current.contains(event.target as Node)) {
        onClose()
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [onClose])

  // ESC 键关闭
  useEffect(() => {
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose()
      }
    }

    document.addEventListener('keydown', handleEscape)
    return () => {
      document.removeEventListener('keydown', handleEscape)
    }
  }, [onClose])

  // 发送验证码
  const handleSendCode = async () => {
    if (!email.trim()) {
      setError(t('auth.error_email_required'))
      return
    }

    setSendingCode(true)
    setError('')
    setMessage('')

    try {
      const response = await authApi.sendCode(email, 'login')
      if (response.success) {
        setMessage(t('auth.success_code_sent'))
        // 开始倒计时
        let count = 60
        setCountdown(count)
        const timer = setInterval(() => {
          count--
          setCountdown(count)
          if (count <= 0) {
            clearInterval(timer)
          }
        }, 1000)
      } else {
        setError(response.message)
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || t('auth.error_send_failed'))
    } finally {
      setSendingCode(false)
    }
  }

  // 处理登录/注册
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setMessage('')

    if (!email.trim()) {
      setError(t('auth.error_email_required'))
      return
    }

    // 验证协议同意
    if (!agreedToTerms) {
      setError(t('auth.agreement_required'))
      return
    }

    setLoading(true)

    try {
      // 验证码登录
      if (!code.trim()) {
        setError(t('auth.error_code_required'))
        setLoading(false)
        return
      }
      const data = await authApi.loginWithCode(email, code)
      // 保存 token
      localStorage.setItem('auth_token', data.access_token)
      localStorage.setItem('user_info', JSON.stringify(data.user))

      // 如果有待处理的主题，保存到 sessionStorage
      if (pendingTopic) {
        sessionStorage.setItem('pending_topic', pendingTopic)
      }

      onLoginSuccess()
    } catch (err: any) {
      setError(err.response?.data?.detail || t('auth.error_operation_failed'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-modal-overlay">
      <div className="login-modal" ref={modalRef}>
        <button className="login-modal-close" onClick={onClose}>×</button>

        <div className="login-modal-header">
          <span className="login-modal-icon">🔬</span>
          <h2 className="login-modal-title">{t('auth.login')} / {t('auth.register')}</h2>
          <p className="login-modal-subtitle">{t('auth.welcome')}</p>
        </div>

        <form className="login-modal-form" onSubmit={handleSubmit}>
          {/* 邮箱输入 */}
          <div className="modal-form-group">
            <label htmlFor="modal-email">{t('auth.email')}</label>
            <input
              id="modal-email"
              type="email"
              className="modal-form-input"
              placeholder={t('auth.email_placeholder')}
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={loading}
            />
          </div>

          {/* 验证码输入 */}
          <div className="modal-form-group">
            <label htmlFor="modal-code">{t('auth.code')}</label>
            <div className="modal-code-input-group">
              <input
                id="modal-code"
                type="text"
                className="modal-form-input modal-code-input"
                placeholder={t('auth.code_placeholder')}
                value={code}
                onChange={(e) => setCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                disabled={loading}
                maxLength={6}
              />
              <button
                type="button"
                className="modal-send-code-button"
                onClick={handleSendCode}
                disabled={sendingCode || countdown > 0 || loading}
              >
                {countdown > 0 ? `${countdown} ${t('auth.seconds')}` : sendingCode ? t('auth.sending') : t('auth.send_code')}
              </button>
            </div>
          </div>

          {/* 协议同意复选框 */}
          <div className="modal-form-group modal-agreement-group">
            <label className="modal-agreement-label">
              <input
                type="checkbox"
                className="modal-agreement-checkbox"
                checked={agreedToTerms}
                onChange={(e) => setAgreedToTerms(e.target.checked)}
                disabled={loading}
              />
              <span className="modal-agreement-text">
                {t('auth.agreement_label')}{' '}
                <a href="/terms-and-conditions" target="_blank" rel="noopener noreferrer" className="modal-agreement-link">
                  {t('home.footer.terms')}
                </a>,{' '}
                <a href="/privacy-policy" target="_blank" rel="noopener noreferrer" className="modal-agreement-link">
                  {t('home.footer.privacy')}
                </a>{' '}
                {t('auth.agreement_and')}{' '}
                <a href="/refund-policy" target="_blank" rel="noopener noreferrer" className="modal-agreement-link">
                  {t('home.footer.refund')}
                </a>
              </span>
            </label>
          </div>

          {/* 错误提示 */}
          {error && (
            <div className="modal-form-error">
              {error}
            </div>
          )}

          {/* 成功提示 */}
          {message && (
            <div className="modal-form-success">
              {message}
            </div>
          )}

          {/* 提交按钮 */}
          <button
            type="submit"
            className="modal-submit-button"
            disabled={loading}
          >
            {loading ? t('auth.processing') : t('auth.login_button')}
          </button>
        </form>

        {/* 第三方登录预留区域 */}
        <div className="login-modal-divider">
          <span className="divider-text">{t('auth.other_methods')}</span>
        </div>
        <div className="login-modal-oauth">
          <button className="oauth-btn oauth-wechat" disabled title={t('auth.wechat_coming')}>
            <svg viewBox="0 0 24 24" width="22" height="22" fill="currentColor">
              <path d="M8.691 2.188C3.891 2.188 0 5.476 0 9.53c0 2.212 1.17 4.203 3.002 5.55a.59.59 0 0 1 .213.665l-.39 1.48c-.019.07-.048.141-.048.213 0 .163.13.295.29.295a.326.326 0 0 0 .167-.054l1.903-1.114a.864.864 0 0 1 .717-.098 10.16 10.16 0 0 0 2.837.403c.276 0 .543-.027.811-.05-.857-2.578.157-4.972 1.932-6.446 1.703-1.415 3.882-1.98 5.853-1.838-.576-3.583-4.196-6.348-8.596-6.348zM5.785 5.991c.642 0 1.162.529 1.162 1.18a1.17 1.17 0 0 1-1.162 1.178A1.17 1.17 0 0 1 4.623 7.17c0-.651.52-1.18 1.162-1.18zm5.813 0c.642 0 1.162.529 1.162 1.18a1.17 1.17 0 0 1-1.162 1.178 1.17 1.17 0 0 1-1.162-1.178c0-.651.52-1.18 1.162-1.18zm3.97 3.258c-3.792 0-6.874 2.549-6.874 5.693 0 3.145 3.082 5.694 6.874 5.694a8.18 8.18 0 0 0 2.262-.322.67.67 0 0 1 .555.076l1.474.863a.252.252 0 0 0 .13.042.227.227 0 0 0 .225-.229c0-.055-.023-.11-.038-.165l-.301-1.146a.458.458 0 0 1 .166-.516C21.138 18.189 22.168 16.517 22.168 14.942c0-3.144-3.082-5.693-6.874-5.693h.274zm-2.17 2.908c.497 0 .9.41.9.914a.907.907 0 0 1-.9.913.907.907 0 0 1-.9-.913c0-.504.403-.914.9-.914zm4.34 0c.497 0 .9.41.9.914a.907.907 0 0 1-.9.913.907.907 0 0 1-.9-.913c0-.504.403-.914.9-.914z"/>
            </svg>
          </button>
          <button className="oauth-btn oauth-alipay" disabled title={t('auth.alipay_coming')}>
            <svg viewBox="0 0 24 24" width="22" height="22" fill="currentColor">
              <path d="M21.088.001H2.912C1.305.001 0 1.306 0 2.914V21.09c0 1.607 1.305 2.912 2.912 2.912h18.176c1.607 0 2.912-1.305 2.912-2.912V2.914c0-1.608-1.305-2.913-2.912-2.913zM7.13 18.293c-2.826 0-4.81-1.956-4.81-4.078 0-1.473.748-2.668 2.122-3.432.84-.454 1.988-.862 3.483-1.223-.652-1.276-1.178-2.48-1.178-3.582 0-1.73 1.256-3.096 3.23-3.096 1.703 0 2.97 1.178 2.97 2.786 0 1.472-1.06 2.548-2.544 3.398.574.916 1.238 1.845 1.935 2.72.76-.498 1.406-1.082 1.926-1.748l1.4 1.6c-.678.82-1.468 1.528-2.342 2.12 1.088 1.118 2.196 2.006 3.116 2.578l-1.168 2.104c-1.144-.804-2.308-1.84-3.408-3.026-1.114 1.456-2.612 2.68-4.692 2.68zm.396-2.17c1.32 0 2.38-.702 3.244-1.844a24.5 24.5 0 01-2.8-3.568c-1.63.444-2.532.92-2.98 1.396-.452.48-.612 1.02-.612 1.56 0 1.318 1.106 2.456 3.148 2.456z"/>
            </svg>
          </button>
        </div>
      </div>
    </div>
  )
}
