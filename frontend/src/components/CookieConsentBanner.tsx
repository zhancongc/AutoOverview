/**
 * Cookie Consent Banner - GDPR Compliant
 * Shows a banner for users to accept/reject cookies
 */
import { useState, useEffect } from 'react'
import './CookieConsentBanner.css'

export function CookieConsentBanner() {
  const [showBanner, setShowBanner] = useState(false)
  const [isMinimized, setIsMinimized] = useState(false)

  useEffect(() => {
    // Check if user has already made a choice
    const consent = localStorage.getItem('cookie_consent')
    if (!consent) {
      // Show banner after a short delay
      const timer = setTimeout(() => setShowBanner(true), 1000)
      return () => clearTimeout(timer)
    }
  }, [])

  const handleAccept = () => {
    localStorage.setItem('cookie_consent', 'accepted')
    localStorage.setItem('cookie_consent_date', new Date().toISOString())
    setShowBanner(false)
  }

  const handleReject = () => {
    localStorage.setItem('cookie_consent', 'rejected')
    localStorage.setItem('cookie_consent_date', new Date().toISOString())
    setShowBanner(false)
  }

  const handleMinimize = () => {
    setIsMinimized(true)
  }

  const handleRestore = () => {
    setIsMinimized(false)
  }

  if (!showBanner) return null

  if (isMinimized) {
    return (
      <div className="cookie-banner-minimized" onClick={handleRestore}>
        <span className="cookie-icon">🍪</span>
        <span className="cookie-text">Privacy Settings</span>
      </div>
    )
  }

  return (
    <div className="cookie-banner-overlay">
      <div className="cookie-banner">
        <div className="cookie-header">
          <span className="cookie-icon">🍪</span>
          <h3 className="cookie-title">Cookie & Privacy Preferences</h3>
          <button className="cookie-minimize" onClick={handleMinimize}>
            −
          </button>
        </div>

        <div className="cookie-content">
          <p className="cookie-description">
            We use cookies to enhance your experience, analyze usage, and assist in our marketing efforts.
            By clicking "Accept All", you consent to our use of cookies.
          </p>

          <div className="cookie-info">
            <h4 className="cookie-info-title">Essential Cookies (Required)</h4>
            <p className="cookie-info-desc">
              These cookies are necessary for the website to function and cannot be switched off.
              They include authentication and security features.
            </p>
          </div>

          <div className="cookie-info">
            <h4 className="cookie-info-title">Analytics & Performance</h4>
            <p className="cookie-info-desc">
              These cookies help us understand how users interact with our website so we can improve
              performance and user experience.
            </p>
          </div>
        </div>

        <div className="cookie-actions">
          <button className="cookie-button cookie-button-reject" onClick={handleReject}>
            Reject Non-Essential
          </button>
          <button className="cookie-button cookie-button-accept" onClick={handleAccept}>
            Accept All
          </button>
        </div>

        <div className="cookie-footer">
          <a href="/privacy-policy" target="_blank" rel="noopener noreferrer" className="cookie-link">
            Privacy Policy
          </a>
          <span className="cookie-divider">•</span>
          <a href="/terms-and-conditions" target="_blank" rel="noopener noreferrer" className="cookie-link">
            Terms & Conditions
          </a>
        </div>
      </div>
    </div>
  )
}
