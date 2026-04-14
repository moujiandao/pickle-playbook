import { useState, useEffect, useCallback, useRef } from 'react'
import { screenToCourt } from '../lib/courtProjection'
import { COURT_W, NET_Y, COURT_L, SVG_W, SVG_H } from '../constants'

export function useDrag(setPlayers, setBall) {
  const [dragging, setDragging] = useState(null)
  const svgContainerRef = useRef(null)

  const getSvgPt = useCallback((e) => {
    const container = svgContainerRef.current
    if (!container) return null
    const svg = container.querySelector('svg')
    if (!svg) return null
    const r = svg.getBoundingClientRect()
    return {
      x: (e.clientX - r.left) * (SVG_W / r.width),
      y: (e.clientY - r.top) * (SVG_H / r.height),
    }
  }, [])

  const onPointerDown = useCallback((e, id) => {
    e.preventDefault()
    e.stopPropagation()
    setDragging(id)
  }, [])

  useEffect(() => {
    if (!dragging) return

    const move = (e) => {
      e.preventDefault()
      const ce = e.touches ? e.touches[0] : e
      const pt = getSvgPt(ce)
      if (!pt) return
      const [ftX, ftY] = screenToCourt(pt.x, pt.y)

      if (dragging === 'ball') {
        setBall((b) => ({
          ...b,
          x: Math.max(0, Math.min(COURT_W, ftX)),
          // Ball restricted to your side (y >= NET_Y)
          y: Math.max(NET_Y, Math.min(COURT_L, ftY)),
        }))
      } else {
        const isOpp = dragging.startsWith('opp')
        const isLeft = dragging.includes('left')
        const cy = isOpp
          ? Math.max(0, Math.min(NET_Y, ftY))
          : Math.max(NET_Y, Math.min(COURT_L, ftY))
        const cx = Math.max(0, Math.min(COURT_W, ftX))

        setPlayers((p) => {
          const updated = { ...p, [dragging]: { x: cx, y: cy } }
          const pfx = isOpp ? 'opp' : 'my'
          // Maintain minimum 1ft gap between left/right players on the same team
          if (isLeft && updated[`${pfx}_left`].x > updated[`${pfx}_right`].x - 1) {
            updated[`${pfx}_left`] = { ...updated[`${pfx}_left`], x: updated[`${pfx}_right`].x - 1 }
          }
          if (!isLeft && updated[`${pfx}_right`].x < updated[`${pfx}_left`].x + 1) {
            updated[`${pfx}_right`] = { ...updated[`${pfx}_right`], x: updated[`${pfx}_left`].x + 1 }
          }
          return updated
        })
      }
    }

    const up = () => setDragging(null)

    window.addEventListener('pointermove', move, { passive: false })
    window.addEventListener('pointerup', up)
    window.addEventListener('touchmove', move, { passive: false })
    window.addEventListener('touchend', up)
    return () => {
      window.removeEventListener('pointermove', move)
      window.removeEventListener('pointerup', up)
      window.removeEventListener('touchmove', move)
      window.removeEventListener('touchend', up)
    }
  }, [dragging, getSvgPt, setBall, setPlayers])

  return { dragging, onPointerDown, svgContainerRef }
}
