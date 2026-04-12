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
      const response = await authApi.sendCode(email, 'login')
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
    setError('')
    setMessage('')

    if (!email.trim()) {
      setError(t('auth.error_email_required'))
      return
    }

    // Validate agreement
    if (!agreedToTerms) {
      setError(t('auth.agreement_required'))
      return
    }

    setLoading(true)

    try {
      // Verification code login
      if (!code.trim()) {
        setError(t('auth.error_code_required'))
        setLoading(false)
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

      onLoginSuccess()
    } catch (err: any) {
      setError(err.response?.data?.detail || t('auth.error_operation_failed'))
    } finally {
      setLoading(false)
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
            className={`modal-submit-button ${!agreedToTerms ? 'modal-submit-button-disabled' : ''}`}
            disabled={loading || !agreedToTerms}
          >
            {loading ? t('auth.processing') : t('auth.login_button')}
          </button>
        </form>

        {/* Divider */}
        <div className="login-modal-divider">
          <span className="divider-text">{t('auth.other_methods')}</span>
        </div>

        {/* OAuth buttons */}
        <div className="login-modal-oauth">
          <button className="oauth-btn oauth-google" disabled title={t('auth.wechat_coming')}>
            <svg viewBox="0 0 24 24" width="22" height="22">
              <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
              <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
              <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
              <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
            </svg>
          </button>
          <button className="oauth-btn oauth-apple" disabled title="Coming soon">
            <svg viewBox="0 0 24 24" width="22" height="22" fill="currentColor">
              <path d="M17.05 20.28c-.98.95-2.05.8-3.08.8-1.03 0-2.15-.63-3.08-.63-.92 0-1.92.63-3 .63-1.1 0-2.87-1.39-4.32-1.39-2.33 0-5.8 1.6-5.8 5.1 0 2.68 1.45 4.48 2.92 4.48.75 0 1.07-.38 1.93-.38.86 0 1.2.38 1.93.38 1.48 0 2.72-1.45 4.72-1.45 2.01 0 3.54 1.45 4.32 1.45.8 0 1.07-.38 1.93-.38.87 0 1.43.38 1.93.38 1.48 0 2.63-1.2 4.48-1.2zM15.04 6.5c.6-1.03 1-2.38 1-3.82-1.28.05-2.63.78-3.38 1.05-.77.28-1.63.95-1.63 2.48 0 1.38.73 2.12 1.63 2.48-.6.9-1.03 1.63-1.03 2.93 0 1.63.73 2.38 1.63 2.38.9 0 2.48-1.05 3.38-1.05.9 0 1.63.75 1.63 2.38 0 1.63-.73 2.38-1.63 2.38-.9 0-1.63-.75-1.63-2.38 0-1.63.73-2.38 1.63-2.38.9 0 2.48 1.05 3.38 1.05.9 0 1.63-.75 1.63-2.38 0-1.63-.73-2.38-1.63-2.38-.9 0-1.63.75-1.63 2.38 0 1.63.73 2.38 1.63 2.38.9 0 2.48-1.05 3.38-1.05.9 0 1.63-.75 1.63-2.38 0-1.63-.73-2.38-1.63-2.38z"/>
            </svg>
          </button>
        </div>
      </div>
    </div>
  )
}
