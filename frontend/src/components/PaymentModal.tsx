import { useState, useEffect, useRef, useCallback } from 'react'
import { api } from '../api'
import './PaymentModal.css'

interface PaymentModalProps {
  onClose: () => void
  onPaymentSuccess: () => void
  planType: string
}

const PLANS = [
  {
    type: 'single',
    name: '单次体验',
    price: 29.8,
    credits: 1,
    features: [
      '1 篇综述生成额度',
      '在线查看 + PDF 导出',
    ],
  },
  {
    type: 'semester',
    name: '学期包',
    price: 59.8,
    credits: 3,
    features: [
      '3 篇综述生成额度',
      '在线查看 + PDF 导出',
      '低至 ¥19.9/篇',
    ],
  },
  {
    type: 'yearly',
    name: '学年包',
    price: 99.8,
    credits: 6,
    features: [
      '6 篇综述生成额度',
      '在线查看 + PDF 导出',
      '低至 ¥16.6/篇',
    ],
  },
]

const IS_DEV = window.location.hostname === 'localhost' ||
  window.location.hostname === '127.0.0.1'

export function PaymentModal({ onClose, onPaymentSuccess, planType }: PaymentModalProps) {
  const [, setLoading] = useState(false)
  const [orderNo, setOrderNo] = useState('')
  const [payUrl, setPayUrl] = useState('')
  const [error, setError] = useState('')
  const [paymentStatus, setPaymentStatus] = useState<'idle' | 'creating' | 'waiting' | 'paid' | 'failed'>('idle')
  const [amount, setAmount] = useState(0)
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const plan = PLANS.find(p => p.type === planType) || PLANS[0]

  // 轮询支付状态
  useEffect(() => {
    if (!orderNo || paymentStatus === 'paid') return

    pollingRef.current = setInterval(async () => {
      try {
        const result = await api.querySubscription(orderNo)
        if (result.status === 'paid') {
          setPaymentStatus('paid')
          if (pollingRef.current) clearInterval(pollingRef.current)
          onPaymentSuccess()
        }
      } catch {
        // 忽略轮询错误，继续轮询
      }
    }, 3000)

    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current)
    }
  }, [orderNo, paymentStatus, onPaymentSuccess])

  // 创建订单
  const createPayment = useCallback(async () => {
    setLoading(true)
    setError('')
    setPaymentStatus('creating')

    try {
      const result = await api.createSubscription(planType)
      setOrderNo(result.order_no)
      setPayUrl(result.pay_url)
      setAmount(result.amount)
      setPaymentStatus('waiting')
    } catch (err: any) {
      const msg = err?.response?.data?.detail || err?.message || '创建订单失败，请稍后重试'
      setError(msg)
      setPaymentStatus('failed')
    } finally {
      setLoading(false)
    }
  }, [planType])

  // 自动创建订单
  useEffect(() => {
    createPayment()
  }, [createPayment])

  // 开发环境模拟支付
  const handleDevPay = () => {
    if (payUrl) {
      window.location.href = payUrl
    }
  }

  // 生产环境跳转支付宝
  const handleAlipayPay = () => {
    if (payUrl) {
      window.open(payUrl, '_blank')
    }
  }

  // 关闭弹窗前清理轮询
  const handleClose = () => {
    if (pollingRef.current) clearInterval(pollingRef.current)
    onClose()
  }

  return (
    <div className="payment-modal-overlay" onClick={handleClose}>
      <div className="payment-modal" onClick={e => e.stopPropagation()}>
        <button className="payment-modal-close" onClick={handleClose}>&times;</button>

        {/* 头部：套餐信息 */}
        <div className="payment-modal-header">
          <span className="payment-modal-icon">💳</span>
          <h2 className="payment-modal-title">购买 {plan.name}</h2>
          <p className="payment-modal-price">
            <span className="amount">¥{plan.price}</span>
          </p>
          <p className="payment-modal-credits">{plan.credits} 篇综述生成额度</p>
          <ul className="payment-modal-features">
            {plan.features.map((f, i) => (
              <li key={i}>✓ {f}</li>
            ))}
          </ul>
        </div>

        {/* 支付区域 */}
        <div className="payment-modal-body">
          {paymentStatus === 'creating' && (
            <div className="payment-modal-loading">
              <div className="payment-spinner"></div>
              <p>正在创建订单...</p>
            </div>
          )}

          {paymentStatus === 'waiting' && payUrl && (
            <div className="payment-modal-payment">
              {IS_DEV ? (
                <div className="payment-modal-devpay">
                  <p className="payment-dev-hint">🔧 开发环境 · 模拟支付</p>
                  <p className="payment-dev-order">订单号：{orderNo}</p>
                  <button className="payment-modal-btn" onClick={handleDevPay}>
                    模拟支付（¥{amount}）
                  </button>
                  <div className="payment-modal-polling">
                    <div className="payment-spinner small"></div>
                    <p>等待支付结果...</p>
                  </div>
                </div>
              ) : (
                <div className="payment-modal-qrcode">
                  <p className="payment-scan-hint">请使用支付宝扫码完成支付</p>
                  <p className="payment-order-info">订单号：{orderNo} · 金额：¥{amount}</p>
                  <button className="payment-modal-btn" onClick={handleAlipayPay}>
                    打开支付宝支付
                  </button>
                  <div className="payment-modal-polling">
                    <div className="payment-spinner small"></div>
                    <p>支付完成后将自动确认...</p>
                  </div>
                </div>
              )}
              <button className="payment-cancel-btn" onClick={handleClose}>
                取消支付
              </button>
            </div>
          )}

          {paymentStatus === 'paid' && (
            <div className="payment-modal-success">
              <span className="payment-success-icon">✓</span>
              <h3>支付成功</h3>
              <p>已获得 {plan.credits} 篇综述生成额度</p>
              <button className="payment-modal-btn" onClick={handleClose}>完成</button>
            </div>
          )}

          {paymentStatus === 'failed' && error && (
            <div className="payment-modal-error">
              <p className="payment-error-text">{error}</p>
              <button className="payment-modal-btn" onClick={createPayment}>重试</button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
