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
  recordId?: number  // For unlock mode
}

// Pricing aligned with backend PADDLE_PRICING
const PADDLE_PRICING = {
  single: {
    type: 'single',
    name: 'Starter',
    price: 9.99,
    credits: 6,
    currency: 'USD',
    features: [
      '6 review credits',
      'DOI-verifiable citations',
      'Standard citation formats',
      'Word export',
    ]
  },
  semester: {
    type: 'semester',
    name: 'Semester Pro',
    price: 24.99,
    credits: 18,
    currency: 'USD',
    features: [
      '18 review credits',
      'Priority processing',
      'Advanced citation formats',
      'All Starter features',
      'Valid for 6 months'
    ]
  },
  yearly: {
    type: 'yearly',
    name: 'Annual Premium',
    price: 49.99,
    credits: 50,
    currency: 'USD',
    features: [
      '50 review credits',
      'Priority processing',
      'Advanced citation formats',
      'All Semester features',
      'Valid for 12 months'
    ]
  },
  unlock: {
    type: 'unlock',
    name: 'Unlock Single Export',
    price: 9.99,
    credits: 0,
    currency: 'USD',
    features: [
      'Unlock Word export for this review',
      'No watermark',
      'Professional formatting',
      'Instant access'
    ]
  }
}

const IS_DEV = window.location.hostname === 'localhost' ||
  window.location.hostname === '127.0.0.1'

// Extend Window type for Paddle.js
declare global {
  interface Window {
    Paddle?: any
  }
}

export function PaddlePaymentModal({ onClose, onPaymentSuccess, planType, recordId }: PaddlePaymentModalProps) {
  const { t } = useTranslation()
  const [, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [paymentStatus, setPaymentStatus] = useState<'idle' | 'creating' | 'waiting' | 'paid' | 'failed'>('idle')
  const [orderNo, setOrderNo] = useState('')
  const [checkoutUrl, setCheckoutUrl] = useState('')

  const plan = PADDLE_PRICING[planType as keyof typeof PADDLE_PRICING] || PADDLE_PRICING.single
  const isUnlockMode = planType === 'unlock' && recordId !== undefined

  // Esc to close
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', handleEscape)
    return () => document.removeEventListener('keydown', handleEscape)
  }, [onClose])

  // Create Paddle payment session
  const createPayment = useCallback(async () => {
    setLoading(true)
    setError('')
    setPaymentStatus('creating')

    try {
      let result

      if (isUnlockMode && recordId !== undefined) {
        result = await api.createPaddleUnlock(recordId)
      } else {
        result = await api.createPaddleSubscription(planType)
      }

      setOrderNo(result.order_no)
      setCheckoutUrl(result.checkout_url)
      setPaymentStatus('waiting')

      if (!IS_DEV && result.checkout_url) {
        // Production: open Paddle checkout
        if (window.Paddle) {
          window.Paddle.Checkout.open({
            url: result.checkout_url,
          })
        } else {
          // Fallback: redirect to checkout URL
          window.open(result.checkout_url, '_blank')
        }
      } else if (IS_DEV) {
        // Development: auto-trigger mock payment
        setTimeout(async () => {
          try {
            await fetch(result.checkout_url.replace(window.location.origin, ''))
          } catch (err) {
            console.error('Mock payment failed:', err)
          }
        }, 3000)
      }
    } catch (err: any) {
      const msg = err?.response?.data?.detail || err?.message || t('payment.failed')
      setError(msg)
      setPaymentStatus('failed')
    } finally {
      setLoading(false)
    }
  }, [planType, isUnlockMode, recordId, t])

  // Poll payment status
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
        // Continue polling
      }
    }, 3000)

    return () => clearInterval(pollingInterval)
  }, [orderNo, paymentStatus, onPaymentSuccess, plan.credits])

  // Auto-create order on mount
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
        <button className="payment-modal-close" onClick={handleClose} aria-label="Close">&times;</button>

        {/* Header: Plan Information */}
        <div className="payment-modal-header">
          <span className="payment-modal-icon">💳</span>
          <h2 className="payment-modal-title">{t('payment.buy', { name: plan.name })}</h2>
          <p className="payment-modal-price">
            <span className="amount">${plan.price}</span>
            <span className="currency"> {plan.currency}</span>
          </p>
          {plan.credits > 0 && (
            <p className="payment-modal-credits">{t('payment.credits_info', { credits: plan.credits })}</p>
          )}
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
              <p>{t('payment.creating')}</p>
            </div>
          )}

          {paymentStatus === 'waiting' && (
            <div className="payment-modal-payment">
              {IS_DEV ? (
                <div className="payment-modal-devpay">
                  <p className="payment-dev-hint">
                    {t('payment.auto_payment')}
                  </p>
                  <p className="payment-dev-order">{t('payment.order_no', { orderNo })}</p>
                  <div className="payment-modal-polling">
                    <div className="payment-spinner small"></div>
                    <p>{t('payment.processing')}</p>
                  </div>
                </div>
              ) : (
                <div className="payment-modal-paddle">
                  <p className="payment-pay-hint">{t('payment.pay_hint')}</p>
                  <p className="payment-order-info">
                    {t('payment.order_info', { orderNo, amount: plan.price })}
                  </p>
                  {checkoutUrl && !window.Paddle && (
                    <a
                      href={checkoutUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="payment-modal-btn primary"
                    >
                      {t('payment.pay_now')}
                    </a>
                  )}
                  <div className="payment-modal-polling">
                    <div className="payment-spinner small"></div>
                    <p>{t('payment.waiting')}</p>
                  </div>
                </div>
              )}
              <button className="payment-cancel-btn" onClick={handleClose}>
                {t('payment.cancel')}
              </button>
            </div>
          )}

          {paymentStatus === 'paid' && (
            <div className="payment-modal-success">
              <span className="payment-success-icon">✓</span>
              <h3>{t('payment.success_title')}</h3>
              <p>
                {isUnlockMode
                  ? t('payment.success_unlock')
                  : t('payment.success_credits', { credits: plan.credits })
                }
              </p>
              <button className="payment-modal-btn" onClick={handleClose}>{t('common.done')}</button>
            </div>
          )}

          {paymentStatus === 'failed' && error && (
            <div className="payment-modal-error">
              <p className="payment-error-text">{error}</p>
              <button className="payment-modal-btn" onClick={handleRetry}>{t('payment.retry')}</button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
