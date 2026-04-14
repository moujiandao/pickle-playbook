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
  const netH = 18

  const [nvzFarX, nvzFarY] = courtToScreen(COURT_W / 2, NET_Y - KITCHEN / 2)
  const [nvzNearX, nvzNearY] = courtToScreen(COURT_W / 2, NET_Y + KITCHEN / 2)

  return (
    <div
      ref={ref}
      style={{ borderRadius: 10, overflow: 'hidden', boxShadow: '0 8px 40px rgba(0,0,0,0.6)' }}
    >
      <svg
        width={SVG_W}
        height={SVG_H}
        viewBox={`0 0 ${SVG_W} ${SVG_H}`}
        style={{ display: 'block', width: '100%', height: 'auto', touchAction: 'none', background: '#0a0a0a' }}
      >
        <path d={quadPath(0, 0, COURT_W, 44)} fill={COLORS.courtMain} />
        <path d={quadPath(0, NET_Y - KITCHEN, COURT_W, NET_Y)} fill={COLORS.kitchenFar} />
        <path d={quadPath(0, NET_Y, COURT_W, NET_Y + KITCHEN)} fill={COLORS.kitchenNear} />

        {COURT_LINES.map((c, i) => {
          const l = courtLine(...c)
          return <line key={i} {...l} stroke={COLORS.lines} strokeWidth={2.2} />
        })}

        <line x1={netLX} y1={netLY + 2} x2={netRX} y2={netLY + 2} stroke="rgba(0,0,0,0.15)" strokeWidth={netH} />
        <rect x={netLX} y={netLY - netH} width={netRX - netLX} height={netH} fill="rgba(0,0,0,0.18)" />
        <line x1={netLX} y1={netLY - netH} x2={netRX} y2={netLY - netH} stroke="rgba(255,255,255,0.7)" strokeWidth={2} />
        {Array.from({ length: 16 }).map((_, i) => {
          const f = (i + 1) / 17
          const mx = netLX + (netRX - netLX) * f
          return (
            <line
              key={`v${i}`}
              x1={mx}
              y1={netLY - netH + 2}
              x2={mx}
              y2={netLY}
              stroke="rgba(255,255,255,0.08)"
              strokeWidth={0.5}
            />
          )
        })}
        {Array.from({ length: 3 }).map((_, i) => {
          const f = (i + 1) / 4
          const my = netLY - netH + 2 + (netH - 3) * f
          return (
            <line
              key={`h${i}`}
              x1={netLX + 3}
              y1={my}
              x2={netRX - 3}
              y2={my}
              stroke="rgba(255,255,255,0.05)"
              strokeWidth={0.4}
            />
          )
        })}

        <text
          x={nvzFarX}
          y={nvzFarY}
          textAnchor="middle"
          dominantBaseline="middle"
          fontSize="9"
          fill="rgba(255,255,255,0.09)"
          fontFamily="'DM Mono', monospace"
          fontWeight="600"
          letterSpacing="2px"
        >
          NVZ
        </text>
        <text
          x={nvzNearX}
          y={nvzNearY}
          textAnchor="middle"
          dominantBaseline="middle"
          fontSize="12"
          fill="rgba(255,255,255,0.07)"
          fontFamily="'DM Mono', monospace"
          fontWeight="600"
          letterSpacing="3px"
        >
          NVZ
        </text>

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
                facingForward={!isOpp}
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
