import { useState, useEffect } from 'react'

const DEFAULT_API_URL = 'http://localhost:8000'

function apiBase() {
  return import.meta.env.VITE_API_URL || DEFAULT_API_URL
}

async function fetchAll() {
  const r = await fetch(`${apiBase()}/api/scenarios`)
  if (!r.ok) throw new Error(`API ${r.status}`)
  return r.json()
}

async function postOne(name, state) {
  const r = await fetch(`${apiBase()}/api/scenarios`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, state }),
  })
  if (!r.ok) {
    const detail = await r.text().catch(() => '')
    throw new Error(`API ${r.status}${detail ? `: ${detail}` : ''}`)
  }
  return r.json()
}

async function deleteOne(id) {
  const r = await fetch(`${apiBase()}/api/scenarios/${id}`, { method: 'DELETE' })
  if (!r.ok && r.status !== 404) throw new Error(`API ${r.status}`)
}

export function useScenarios() {
  const [scenarios, setScenarios] = useState([])

  useEffect(() => {
    fetchAll()
      .then(setScenarios)
      .catch((err) => {
        console.error('Failed to load scenarios', err)
        setScenarios([])
      })
  }, [])

  async function saveScenario(entry) {
    try {
      const saved = await postOne(entry.name, entry.state)
      setScenarios((prev) => [saved, ...prev].slice(0, 50))
    } catch (err) {
      console.error('Failed to save scenario', err)
    }
  }

  async function deleteScenario(id) {
    try {
      await deleteOne(id)
      setScenarios((prev) => prev.filter((s) => s.id !== id))
    } catch (err) {
      console.error('Failed to delete scenario', err)
    }
  }

  return { scenarios, saveScenario, deleteScenario }
}
