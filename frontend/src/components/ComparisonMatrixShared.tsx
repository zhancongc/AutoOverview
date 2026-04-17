import { useState, useEffect } from 'react'
import { api } from '../api'
import { isLoggedIn as checkLoggedIn } from '../authApi'

export interface Paper {
  id: string
  title: string
  authors: string[]
  year: number | null
  cited_by_count: number
  abstract: string | null
  doi: string | null
  is_english: boolean
}

export interface Statistics {
  total: number
  recent_count: number
  recent_ratio: number
  english_count: number
  english_ratio: number
  total_citations: number
  avg_citations: number
}

export interface ComparisonMatrixData {
  topic: string
  comparison_matrix: string
  statistics: {
    papers_used: number
    total_time_seconds: number
    generated_at: string
  }
  papers: Paper[]
}

export type TabType = 'matrix' | 'references'
export type SortMode = 'citations' | 'year'
export type CombinedPhase = 'idle' | 'searching' | 'generating_matrix'

export function useMatrixAuth() {
  const [isChineseSite, setIsChineseSite] = useState(false)
  const [loggedIn, setLoggedIn] = useState(checkLoggedIn())
  const [showLoginModal, setShowLoginModal] = useState(false)
  const [credits, setCredits] = useState<number>(0)

  useEffect(() => {
    setIsChineseSite(!document.documentElement.classList.contains('intl'))
  }, [])

  useEffect(() => {
    if (checkLoggedIn()) {
      api.getCredits().then(data => {
        setCredits(data.credits)
      }).catch(() => {})
    }
  }, [])

  const handleLoginSuccess = () => {
    setShowLoginModal(false)
    setLoggedIn(true)
    api.getCredits().then(data => {
      setCredits(data.credits)
    }).catch(() => {})
  }

  return {
    isChineseSite, loggedIn, showLoginModal, credits,
    setShowLoginModal, handleLoginSuccess, setCredits
  }
}
