import { useState } from 'react'

const DEFAULT_API_URL = 'http://localhost:8000'

export function useAnalyze() {
  const [result, setResult] = useState(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [error, setError] = useState(null)
  const [warning, setWarning] = useState(null)

  async function analyze(players, ball, mySide, skillLevel) {
    setIsAnalyzing(true)
    setResult(null)
    setError(null)
    setWarning(null)

    try {
      const apiUrl = import.meta.env.VITE_API_URL || DEFAULT_API_URL
      const resp = await fetch(`${apiUrl}/api/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ my_side: mySide, players, ball, skill_level: skillLevel }),
      })
      if (!resp.ok) {
        const detail = await resp.text().catch(() => '')
        throw new Error(`API error ${resp.status}${detail ? `: ${detail}` : ''}`)
      }
      const warningHeader = resp.headers.get('X-Pickle-Warning')
      setWarning(warningHeader)
      setResult(await resp.json())
    } catch (err) {
      setError(err.message)
    } finally {
      setIsAnalyzing(false)
    }
  }

  return { result, setResult, isAnalyzing, error, warning, analyze }
}
