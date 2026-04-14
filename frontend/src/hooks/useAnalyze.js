import { useState } from 'react'

const API_URL = import.meta.env.VITE_API_URL

export function useAnalyze() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [recommendations, setRecommendations] = useState([])

  async function analyze(gameState) {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`${API_URL}/api/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(gameState),
      })
      if (!res.ok) {
        throw new Error(`Server error: ${res.status}`)
      }
      const data = await res.json()
      setRecommendations(data)
      return data
    } catch (err) {
      setError(err.message)
      return []
    } finally {
      setLoading(false)
    }
  }

  return { analyze, loading, error, recommendations }
}
