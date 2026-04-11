/**
 * Paddle Payment Modal for International Markets
 * Supports USD payments via Paddle checkout overlay
 */
import { useState, useEffect, useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import { api } from '../api'
import './PaymentModal.css'

interface PaddlePaymentModalProps {
  onClose: () => void
  onPaymentSuccess: (addedCredits?: number) => void
  planType: string
}

// Paddle pricing in USD (from backend)
const PADDLE_PRICING = {
  single: {
    type: 'single',
    name: 'Single Review',
    price: 5.99,
    credits: 1,
    currency: 'USD',
    features: [
      '1 complete literature review',
      'AI-powered paper search',
      'Standardized citations',
      'Word export',
      'Email delivery'
    ]
  },
  semester: {
    type: 'semester',
    name: 'Semester Pack',
    price: 29.99,
    credits: 10,
    currency: 'USD',
    features: [
      '10 review credits',
      'Priority processing',
      'Advanced citation formats',
      'All Single features',
      'Valid for 6 months'
    ]
  },
  yearly: {
    type: 'yearly',
    name: 'Academic Year Pack',
    price: 79.99,
    credits: 30,
    currency: 'USD',
    features: [
      '30 review credits',
      'Priority processing',
      'Advanced citation formats',
      'All Semester features',
      'Valid for 12 months'
    ]
  }
}

const IS_DEV = window.location.hostname === 'localhost' ||
  window.location.hostname === '127.0.0.1'

export function PaddlePaymentModal({ onClose, onPaymentSuccess, planType }: PaddlePaymentModalProps) {
  const { t } = useTranslation()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [paymentStatus, setPaymentStatus] = useState<'idle' | 'creating' | 'waiting' | 'paid' | 'failed'>('idle')
  const [orderNo, setOrderNo] = useState('')
  const [checkoutUrl, setCheckoutUrl] = useState('')

  const plan = PADDLE_PRICING[planType as keyof typeof PADDLE_PRICING] || PADDLE_PRICING.single

  // Esc 关闭弹窗
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', handleEscape)
    return () => document.removeEventListener('keydown', handleEscape)
  }, [onClose])

  // 创建 Paddle 支付会话
  const createPayment = useCallback(async () => {
    setLoading(true)
    setError('')
    setPaymentStatus('creating')

    try {
      const result = await api.createPaddleSubscription(planType)
      setOrderNo(result.order_no)
      setCheckoutUrl(result.checkout_url)
      setPaymentStatus('waiting')

      // 初始化 Paddle checkout
      if (!IS_DEV && window.Paddle) {
        // 生产环境：使用 Paddle.js 打开 checkout overlay
        // 注意：这里需要根据实际的 Paddle.js API 调整
        // Paddle.Initialize({ ... })
        // Paddle.Checkout.open({ ... })
      } else if (IS_DEV) {
        // 开发环境：自动触发模拟支付
        setTimeout(async () => {
          try {
            // 调用模拟支付回调 URL
            await fetch(result.checkout_url.replace(window.location.origin, ''))
            // 轮询会检测到支付成功
          } catch (err) {
            console.error('模拟支付失败:', err)
          }
        }, 3000)
      }
    } catch (err: any) {
      const msg = err?.response?.data?.detail || err?.message || 'Failed to create payment. Please try again.'
      setError(msg)
      setPaymentStatus('failed')
    } finally {
      setLoading(false)
    }
  }, [planType])

  // 轮询支付状态
  useEffect(() => {
    if (!orderNo || paymentStatus === 'paid') return

    const pollingInterval = setInterval(async () => {
      try {
        const result = await api.queryPaddleSubscription(orderNo)
        if (result.status === 'paid') {
          setPaymentStatus('paid')
          clearInterval(pollingInterval)
          onPaymentSuccess(plan.credits)
        }
      } catch {
        // 忽略轮询错误，继续轮询
      }
    }, 3000)

    return () => clearInterval(pollingInterval)
  }, [orderNo, paymentStatus, onPaymentSuccess, plan.credits])

  // 自动创建订单
  useEffect(() => {
    createPayment()
  }, [createPayment])

  const handleClose = () => {
    onClose()
  }

  const handleRetry = () => {
    createPayment()
  }

  return (
    <div className="payment-modal-overlay" onClick={handleClose}>
      <div className="payment-modal" onClick={e => e.stopPropagation()}>
        <button className="payment-modal-close" onClick={handleClose}>&times;</button>

        {/* Header: Plan Information */}
        <div className="payment-modal-header">
          <span className="payment-modal-icon">💳</span>
          <h2 className="payment-modal-title">Buy {plan.name}</h2>
          <p className="payment-modal-price">
            <span className="amount">${plan.price}</span>
            <span className="currency">{plan.currency}</span>
          </p>
          <p className="payment-modal-credits">{plan.credits} review credits</p>
          <ul className="payment-modal-features">
            {plan.features.map((f: string, i: number) => (
              <li key={i}>✓ {f}</li>
            ))}
          </ul>
        </div>

        {/* Payment Area */}
        <div className="payment-modal-body">
          {paymentStatus === 'creating' && (
            <div className="payment-modal-loading">
              <div className="payment-spinner"></div>
              <p>Creating payment session...</p>
            </div>
          )}

          {paymentStatus === 'waiting' && (
            <div className="payment-modal-payment">
              {IS_DEV ? (
                <div className="payment-modal-devpay">
                  <p className="payment-dev-hint">
                    🔧 Development Mode · Auto-payment in 3 seconds
                  </p>
                  <p className="payment-dev-order">Order: {orderNo}</p>
                  <div className="payment-modal-polling">
                    <div className="payment-spinner small"></div>
                    <p>Processing payment...</p>
                  </div>
                </div>
              ) : (
                <div className="payment-modal-paddle">
                  <p className="payment-pay-hint">Complete your payment securely via Paddle</p>
                  <p className="payment-order-info">Order: {orderNo} · Amount: ${plan.price}</p>
                  <div className="payment-modal-polling">
                    <div className="payment-spinner small"></div>
                    <p>Waiting for payment completion...</p>
                  </div>
                </div>
              )}
              <button className="payment-cancel-btn" onClick={handleClose}>
                Cancel
              </button>
            </div>
          )}

          {paymentStatus === 'paid' && (
            <div className="payment-modal-success">
              <span className="payment-success-icon">✓</span>
              <h3>Payment Successful</h3>
              <p>You now have {plan.credits} review credits</p>
              <button className="payment-modal-btn" onClick={handleClose}>Done</button>
            </div>
          )}

          {paymentStatus === 'failed' && error && (
            <div className="payment-modal-error">
              <p className="payment-error-text">{error}</p>
              <button className="payment-modal-btn" onClick={handleRetry}>Retry</button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
