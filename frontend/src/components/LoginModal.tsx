import { useState, useEffect, useRef } from 'react'
import { authApi } from '../authApi'
import './LoginModal.css'

interface LoginModalProps {
  onClose: () => void
  onLoginSuccess: () => void
  pendingTopic?: string
}

export function LoginModal({ onClose, onLoginSuccess, pendingTopic }: LoginModalProps) {
  const modalRef = useRef<HTMLDivElement>(null)
  const [email, setEmail] = useState('')
  const [code, setCode] = useState('')

  const [loading, setLoading] = useState(false)
  const [sendingCode, setSendingCode] = useState(false)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [countdown, setCountdown] = useState(0)

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
      setError('请输入邮箱')
      return
    }

    setSendingCode(true)
    setError('')
    setMessage('')

    try {
      const response = await authApi.sendCode(email, 'login')
      if (response.success) {
        setMessage(response.message)
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
      setError(err.response?.data?.detail || '发送失败，请稍后重试')
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
      setError('请输入邮箱')
      return
    }

    setLoading(true)

    try {
      // 验证码登录
      if (!code.trim()) {
        setError('请输入验证码')
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
      setError(err.response?.data?.detail || '操作失败，请稍后重试')
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
          <h2 className="login-modal-title">登录 / 注册</h2>
          <p className="login-modal-subtitle">欢迎使用 AutoOverview</p>
        </div>

        <form className="login-modal-form" onSubmit={handleSubmit}>
          {/* 邮箱输入 */}
          <div className="modal-form-group">
            <label htmlFor="modal-email">邮箱</label>
            <input
              id="modal-email"
              type="email"
              className="modal-form-input"
              placeholder="请输入邮箱"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={loading}
            />
          </div>

          {/* 验证码输入 */}
          <div className="modal-form-group">
            <label htmlFor="modal-code">验证码</label>
            <div className="modal-code-input-group">
              <input
                id="modal-code"
                type="text"
                className="modal-form-input modal-code-input"
                placeholder="请输入6位验证码"
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
                {countdown > 0 ? `${countdown}秒` : sendingCode ? '发送中' : '发送验证码'}
              </button>
            </div>
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
            {loading ? '处理中...' : '登录'}
          </button>
        </form>

        {/* 第三方登录预留区域 */}
        <div className="login-modal-divider">
          <span className="divider-text">其他登录方式</span>
        </div>
        <div className="login-modal-oauth">
          <button className="oauth-btn oauth-wechat" disabled title="即将支持微信登录">
            <svg viewBox="0 0 24 24" width="22" height="22" fill="currentColor">
              <path d="M8.691 2.188C3.891 2.188 0 5.476 0 9.53c0 2.212 1.17 4.203 3.002 5.55a.59.59 0 0 1 .213.665l-.39 1.48c-.019.07-.048.141-.048.213 0 .163.13.295.29.295a.326.326 0 0 0 .167-.054l1.903-1.114a.864.864 0 0 1 .717-.098 10.16 10.16 0 0 0 2.837.403c.276 0 .543-.027.811-.05-.857-2.578.157-4.972 1.932-6.446 1.703-1.415 3.882-1.98 5.853-1.838-.576-3.583-4.196-6.348-8.596-6.348zM5.785 5.991c.642 0 1.162.529 1.162 1.18a1.17 1.17 0 0 1-1.162 1.178A1.17 1.17 0 0 1 4.623 7.17c0-.651.52-1.18 1.162-1.18zm5.813 0c.642 0 1.162.529 1.162 1.18a1.17 1.17 0 0 1-1.162 1.178 1.17 1.17 0 0 1-1.162-1.178c0-.651.52-1.18 1.162-1.18zm3.97 3.258c-3.792 0-6.874 2.549-6.874 5.693 0 3.145 3.082 5.694 6.874 5.694a8.18 8.18 0 0 0 2.262-.322.67.67 0 0 1 .555.076l1.474.863a.252.252 0 0 0 .13.042.227.227 0 0 0 .225-.229c0-.055-.023-.11-.038-.165l-.301-1.146a.458.458 0 0 1 .166-.516C21.138 18.189 22.168 16.517 22.168 14.942c0-3.144-3.082-5.693-6.874-5.693h.274zm-2.17 2.908c.497 0 .9.41.9.914a.907.907 0 0 1-.9.913.907.907 0 0 1-.9-.913c0-.504.403-.914.9-.914zm4.34 0c.497 0 .9.41.9.914a.907.907 0 0 1-.9.913.907.907 0 0 1-.9-.913c0-.504.403-.914.9-.914z"/>
            </svg>
          </button>
          <button className="oauth-btn oauth-alipay" disabled title="即将支持支付宝登录">
            <svg viewBox="0 0 24 24" width="22" height="22" fill="currentColor">
              <path d="M21.422 15.358c-1.593-.699-5.354-2.328-5.953-2.583.348-.787.64-1.648.85-2.568H13.2V8.694h4.02V7.452H13.2V4.2h-2.24v3.252H6.94v1.242h4.02v1.513H5.64v1.242h8.398c-.155.607-.364 1.178-.617 1.707-1.365-.506-2.87-.862-3.9-.862-2.533 0-3.872 1.293-3.872 2.833 0 1.89 1.976 3.236 4.678 3.236 1.713 0 3.236-.648 4.48-1.774 1.282.72 4.603 2.143 6.293 2.847V24H0V0h24v15.358h-2.578zM9.002 16.08c-1.713 0-2.701-.677-2.701-1.689 0-.945.878-1.562 2.238-1.562.947 0 2.073.26 3.2.74-.973 1.608-2.016 2.511-2.737 2.511z"/>
            </svg>
          </button>
        </div>
      </div>
    </div>
  )
}
