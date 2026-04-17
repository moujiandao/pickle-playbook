import { forwardRef } from 'react'
import StickFigure from './StickFigure'
import BallIcon from './BallIcon'
import { courtToScreen, quadPath, courtLine, depthScale } from '../lib/courtProjection'
import {
  COURT_W,
  KITCHEN,
  NET_Y,
  SVG_W,
  SVG_H,
  COLORS,
  NET_PIXEL_HEIGHT,
  BALL_RADIUS,
} from '../constants'

// First 4 entries = court perimeter (drawn 2x thicker).
// Remaining = interior lines (kitchen + center service lines).
const COURT_PERIMETER = [
  [0, 0, COURT_W, 0],
  [COURT_W, 0, COURT_W, 44],
  [0, 44, COURT_W, 44],
  [0, 0, 0, 44],
]
const COURT_INTERIOR = [
  [0, NET_Y - KITCHEN, COURT_W, NET_Y - KITCHEN],
  [0, NET_Y + KITCHEN, COURT_W, NET_Y + KITCHEN],
  [COURT_W / 2, 0, COURT_W / 2, NET_Y - KITCHEN],
  [COURT_W / 2, NET_Y + KITCHEN, COURT_W / 2, 44],
]

const BALL_ELEVATION_MULT = { low: 1, mid: 2, high: 4 }

const Court3D = forwardRef(function Court3D({ players, ball, mySide, dragging, onPointerDown }, ref) {
  const entities = [
    ...Object.entries(players).map(([k, p]) => ({ type: 'player', key: k, ...p })),
    { type: 'ball', key: 'ball', ...ball },
  ].sort((a, b) => b.y - a.y)

  const [netLX, netLY] = courtToScreen(-0.3, NET_Y)
  const [netRX] = courtToScreen(COURT_W + 0.3, NET_Y)
  // Size the net so its top sits just below where a 'mid'-height ball would
  // float when it's at the net line. Uses the ball's depth scale at NET_Y so
  // the ratio stays consistent if NET_PIXEL_HEIGHT or BALL_RADIUS changes.
  const netScale = depthScale(NET_Y)
  const midBallBottom = BALL_ELEVATION_MULT.mid * NET_PIXEL_HEIGHT * netScale - BALL_RADIUS * netScale
  const netH = Math.max(12, midBallBottom - 3)
  // Post height sticks up slightly above the mesh.
  const postTopY = netLY - netH - 3

  return (
    <div
      ref={ref}
      style={{ borderRadius: 10, overflow: 'hidden', boxShadow: '0 8px 40px rgba(0,0,0,0.6)' }}
    >
      <svg
        width={SVG_W}
        height={SVG_H}
        viewBox={`0 0 ${SVG_W} ${SVG_H}`}
        style={{ display: 'block', width: '100%', height: 'auto', touchAction: 'none', background: COLORS.outOfBounds }}
      >
        <path d={quadPath(0, 0, COURT_W, 44)} fill={COLORS.courtMain} />

        {/* 4 service box corners (kitchen strip keeps the main court color) */}
        <path d={quadPath(0, 0, COURT_W / 2, NET_Y - KITCHEN)} fill={COLORS.serviceBox} />
        <path d={quadPath(COURT_W / 2, 0, COURT_W, NET_Y - KITCHEN)} fill={COLORS.serviceBox} />
        <path d={quadPath(0, NET_Y + KITCHEN, COURT_W / 2, 44)} fill={COLORS.serviceBox} />
        <path d={quadPath(COURT_W / 2, NET_Y + KITCHEN, COURT_W, 44)} fill={COLORS.serviceBox} />

        {COURT_INTERIOR.map((c, i) => {
          const l = courtLine(...c)
          return <line key={`int${i}`} {...l} stroke={COLORS.lines} strokeWidth={2.6} strokeLinecap="square" />
        })}
        {COURT_PERIMETER.map((c, i) => {
          const l = courtLine(...c)
          return <line key={`per${i}`} {...l} stroke={COLORS.lines} strokeWidth={5.2} strokeLinecap="square" />
        })}

        {/* Left post */}
        <line
          x1={netLX}
          y1={postTopY}
          x2={netLX}
          y2={netLY + 4}
          stroke={COLORS.netFill}
          strokeWidth={3}
          strokeLinecap="square"
        />
        {/* Right post */}
        <line
          x1={netRX}
          y1={postTopY}
          x2={netRX}
          y2={netLY + 4}
          stroke={COLORS.netFill}
          strokeWidth={3}
          strokeLinecap="square"
        />
        {/* Top tape of the net */}
        <line
          x1={netLX}
          y1={netLY - netH}
          x2={netRX}
          y2={netLY - netH}
          stroke="#000000"
          strokeWidth={2.5}
        />
        {/* Bottom band of the net */}
        <line
          x1={netLX}
          y1={netLY}
          x2={netRX}
          y2={netLY}
          stroke="#FFFFFF"
          strokeWidth={2.5}
        />
        {/* Vertical mesh — transparent cells, thicker lines */}
        {Array.from({ length: 90 }).map((_, i) => {
          const f = (i + 1) / 91
          const mx = netLX + (netRX - netLX) * f
          return (
            <line
              key={`v${i}`}
              x1={mx}
              y1={netLY - netH + 1}
              x2={mx}
              y2={netLY - 1}
              stroke={COLORS.netMesh}
              strokeWidth={2}
            />
          )
        })}
        {/* Horizontal mesh — transparent cells, thicker lines */}
        {Array.from({ length: 12 }).map((_, i) => {
          const f = (i + 1) / 13
          const my = netLY - netH + (netH - 2) * f
          return (
            <line
              key={`h${i}`}
              x1={netLX + 1}
              y1={my}
              x2={netRX - 1}
              y2={my}
              stroke={COLORS.netMesh}
              strokeWidth={2}
            />
          )
        })}

        {entities.map((ent) => {
          const [sx, sy] = courtToScreen(ent.x, ent.y)
          const scale = depthScale(ent.y)
          if (ent.type === 'ball') {
            const elevation = (BALL_ELEVATION_MULT[ent.height] ?? 0) * NET_PIXEL_HEIGHT * scale
            return (
              <g key="ball" onPointerDown={(e) => onPointerDown(e, 'ball')}>
                <BallIcon
                  cx={sx}
                  cy={sy}
                  elevation={elevation}
                  spin={ent.spin}
                  isSelected={dragging === 'ball'}
                  scale={scale}
                />
              </g>
            )
          }
          const isOpp = ent.key.startsWith('opp')
          const isLeft = ent.key.includes('left')
          const color = isOpp ? COLORS.oppTeam : COLORS.myTeam
          const label = isOpp ? null : isLeft ? 'Leftside Player' : 'Rightside Player'
          const isMe =
            (mySide === 'left' && ent.key === 'my_left') || (mySide === 'right' && ent.key === 'my_right')
          // Reach ring: diameter = 1/3 of the court's screen width at this depth.
          const [courtLx] = courtToScreen(0, ent.y)
          const [courtRx] = courtToScreen(COURT_W, ent.y)
          const reachR = (courtRx - courtLx) / 6
          return (
            <g key={ent.key} onPointerDown={(e) => onPointerDown(e, ent.key)}>
              {isMe && (
                <circle
                  cx={sx}
                  cy={sy}
                  r={reachR}
                  fill="none"
                  stroke="rgba(255,255,255,0.35)"
                  strokeWidth={1.5}
                  strokeDasharray="8,5"
                  pointerEvents="none"
                />
              )}
              <StickFigure
                cx={sx}
                cy={sy}
                color={color}
                label={label}
                isSelected={dragging === ent.key}
                isMe={isMe}
                scale={scale}
              />
            </g>
          )
        })}
      </svg>
    </div>
  )
})

export default Court3D
