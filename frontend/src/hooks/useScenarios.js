import { useState, useEffect } from 'react'

const STORAGE_KEY = 'pickle-scenarios'

function load() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : []
  } catch {
    return []
  }
}

function persist(scenarios) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(scenarios))
  } catch {}
}

export function useScenarios() {
  const [scenarios, setScenarios] = useState([])

  useEffect(() => {
    setScenarios(load())
  }, [])

  function saveScenario(entry) {
    setScenarios((prev) => {
      const updated = [entry, ...prev].slice(0, 50)
      persist(updated)
      return updated
    })
  }

  function deleteScenario(id) {
    setScenarios((prev) => {
      const updated = prev.filter((s) => s.id !== id)
      persist(updated)
      return updated
    })
  }

  return { scenarios, saveScenario, deleteScenario }
}
