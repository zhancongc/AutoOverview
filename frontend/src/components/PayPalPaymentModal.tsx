/**
 * PayPal Payment Modal for International Markets (Default)
 * Supports USD payments via PayPal JavaScript SDK
 * Falls back to Paddle if needed
 */
import { useState, useEffect, useCallback, useRef } from 'react'
import { useTranslation } from 'react-i18next'
import { api } from '../api'
import './PaymentModal.css'

interface PayPalPaymentModalProps {
  onClose: () => void
  onPaymentSuccess: (addedCredits?: number) => void
  planType: string
  recordId?: number  // For unlock mode
  showPaddleOption?: boolean  // Allow switching to Paddle
  onSwitchToPaddle?: () => void
}

// Pricing aligned with backend PAYPAL_PRICING (and Paddle)
const PAYPAL_PRICING = {
  single: {
    type: 'single',
    name: 'Starter',
    price: 5.99,
    credits: 1,
    currency: 'USD',
    features: [
      '1 complete literature review',
      'DOI-verifiable citations',
      'Standard citation formats',
      'Word export',
    ]
  },
  semester: {
    type: 'semester',
    name: 'Semester Pro',
    price: 27.99,
    credits: 12,
    currency: 'USD',
    features: [
      '12 review credits',
      'Priority processing',
      'Advanced citation formats',
      'All Starter features',
      'Valid for 6 months'
    ]
  },
  yearly: {
    type: 'yearly',
    name: 'Annual Premium',
    price: 64.99,
    credits: 36,
    currency: 'USD',
    features: [
      '36 review credits',
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

// Extend Window type for PayPal
declare global {
  interface Window {
    paypal?: any
  }
}

export function PayPalPaymentModal({
  onClose,
  onPaymentSuccess,
  planType,
  recordId,
  showPaddleOption = true,
  onSwitchToPaddle
}: PayPalPaymentModalProps) {
  const { t } = useTranslation()
  const [, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [paymentStatus, setPaymentStatus] = useState<'idle' | 'creating' | 'waiting' | 'paid' | 'failed'>('idle')
  const [orderNo, setOrderNo] = useState('')
  const [paypalOrderId, setPayPalOrderId] = useState('')
  const [paypalSdkLoaded, setPaypalSdkLoaded] = useState(false)
  const paypalButtonContainerRef = useRef<HTMLDivElement>(null)

  const plan = PAYPAL_PRICING[planType as keyof typeof PAYPAL_PRICING] || PAYPAL_PRICING.single
  const isUnlockMode = planType === 'unlock' && recordId !== undefined

  // Load PayPal SDK
  useEffect(() => {
    const loadPayPalSdk = async () => {
      try {
        // Get PayPal config from backend
        const configResponse = await fetch('/api/paypal/config')
        const configData = await configResponse.json()
        const clientId = configData.client_id || 'test'

        if (window.paypal) {
          setPaypalSdkLoaded(true)
          return
        }

        // Load PayPal SDK
        const script = document.createElement('script')
        script.src = `https://www.paypal.com/sdk/js?client-id=${clientId}&currency=USD`
        script.onload = () => {
          setPaypalSdkLoaded(true)
        }
        script.onerror = () => {
          setError('Failed to load PayPal. Please try again or use Paddle.')
        }
        document.body.appendChild(script)
      } catch (err) {
        console.error('Failed to get PayPal config:', err)
        setError('Failed to initialize payment. Please try again or use Paddle.')
      }
    }

    loadPayPalSdk()
  }, [])

  // Render PayPal buttons when SDK is loaded and we have an order ID
  useEffect(() => {
    if (!paypalSdkLoaded || !paypalOrderId || !paypalButtonContainerRef.current || paymentStatus !== 'waiting') {
      return
    }

    // Clear previous buttons
    if (paypalButtonContainerRef.current) {
      paypalButtonContainerRef.current.innerHTML = ''
    }

    if (window.paypal) {
      window.paypal.Buttons({
        createOrder: () => {
          return paypalOrderId
        },
        onApprove: async () => {
          setPaymentStatus('creating')
          try {
            // Capture the order on the server
            await api.capturePayPalOrder(paypalOrderId)
            setPaymentStatus('paid')
            onPaymentSuccess(plan.credits)
          } catch (err: any) {
            const msg = err?.response?.data?.detail || err?.message || t('payment.failed')
            setError(msg)
            setPaymentStatus('failed')
          }
        },
        onError: (err: any) => {
          console.error('PayPal error:', err)
          setError('PayPal payment failed. Please try again or use Paddle.')
          setPaymentStatus('failed')
        },
        onCancel: () => {
          setError('Payment cancelled. You can try again or use Paddle.')
          setPaymentStatus('failed')
        }
      }).render(paypalButtonContainerRef.current)
    }
  }, [paypalSdkLoaded, paypalOrderId, paymentStatus, plan.credits, onPaymentSuccess, t])

  // Esc to close
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', handleEscape)
    return () => document.removeEventListener('keydown', handleEscape)
  }, [onClose])

  // Create PayPal payment session
  const createPayment = useCallback(async () => {
    setLoading(true)
    setError('')
    setPaymentStatus('creating')

    try {
      let result

      if (isUnlockMode && recordId !== undefined) {
        result = await api.createPayPalUnlock(recordId)
      } else {
        result = await api.createPayPalSubscription(planType)
      }

      setOrderNo(result.order_no)
      setPayPalOrderId(result.paypal_order_id)
      setPaymentStatus('waiting')

      if (IS_DEV) {
        // Development: auto-trigger mock payment after delay
        setTimeout(async () => {
          try {
            setPaymentStatus('creating')
            await api.capturePayPalOrder(result.paypal_order_id)
            setPaymentStatus('paid')
            onPaymentSuccess(plan.credits)
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
  }, [planType, isUnlockMode, recordId, t, onPaymentSuccess, plan.credits])

  // Poll payment status
  useEffect(() => {
    if (!orderNo || paymentStatus === 'paid') return

    const pollingInterval = setInterval(async () => {
      try {
        const result = await api.queryPayPalSubscription(orderNo)
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
                <div className="payment-modal-paypal">
                  <p className="payment-pay-hint">{t('payment.pay_hint')}</p>
                  <p className="payment-order-info">
                    {t('payment.order_info', { orderNo, amount: plan.price })}
                  </p>
                  <div ref={paypalButtonContainerRef} className="paypal-button-container"></div>
                  <div className="payment-modal-polling">
                    <div className="payment-spinner small"></div>
                    <p>{t('payment.waiting')}</p>
                  </div>
                </div>
              )}

              {/* Alternative payment option: Paddle */}
              {showPaddleOption && onSwitchToPaddle && (
                <div className="payment-alternative">
                  <p className="payment-alternative-text">Or pay with:</p>
                  <button
                    className="payment-alternative-btn"
                    onClick={(e) => {
                      e.stopPropagation()
                      onSwitchToPaddle()
                    }}
                  >
                    Credit Card (Paddle)
                  </button>
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
              <div className="payment-error-actions">
                <button className="payment-modal-btn" onClick={handleRetry}>{t('payment.retry')}</button>
                {showPaddleOption && onSwitchToPaddle && (
                  <button className="payment-modal-btn secondary" onClick={onSwitchToPaddle}>
                    Use Paddle instead
                  </button>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
