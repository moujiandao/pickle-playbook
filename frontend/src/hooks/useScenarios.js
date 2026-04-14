import { useState, useEffect } from 'react'

const API_URL = import.meta.env.VITE_API_URL

export function useScenarios() {
  const [scenarios, setScenarios] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  async function loadScenarios() {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`${API_URL}/api/scenarios`)
      if (!res.ok) throw new Error(`Server error: ${res.status}`)
      const data = await res.json()
      setScenarios(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  async function saveScenario(name, gameState) {
    setError(null)
    try {
      const res = await fetch(`${API_URL}/api/scenarios`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, game_state: gameState }),
      })
      if (!res.ok) throw new Error(`Server error: ${res.status}`)
      await loadScenarios()
    } catch (err) {
      setError(err.message)
    }
  }

  async function deleteScenario(id) {
    setError(null)
    try {
      const res = await fetch(`${API_URL}/api/scenarios/${id}`, {
        method: 'DELETE',
      })
      if (!res.ok) throw new Error(`Server error: ${res.status}`)
      setScenarios((prev) => prev.filter((s) => s.id !== id))
    } catch (err) {
      setError(err.message)
    }
  }

  useEffect(() => {
    loadScenarios()
  }, [])

  return { scenarios, saveScenario, deleteScenario, loadScenarios, loading, error }
}
