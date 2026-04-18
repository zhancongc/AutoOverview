import { useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import './ConfirmModal.css'

export type ExportFormat = 'bibtex' | 'ris' | 'word'

interface ExportFormatModalProps {
  selectedFormat: ExportFormat
  onSelectFormat: (format: ExportFormat) => void
  onConfirm: () => void
  onCancel: () => void
  loading?: boolean
}

export function ExportFormatModal({
  selectedFormat,
  onSelectFormat,
  onConfirm,
  onCancel,
  loading = false,
}: ExportFormatModalProps) {
  const { t } = useTranslation()

  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onCancel()
    }
    document.addEventListener('keydown', handleEscape)
    return () => document.removeEventListener('keydown', handleEscape)
  }, [onCancel])

  const formats: { key: ExportFormat; icon: string; desc: string }[] = [
    { key: 'bibtex', icon: '📄', desc: t('search_papers.export.bibtex_desc') },
    { key: 'ris', icon: '📋', desc: t('search_papers.export.ris_desc') },
    { key: 'word', icon: '📝', desc: t('search_papers.export.word_desc') },
  ]

  return (
    <div className="confirm-modal-overlay" onClick={onCancel}>
      <div className="confirm-modal" onClick={e => e.stopPropagation()}>
        <button className="confirm-modal-close" onClick={onCancel}>&times;</button>

        <div className="confirm-modal-header">
          <span className="confirm-modal-icon">📥</span>
          <h2 className="confirm-modal-title">{t('search_papers.export.title')}</h2>
        </div>

        <div className="confirm-modal-body">
          <div className="export-format-options">
            {formats.map(fmt => (
              <label
                key={fmt.key}
                className={`export-format-option ${selectedFormat === fmt.key ? 'active' : ''}`}
              >
                <input
                  type="radio"
                  name="export-format"
                  value={fmt.key}
                  checked={selectedFormat === fmt.key}
                  onChange={() => onSelectFormat(fmt.key)}
                />
                <span className="export-format-icon">{fmt.icon}</span>
                <span className="export-format-info">
                  <span className="export-format-name">{t(`search_papers.export.${fmt.key}`)}</span>
                  <span className="export-format-desc">{fmt.desc}</span>
                </span>
              </label>
            ))}
          </div>
        </div>

        <div className="confirm-modal-footer">
          <button className="confirm-modal-btn confirm-modal-btn-cancel" onClick={onCancel} disabled={loading}>
            {t('search_papers.export.cancel')}
          </button>
          <button className="confirm-modal-btn confirm-modal-btn-primary" onClick={onConfirm} disabled={loading}>
            {loading && <span className="confirm-modal-spinner" />}
            {loading ? t('search_papers.export.exporting', 'Exporting...') : t('search_papers.export.confirm')}
          </button>
        </div>
      </div>
    </div>
  )
}
