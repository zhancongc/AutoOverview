import React, { useState, useEffect } from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import App from './App'
import { SimpleApp } from './components/SimpleApp'
import { ReviewPage } from './components/ReviewPage'
import { ProfilePage } from './components/ProfilePage'
import { LoginPage } from './components/LoginPage'
import ErrorBoundary from './ErrorBoundary'
import { api } from './api'
import './index.css'

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

ReactDOM.createRoot(document.getElementById('root')!).render(
  <ErrorBoundary>
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/" element={<SimpleApp />} />
        <Route path="/profile" element={
          <ProtectedRoute>
            <ProfilePage />
          </ProtectedRoute>
        } />
        <Route path="/review" element={
          <ProtectedRoute>
            <ReviewPage />
          </ProtectedRoute>
        } />
        <Route path="/jade" element={
          <JadeRoute>
            <App />
          </JadeRoute>
        } />
      </Routes>
      <BackToTop />
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
