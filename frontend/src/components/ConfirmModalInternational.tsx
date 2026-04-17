/**
 * Confirm Modal Component - International Version
 * Reusable confirmation dialog for international market
 */
import { useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import './ConfirmModalInternational.css'

interface ConfirmModalInternationalProps {
  title?: string
  message: string
  confirmText?: string
  cancelText?: string
  onConfirm: () => void
  onCancel: () => void
  type?: 'info' | 'warning' | 'danger'
}

export function ConfirmModalInternational({
  title,
  message,
  confirmText,
  cancelText,
  onConfirm,
  onCancel,
  type = 'info'
}: ConfirmModalInternationalProps) {
  const { t } = useTranslation()

  // Default texts with i18n fallback
  const defaultTitle = title || t('common.confirm', 'Confirm')
  const defaultConfirmText = confirmText || t('common.confirm', 'Confirm')
  const defaultCancelText = cancelText || t('common.cancel', 'Cancel')

  // Esc key to close
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onCancel()
    }
    document.addEventListener('keydown', handleEscape)
    return () => document.removeEventListener('keydown', handleEscape)
  }, [onCancel])

  const getConfirmButtonClass = () => {
    switch (type) {
      case 'danger':
        return 'confirm-modal-btn confirm-modal-btn-danger'
      case 'warning':
        return 'confirm-modal-btn confirm-modal-btn-warning'
      default:
        return 'confirm-modal-btn confirm-modal-btn-primary'
    }
  }

  return (
    <div className="confirm-modal-overlay-international" onClick={onCancel}>
      <div className="confirm-modal-international" onClick={e => e.stopPropagation()}>
        <button className="confirm-modal-close" onClick={onCancel}>&times;</button>

        <div className="confirm-modal-header">
          <h2 className="confirm-modal-title">{defaultTitle}</h2>
        </div>

        <div className="confirm-modal-body">
          <p className="confirm-modal-message">{message}</p>
        </div>

        <div className="confirm-modal-footer">
          <button className="confirm-modal-btn confirm-modal-btn-cancel" onClick={onCancel}>
            {defaultCancelText}
          </button>
          <button className={getConfirmButtonClass()} onClick={onConfirm}>
            {defaultConfirmText}
          </button>
        </div>
      </div>
    </div>
  )
}
