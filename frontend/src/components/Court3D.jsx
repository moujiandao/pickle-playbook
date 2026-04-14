import { forwardRef } from 'react'
import StickFigure from './StickFigure'
import BallIcon from './BallIcon'
import { courtToScreen, quadPath, courtLine, depthScale } from '../lib/courtProjection'
import { COURT_W, KITCHEN, NET_Y, SVG_W, SVG_H, COLORS } from '../constants'

const COURT_LINES = [
  [0, 0, COURT_W, 0],
  [COURT_W, 0, COURT_W, 44],
  [0, 44, COURT_W, 44],
  [0, 0, 0, 44],
  [0, NET_Y - KITCHEN, COURT_W, NET_Y - KITCHEN],
  [0, NET_Y + KITCHEN, COURT_W, NET_Y + KITCHEN],
  [COURT_W / 2, 0, COURT_W / 2, NET_Y - KITCHEN],
  [COURT_W / 2, NET_Y + KITCHEN, COURT_W / 2, 44],
]

const Court3D = forwardRef(function Court3D({ players, ball, mySide, dragging, onPointerDown }, ref) {
  const entities = [
    ...Object.entries(players).map(([k, p]) => ({ type: 'player', key: k, ...p })),
    { type: 'ball', key: 'ball', ...ball },
  ].sort((a, b) => b.y - a.y)

  const [netLX, netLY] = courtToScreen(-0.3, NET_Y)
  const [netRX] = courtToScreen(COURT_W + 0.3, NET_Y)
  // Net visual height per pickleball-court-rendering skill: 8-15 units
  // representing 34 inches (exaggerated for visibility).
  const netH = 12
  // Post height sticks up slightly above the mesh (36" vs 34").
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

        {COURT_LINES.map((c, i) => {
          const l = courtLine(...c)
          return <line key={i} {...l} stroke={COLORS.lines} strokeWidth={2.6} strokeLinecap="square" />
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
        {/* Net body */}
        <rect
          x={netLX}
          y={netLY - netH}
          width={netRX - netLX}
          height={netH}
          fill={COLORS.netFill}
          stroke={COLORS.netFill}
          strokeWidth={1}
        />
        {/* Top tape of the net */}
        <line
          x1={netLX}
          y1={netLY - netH}
          x2={netRX}
          y2={netLY - netH}
          stroke="#ffffff"
          strokeWidth={1.5}
          opacity={0.9}
        />
        {/* Vertical mesh */}
        {Array.from({ length: 30 }).map((_, i) => {
          const f = (i + 1) / 31
          const mx = netLX + (netRX - netLX) * f
          return (
            <line
              key={`v${i}`}
              x1={mx}
              y1={netLY - netH + 1}
              x2={mx}
              y2={netLY - 1}
              stroke={COLORS.netMesh}
              strokeWidth={0.6}
            />
          )
        })}
        {/* Horizontal mesh */}
        {Array.from({ length: 4 }).map((_, i) => {
          const f = (i + 1) / 5
          const my = netLY - netH + (netH - 2) * f
          return (
            <line
              key={`h${i}`}
              x1={netLX + 1}
              y1={my}
              x2={netRX - 1}
              y2={my}
              stroke={COLORS.netMesh}
              strokeWidth={0.5}
            />
          )
        })}

        {entities.map((ent) => {
          const [sx, sy] = courtToScreen(ent.x, ent.y)
          const scale = depthScale(ent.y)
          if (ent.type === 'ball') {
            return (
              <g key="ball" onPointerDown={(e) => onPointerDown(e, 'ball')}>
                <BallIcon cx={sx} cy={sy} isSelected={dragging === 'ball'} scale={scale} />
              </g>
            )
          }
          const isOpp = ent.key.startsWith('opp')
          const isLeft = ent.key.includes('left')
          const color = isOpp ? COLORS.oppTeam : COLORS.myTeam
          const label = isOpp ? (isLeft ? 'OPP L' : 'OPP R') : isLeft ? 'YOU L' : 'YOU R'
          const isMe =
            (mySide === 'left' && ent.key === 'my_left') || (mySide === 'right' && ent.key === 'my_right')
          return (
            <g key={ent.key} onPointerDown={(e) => onPointerDown(e, ent.key)}>
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
