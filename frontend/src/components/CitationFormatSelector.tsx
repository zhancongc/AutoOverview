import { useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import './CitationFormatSelector.css'

type CitationFormat = 'ieee' | 'apa' | 'mla' | 'gb_t_7714'

interface CitationFormatSelectorProps {
  currentFormat: CitationFormat
  onFormatChange: (format: CitationFormat) => void
  disabled?: boolean
}

const FORMAT_KEYS: CitationFormat[] = ['ieee', 'apa', 'mla', 'gb_t_7714']

export function CitationFormatSelector({
  currentFormat,
  onFormatChange,
  disabled = false
}: CitationFormatSelectorProps) {
  const { t } = useTranslation()
  const formats = useMemo(() => FORMAT_KEYS, [])

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
