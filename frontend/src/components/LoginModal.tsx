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
      </div>
    </div>
  )
}
