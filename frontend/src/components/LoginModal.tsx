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
  const isSubmitting = useRef(false)
  const [loginSuccess, setLoginSuccess] = useState(false)

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
      const response = await authApi.sendCode(email, 'login', 'zh')
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

    // 防抖：阻止重复提交
    if (isSubmitting.current || loading) return
    isSubmitting.current = true

    setError('')
    setMessage('')

    if (!email.trim()) {
      setError(t('auth.error_email_required'))
      isSubmitting.current = false
      return
    }

    // 验证协议同意
    if (!agreedToTerms) {
      setError(t('auth.agreement_required'))
      isSubmitting.current = false
      return
    }

    setLoading(true)

    try {
      // 验证码登录
      if (!code.trim()) {
        setError(t('auth.error_code_required'))
        setLoading(false)
        isSubmitting.current = false
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

      // 显示登录成功反馈
      setLoginSuccess(true)
      setTimeout(() => {
        onLoginSuccess()
      }, 800)
    } catch (err: any) {
      setError(err.response?.data?.detail || t('auth.error_operation_failed'))
      setLoading(false)
      isSubmitting.current = false
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
            className={`modal-submit-button ${loginSuccess ? 'modal-submit-success' : ''}`}
            disabled={loading || loginSuccess}
          >
            {loginSuccess ? t('common.success') : loading ? t('auth.processing') : t('auth.login_button')}
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
            <svg viewBox="0 0 1024 1024" width="24" height="24">
              <rect width="1024" height="1024" rx="192" fill="#1677FF"/>
              <path fill="#fff" d="M308.8 546.7c0 17.8-14.4 32.2-32.2 32.2s-32.2-14.4-32.2-32.2 14.4-32.2 32.2-32.2 32.2 14.4 32.2 32.2zm149.2 0c0 17.8-14.4 32.2-32.2 32.2s-32.2-14.4-32.2-32.2 14.4-32.2 32.2-32.2 32.2 14.4 32.2 32.2z"/>
              <path fill="#fff" d="M228.8 452.8h-25.2v132.5h25.2c37.8 0 68.5-29.7 68.5-66.3s-30.7-66.2-68.5-66.2zm0 0h-25.2v132.5h25.2c37.8 0 68.5-29.7 68.5-66.3s-30.7-66.2-68.5-66.2z" opacity="0"/>
              <path fill="#fff" d="M512 78C271.5 78 76 273.5 76 514s195.5 436 436 436 436-195.5 436-436S752.5 78 512 78zm222.8 490.4c-46 22.7-98.3 40.2-154.3 51.8 14.2 39.8 33 76.2 55.5 107.2 6.2 8.6 17.3 12 27.3 8.3l4.3-1.6c12.5-4.6 18.2-19.2 12-30.8-12.8-23.6-23.5-49-31.8-75.8 46.4-9.2 89.8-22.2 128.5-38.7 14.5-6.2 21.4-23 15.2-37.4-6.2-14.5-23-21.4-37.4-15.2-32.3 13.7-68 24.8-106.3 33 16.7-56.2 25.7-117 25.7-180.2H548v-62h122.5c8.3 0 15-6.7 15-15s-6.7-15-15-15H548v-62c0-8.3-6.7-15-15-15s-15 6.7-15 15v62H395.5c-8.3 0-15 6.7-15 15s6.7 15 15 15H518v62H375.2c0 63.2 9 124 25.7 180.2-38.3-8.2-74-19.3-106.3-33-14.5-6.2-31.2.7-37.4 15.2-6.2 14.5.7 31.2 15.2 37.4 38.7 16.5 82.2 29.5 128.5 38.7-8.3 26.8-19 52.2-31.8 75.8-6.2 11.6-.5 26.2 12 30.8l4.3 1.6c10 3.7 21.1.3 27.3-8.3 22.5-31 41.3-67.4 55.5-107.2-56-11.6-108.3-29.1-154.3-51.8z"/>
            </svg>
          </button>
        </div>
      </div>
    </div>
  )
}
