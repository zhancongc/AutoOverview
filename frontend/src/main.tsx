import React, { useState, useEffect } from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route, Navigate, useSearchParams, useLocation } from 'react-router-dom'
import App from './App'
import { SimpleApp } from './components/SimpleApp'
import { SimpleAppInternational } from './components/SimpleAppInternational'
import { ReviewPage } from './components/ReviewPage'
import { ReviewPageInternational } from './components/ReviewPageInternational'
import { SearchPapersPage } from './components/SearchPapersPage'
import { ProfilePage } from './components/ProfilePage'
import { ProfilePageInternational } from './components/ProfilePageInternational'
import { DavidPage } from './components/DavidPage'
import { TermsAndConditionsPage } from './components/TermsAndConditionsPage'
import { PrivacyPolicyPage } from './components/PrivacyPolicyPage'
import { RefundPolicyPage } from './components/RefundPolicyPage'
import { TermsAndConditionsPageChinese } from './components/TermsAndConditionsPageChinese'
import { PrivacyPolicyPageChinese } from './components/PrivacyPolicyPageChinese'
import { RefundPolicyPageChinese } from './components/RefundPolicyPageChinese'
import { AcademicIntegrityPage } from './components/AcademicIntegrityPage'
import { AcademicIntegrityPageChinese } from './components/AcademicIntegrityPageChinese'
import { ComparisonMatrixPage } from './components/ComparisonMatrixPage'
import { GenerateReviewPage } from './components/GenerateReviewPage'
import ErrorBoundary from './ErrorBoundary'
import { FeedbackFloatingButton } from './components/FeedbackFloatingButton'
import { api } from './api'
import './i18n' // 导入 i18n 配置
import './index.css'

// 检测是否为英文版
const isEnglishVersion = typeof __BUILD_VERSION__ !== 'undefined' && __BUILD_VERSION__ === 'english'

// 设置根元素版本标识，用于 CSS 作用域隔离
document.documentElement.classList.add(isEnglishVersion ? 'intl' : 'zh')

function BackToTop() {
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    const onScroll = () => setVisible(window.scrollY > 300)
    window.addEventListener('scroll', onScroll)
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  return (
    <button
      className="back-to-top"
      style={{ opacity: visible ? 1 : 0, pointerEvents: visible ? 'auto' : 'none' }}
      onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
    >
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
        <path d="M10 4L4 10h4v6h4v-6h4L10 4z" fill="currentColor"/>
      </svg>
    </button>
  )
}

function AppContent() {
  const location = useLocation()
  const showFeedback = !['/review', '/comparison-matrix'].some(path => location.pathname.startsWith(path))

  return (
    <>
      <Routes>
        <Route path="/login" element={isEnglishVersion ? <SimpleAppInternational autoShowLogin /> : <SimpleApp autoShowLogin />} />
        <Route path="/" element={isEnglishVersion ? <SimpleAppInternational /> : <SimpleApp />} />
        <Route path="/search-papers" element={<SearchPapersPage />} />
        <Route path="/profile" element={
          <ProtectedRoute>
            {isEnglishVersion ? <ProfilePageInternational /> : <ProfilePage />}
          </ProtectedRoute>
        } />
        <Route path="/review" element={
          <ReviewRoute>
            {isEnglishVersion ? <ReviewPageInternational /> : <ReviewPage />}
          </ReviewRoute>
        } />
        <Route path="/david" element={
          <DavidRoute>
            <DavidPage />
          </DavidRoute>
        } />
        <Route path="/jade" element={
          <JadeRoute>
            <App />
          </JadeRoute>
        } />
        <Route path="/terms-and-conditions" element={isEnglishVersion ? <TermsAndConditionsPage /> : <TermsAndConditionsPageChinese />} />
        <Route path="/privacy-policy" element={isEnglishVersion ? <PrivacyPolicyPage /> : <PrivacyPolicyPageChinese />} />
        <Route path="/refund-policy" element={isEnglishVersion ? <RefundPolicyPage /> : <RefundPolicyPageChinese />} />
        <Route path="/academic-integrity" element={isEnglishVersion ? <AcademicIntegrityPage /> : <AcademicIntegrityPageChinese />} />
        <Route path="/comparison-matrix" element={<ComparisonMatrixPage />} />
        <Route path="/generate" element={<GenerateReviewPage />} />
        <Route path="/payment/success" element={<PaymentRedirect />} />
        <Route path="/payment/cancel" element={<PaymentRedirect />} />
      </Routes>
      <BackToTop />
      {showFeedback && <FeedbackFloatingButton />}
    </>
  )
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <ErrorBoundary>
    <BrowserRouter>
      <AppContent />
    </BrowserRouter>
  </ErrorBoundary>,
)

// 受保护的路由组件（用于需要登录的页面）
function ProtectedRoute({ children }: { children: React.ReactElement }) {
  const token = localStorage.getItem('auth_token')
  if (!token) {
    return <Navigate to="/login" replace state={{ from: { pathname: window.location.pathname } }} />
  }
  return <>{children}</>
}

// Review 路由守卫（案例白名单免登录，其余需登录）
function ReviewRoute({ children }: { children: React.ReactElement }) {
  const [searchParams] = useSearchParams()
  const taskId = searchParams.get('task_id')
  const [demoIds, setDemoIds] = useState<Set<string> | null>(null)

  useEffect(() => {
    fetch('/api/health')
      .then(res => res.json())
      .then(data => {
        const ids = (data.demo_task_ids || []) as string[]
        const idsEn = (data.demo_task_ids_en || []) as string[]
        setDemoIds(new Set([...ids, ...idsEn]))
      })
      .catch(() => setDemoIds(new Set()))
  }, [])

  // 等待白名单加载
  if (demoIds === null) return null

  // 案例展示，免登录
  if (taskId && demoIds.has(taskId)) {
    return children
  }

  // 其余需要登录
  const token = localStorage.getItem('auth_token')
  if (!token) {
    return <Navigate to="/login" replace state={{ from: { pathname: window.location.pathname + window.location.search } }} />
  }

  return children
}

// Jade 路由守卫（白名单用户才能访问）
function JadeRoute({ children }: { children: React.ReactElement }) {
  const [checking, setChecking] = useState(true)
  const [allowed, setAllowed] = useState(false)

  useEffect(() => {
    api.checkJadeAccess().then(data => {
      setAllowed(data.allowed)
      setChecking(false)
    }).catch(() => {
      setAllowed(false)
      setChecking(false)
    })
  }, [])

  if (checking) return null
  if (!allowed) return <Navigate to="/" replace />
  return children
}

// 支付回调跳转页（PayPal return URL 兜底）
function PaymentRedirect() {
  const location = useLocation()
  const isSuccess = location.pathname === '/payment/success'

  useEffect(() => {
    const timer = setTimeout(() => {
      window.location.href = '/'
    }, 3000)
    return () => clearTimeout(timer)
  }, [])

  return (
    <div style={{
      display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
      height: '100vh', fontFamily: '-apple-system, BlinkMacSystemFont, sans-serif', color: '#333',
    }}>
      <span style={{ fontSize: 48, marginBottom: 16 }}>{isSuccess ? '✓' : '✕'}</span>
      <h2 style={{ margin: '0 0 8px' }}>
        {isSuccess ? 'Payment Successful!' : 'Payment Cancelled'}
      </h2>
      <p style={{ color: '#666', margin: 0 }}>
        Redirecting to homepage...
      </p>
    </div>
  )
}

// David 路由守卫（只有白名单用户才能访问）
function DavidRoute({ children }: { children: React.ReactElement }) {
  const [checking, setChecking] = useState(true)
  const [allowed, setAllowed] = useState(false)

  useEffect(() => {
    const checkAccess = async () => {
      try {
        const token = localStorage.getItem('auth_token')
        const headers: Record<string, string> = {}
        if (token) headers.Authorization = `Bearer ${token}`

        const res = await fetch('/api/david/access', { headers })
        const data = await res.json()
        setAllowed(data.allowed || false)
      } catch {
        setAllowed(false)
      } finally {
        setChecking(false)
      }
    }

    checkAccess()
  }, [])

  if (checking) return null
  if (!allowed) return <Navigate to="/" replace />
  return children
}
