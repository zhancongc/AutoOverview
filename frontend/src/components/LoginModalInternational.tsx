/**
 * Login Modal Component - International Version
 * Email verification login for international market
 */
import { useState, useEffect, useRef } from 'react'
import { useTranslation } from 'react-i18next'
import { authApi } from '../authApi'
import './LoginModalInternational.css'

interface LoginModalInternationalProps {
  onClose: () => void
  onLoginSuccess: () => void
  pendingTopic?: string
}

export function LoginModalInternational({ onClose, onLoginSuccess, pendingTopic }: LoginModalInternationalProps) {
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
  const [showTermsHint, setShowTermsHint] = useState(false)
  const [shakeCheckbox, setShakeCheckbox] = useState(false)
  const isSubmitting = useRef(false)
  const [loginSuccess, setLoginSuccess] = useState(false)

  // Click outside to close
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

  // ESC key to close
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

  // Send verification code
  const handleSendCode = async () => {
    if (!email.trim()) {
      setError(t('auth.error_email_required'))
      return
    }

    setSendingCode(true)
    setError('')
    setMessage('')

    try {
      const response = await authApi.sendCode(email, 'login', 'en')
      if (response.success) {
        setMessage(t('auth.success_code_sent'))
        // Start countdown
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

  // Handle login/register
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    // Debounce: prevent double clicks
    if (isSubmitting.current || loading) return
    isSubmitting.current = true

    setError('')
    setMessage('')

    if (!email.trim()) {
      setError(t('auth.error_email_required'))
      isSubmitting.current = false
      return
    }

    // Validate agreement - show friendly hint instead of error
    if (!agreedToTerms) {
      setShowTermsHint(true)
      setShakeCheckbox(true)
      setTimeout(() => setShakeCheckbox(false), 500)
      isSubmitting.current = false
      return
    }

    setLoading(true)

    try {
      // Verification code login
      if (!code.trim()) {
        setError(t('auth.error_code_required'))
        setLoading(false)
        isSubmitting.current = false
        return
      }
      const data = await authApi.loginWithCode(email, code)
      // Save token
      localStorage.setItem('auth_token', data.access_token)
      localStorage.setItem('user_info', JSON.stringify(data.user))

      // Save pending topic to sessionStorage
      if (pendingTopic) {
        sessionStorage.setItem('pending_topic', pendingTopic)
      }

      // Show success feedback before closing
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
    <div className="login-modal-overlay-international">
      <div className="login-modal-international" ref={modalRef}>
        <button className="login-modal-close" onClick={onClose}>×</button>

        <div className="login-modal-header">
          <span className="login-modal-icon">🔬</span>
          <h2 className="login-modal-title">{t('auth.login')} / {t('auth.register')}</h2>
          <p className="login-modal-subtitle">{t('auth.welcome')}</p>
        </div>

        <form className="login-modal-form" onSubmit={handleSubmit}>
          {/* Email input */}
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
              autoComplete="email"
            />
          </div>

          {/* Verification code input */}
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
                autoComplete="one-time-code"
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

          {/* Agreement checkbox */}
          <div className={`modal-form-group modal-agreement-group ${shakeCheckbox ? 'shake-animation' : ''}`}>
            <label className="modal-agreement-label">
              <input
                type="checkbox"
                className="modal-agreement-checkbox"
                checked={agreedToTerms}
                onChange={(e) => {
                  setAgreedToTerms(e.target.checked)
                  if (e.target.checked) {
                    setShowTermsHint(false)
                  }
                }}
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

            {/* Friendly hint for agreement */}
            {showTermsHint && (
              <div className="modal-agreement-hint">
                <span className="hint-icon">💡</span>
                <span className="hint-text">Please agree to the Terms & Conditions to continue</span>
              </div>
            )}
          </div>

          {/* Error message */}
          {error && (
            <div className="modal-form-error">
              {error}
            </div>
          )}

          {/* Success message */}
          {message && (
            <div className="modal-form-success">
              {message}
            </div>
          )}

          {/* Submit button */}
          <button
            type="submit"
            className={`modal-submit-button ${loginSuccess ? 'modal-submit-success' : ''}`}
            disabled={loading || loginSuccess}
          >
            {loginSuccess ? t('common.success') : loading ? t('auth.processing') : t('auth.login_button')}
          </button>
        </form>

        {/* Divider */}
        <div className="login-modal-divider">
          <span className="divider-text">{t('auth.other_methods')}</span>
        </div>

        {/* OAuth buttons */}
        <div className="login-modal-oauth">
          <button className="oauth-btn oauth-google" onClick={() => { window.location.href = '/api/auth/google/authorize' }} title={t('auth.google_login')}>
            <svg viewBox="0 0 24 24" width="22" height="22">
              <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
              <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
              <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
              <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
            </svg>
          </button>
          {/* Apple 登录 - 暂未接入 */}
          {/*
          <button className="oauth-btn oauth-apple" disabled title={t('auth.apple_coming')}>
            <svg viewBox="0 0 24 24" width="22" height="22" fill="currentColor">
              <path d="M18.71 19.5c-.83 1.24-1.71 2.45-3.05 2.47-1.34.03-1.77-.79-3.29-.79-1.53 0-2 .77-3.27.82-1.31.05-2.3-1.32-3.14-2.53C4.25 17 2.94 12.45 4.7 9.39c.87-1.52 2.43-2.48 4.12-2.51 1.28-.02 2.5.87 3.29.87.78 0 2.26-1.07 3.8-.91.65.03 2.47.26 3.64 1.98-.09.06-2.17 1.28-2.15 3.81.03 3.02 2.65 4.03 2.68 4.04-.03.07-.42 1.44-1.38 2.83M13 3.5c.73-.83 1.94-1.46 2.94-1.5.13 1.17-.34 2.35-1.04 3.19-.69.85-1.83 1.51-2.95 1.42-.15-1.15.41-2.35 1.05-3.11z"/>
            </svg>
          </button>
          */}
        </div>
      </div>
    </div>
  )
}
