// CorrectionControls — thumbs feedback + inline rewrite editor per recommendation card.
// One submission per recommendation; controls lock after submit.

import { useState, useEffect } from 'react'

const API_URL = import.meta.env.VITE_API_URL ?? ''

function recToText(rec) {
  const shots = rec.rally
    .map((s) => `${s.shot}. [${s.who}] ${s.action}`)
    .join('\n')
  return `${rec.name}\n${rec.why}\n\n${shots}`
}

// Minimal inline toast — fades out after 2.5s
function Toast({ message, type }) {
  const base = 'text-xs px-3 py-1.5 rounded-full font-medium transition-opacity'
  const color =
    type === 'success'
      ? 'bg-emerald-900/60 text-emerald-300 border border-emerald-700'
      : 'bg-red-900/60 text-red-300 border border-red-700'
  return <span className={`${base} ${color}`}>{message}</span>
}

// Thumbs icon — outline by default, solid when active
function ThumbsIcon({ direction, active, hovered }) {
  // Unicode approach: simple, no dep
  const solid = direction === 'up' ? '👍' : '👎'
  const outline = direction === 'up' ? '👍' : '👎'
  // Use opacity/scale to distinguish states
  const style = active
    ? 'opacity-100 scale-110'
    : hovered
    ? 'opacity-80'
    : 'opacity-40 grayscale'
  return (
    <span
      className={`text-base leading-none transition-all duration-150 ${style} select-none`}
      aria-hidden
    >
      {active ? solid : outline}
    </span>
  )
}

export default function CorrectionControls({ recommendation, gameState }) {
  // mode: idle | editing | submitted
  const [mode, setMode] = useState('idle')
  const [selected, setSelected] = useState(null) // 'thumbs_up' | 'thumbs_down'
  const [editText, setEditText] = useState('')
  const [toast, setToast] = useState(null) // { message, type }
  const [hoveredBtn, setHoveredBtn] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  // Auto-clear toast
  useEffect(() => {
    if (!toast) return
    const id = setTimeout(() => setToast(null), 2500)
    return () => clearTimeout(id)
  }, [toast])

  const disabled = mode === 'submitted'

  async function postCorrection(feedbackType, correctedText) {
    setSubmitting(true)
    try {
      const res = await fetch(`${API_URL}/api/correct`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          game_state: gameState,
          original_recommendation: recommendation,
          corrected_recommendation: correctedText ?? null,
          feedback_type: feedbackType,
        }),
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      setMode('submitted')
      setToast({ message: 'Feedback saved', type: 'success' })
    } catch {
      setToast({ message: 'Submit failed — try again', type: 'error' })
    } finally {
      setSubmitting(false)
    }
  }

  function handleThumb(type) {
    if (disabled || submitting) return
    setSelected(type)
    postCorrection(type, null)
  }

  function handleEditOpen() {
    if (disabled) return
    setEditText(recToText(recommendation))
    setMode('editing')
  }

  function handleEditCancel() {
    setMode('idle')
    setEditText('')
  }

  function handleEditSubmit() {
    if (!editText.trim() || submitting) return
    postCorrection('rewrite', editText.trim())
  }

  return (
    <div className="mt-3 pt-3 border-t border-slate-700/50">
      {mode !== 'editing' && (
        <div className="flex items-center gap-2 flex-wrap">
          {/* Thumbs up */}
          <button
            onClick={() => handleThumb('thumbs_up')}
            onMouseEnter={() => setHoveredBtn('up')}
            onMouseLeave={() => setHoveredBtn(null)}
            disabled={disabled || submitting}
            className="flex items-center gap-1 px-2 py-1 rounded-md text-xs bg-slate-700/50 hover:bg-slate-600/50 disabled:cursor-not-allowed disabled:opacity-50 transition-colors"
            title="Good recommendation"
          >
            <ThumbsIcon
              direction="up"
              active={selected === 'thumbs_up'}
              hovered={hoveredBtn === 'up' && !disabled}
            />
            <span className={`text-slate-400 ${selected === 'thumbs_up' ? 'text-emerald-400' : ''}`}>
              Good
            </span>
          </button>

          {/* Thumbs down */}
          <button
            onClick={() => handleThumb('thumbs_down')}
            onMouseEnter={() => setHoveredBtn('down')}
            onMouseLeave={() => setHoveredBtn(null)}
            disabled={disabled || submitting}
            className="flex items-center gap-1 px-2 py-1 rounded-md text-xs bg-slate-700/50 hover:bg-slate-600/50 disabled:cursor-not-allowed disabled:opacity-50 transition-colors"
            title="Poor recommendation"
          >
            <ThumbsIcon
              direction="down"
              active={selected === 'thumbs_down'}
              hovered={hoveredBtn === 'down' && !disabled}
            />
            <span className={`text-slate-400 ${selected === 'thumbs_down' ? 'text-red-400' : ''}`}>
              Off
            </span>
          </button>

          {/* Edit / rewrite */}
          {!disabled && (
            <button
              onClick={handleEditOpen}
              disabled={disabled || submitting}
              className="flex items-center gap-1 px-2 py-1 rounded-md text-xs bg-slate-700/50 hover:bg-slate-600/50 disabled:cursor-not-allowed disabled:opacity-50 transition-colors text-slate-400"
              title="Rewrite this recommendation"
            >
              <svg
                className="w-3 h-3"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                aria-hidden
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                />
              </svg>
              Edit
            </button>
          )}

          {toast && <Toast message={toast.message} type={toast.type} />}
        </div>
      )}

      {mode === 'editing' && (
        <div className="space-y-2">
          <textarea
            value={editText}
            onChange={(e) => setEditText(e.target.value)}
            rows={6}
            className="w-full text-xs bg-slate-900/60 border border-slate-600 rounded-md px-3 py-2 text-slate-200 placeholder-slate-500 resize-y focus:outline-none focus:border-slate-400 font-mono leading-relaxed"
            placeholder="Rewrite the recommendation..."
            autoFocus
          />
          <div className="flex items-center gap-2">
            <button
              onClick={handleEditSubmit}
              disabled={!editText.trim() || submitting}
              className="px-3 py-1 rounded-md text-xs bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium transition-colors"
            >
              {submitting ? 'Saving…' : 'Save'}
            </button>
            <button
              onClick={handleEditCancel}
              disabled={submitting}
              className="px-3 py-1 rounded-md text-xs bg-slate-700 hover:bg-slate-600 disabled:opacity-50 text-slate-300 transition-colors"
            >
              Cancel
            </button>
            {toast && <Toast message={toast.message} type={toast.type} />}
          </div>
        </div>
      )}
    </div>
  )
}
