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

        {/* 第三方登录 */}
        <div className="login-modal-divider">
          <span className="divider-text">{t('auth.other_methods')}</span>
        </div>
        <div className="login-modal-oauth">
          {/* 微信登录 - 暂未接入 */}
          {/*
          <button className="oauth-btn oauth-wechat" disabled title={t('auth.wechat_coming')}>
            <svg viewBox="0 0 24 24" width="22" height="22" fill="currentColor">
              <path d="M8.691 2.188C3.891 2.188 0 5.476 0 9.53c0 2.212 1.17 4.203 3.002 5.55a.59.59 0 0 1 .213.665l-.39 1.48c-.019.07-.048.141-.048.213 0 .163.13.295.29.295a.326.326 0 0 0 .167-.054l1.903-1.114a.864.864 0 0 1 .717-.098 10.16 10.16 0 0 0 2.837.403c.276 0 .543-.027.811-.05-.857-2.578.157-4.972 1.932-6.446 1.703-1.415 3.882-1.98 5.853-1.838-.576-3.583-4.196-6.348-8.596-6.348zM5.785 5.991c.642 0 1.162.529 1.162 1.18a1.17 1.17 0 0 1-1.162 1.178A1.17 1.17 0 0 1 4.623 7.17c0-.651.52-1.18 1.162-1.18zm5.813 0c.642 0 1.162.529 1.162 1.18a1.17 1.17 0 0 1-1.162 1.178 1.17 1.17 0 0 1-1.162-1.178c0-.651.52-1.18 1.162-1.18zm3.97 3.258c-3.792 0-6.874 2.549-6.874 5.693 0 3.145 3.082 5.694 6.874 5.694a8.18 8.18 0 0 0 2.262-.322.67.67 0 0 1 .555.076l1.474.863a.252.252 0 0 0 .13.042.227.227 0 0 0 .225-.229c0-.055-.023-.11-.038-.165l-.301-1.146a.458.458 0 0 1 .166-.516C21.138 18.189 22.168 16.517 22.168 14.942c0-3.144-3.082-5.693-6.874-5.693h.274zm-2.17 2.908c.497 0 .9.41.9.914a.907.907 0 0 1-.9.913.907.907 0 0 1-.9-.913c0-.504.403-.914.9-.914zm4.34 0c.497 0 .9.41.9.914a.907.907 0 0 1-.9.913.907.907 0 0 1-.9-.913c0-.504.403-.914.9-.914z"/>
            </svg>
          </button>
          */}
          <button className="oauth-btn oauth-alipay" onClick={() => { window.location.href = '/api/auth/alipay/authorize' }} title={t('auth.alipay_login')}>
            <svg viewBox="0 0 1024 1024" width="28" height="28">
              <path d="M902.095 652.871l-250.96-84.392s19.287-28.87 39.874-85.472c20.59-56.606 23.539-87.689 23.539-87.689l-162.454-1.339v-55.487l196.739-1.387v-39.227H552.055v-89.29h-96.358v89.294H272.133v39.227l183.564-1.304v59.513h-147.24v31.079h303.064s-3.337 25.223-14.955 56.606c-11.615 31.38-23.58 58.862-23.58 58.862s-142.3-49.804-217.285-49.804c-74.985 0-166.182 30.123-175.024 117.55-8.8 87.383 42.481 134.716 114.728 152.139 72.256 17.513 138.962-0.173 197.04-28.607 58.087-28.391 115.081-92.933 115.081-92.933l292.486 142.041c-11.932 69.3-72.067 119.914-142.387 119.844H266.37c-79.714 0.078-144.392-64.483-144.466-144.194V266.374c-0.074-79.72 64.493-144.399 144.205-144.47h491.519c79.714-0.073 144.396 64.49 144.466 144.203v386.764z m-365.76-48.895s-91.302 115.262-198.879 115.262c-107.623 0-130.218-54.767-130.218-94.155 0-39.34 22.373-82.144 113.943-88.333 91.519-6.18 215.2 67.226 215.2 67.226h-0.047z" fill="#1677FF"/>
            </svg>
          </button>
        </div>
      </div>
    </div>
  )
}
