import { useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import './CitationFormatSelector.css'

export type CitationFormat = 'ieee' | 'apa' | 'mla' | 'gb_t_7714'

interface CitationFormatSelectorProps {
  currentFormat: CitationFormat
  onFormatChange: (format: CitationFormat) => void
  disabled?: boolean
}

const ALL_FORMATS: CitationFormat[] = ['ieee', 'apa', 'mla', 'gb_t_7714']

export function CitationFormatSelector({
  currentFormat,
  onFormatChange,
  disabled = false
}: CitationFormatSelectorProps) {
  const { t } = useTranslation()
  const isChineseSite = !document.documentElement.classList.contains('intl')
  const formats = useMemo(() =>
    isChineseSite ? ALL_FORMATS : ALL_FORMATS.filter(f => f !== 'gb_t_7714'),
    [isChineseSite]
  )

  return (
    <div className="citation-format-selector">
      <label className="format-label">{t('review.citation.title')}：</label>
      <div className="format-options">
        {formats.map((format) => (
          <button
            key={format}
            className={`format-button ${currentFormat === format ? 'active' : ''}`}
            onClick={() => onFormatChange(format)}
            disabled={disabled}
            title={t(`review.citation.${format}`)}
          >
            {format.toUpperCase()}
          </button>
        ))}
      </div>
    </div>
  )
}
