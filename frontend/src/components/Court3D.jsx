import { forwardRef } from 'react'
import StickFigure from './StickFigure'
import BallIcon from './BallIcon'
import { courtToScreen, depthScale } from '../lib/courtProjection'
import { SVG_W, SVG_H, COLORS } from '../constants'

const Court3D = forwardRef(function Court3D({ players, ball, mySide, dragging, onPointerDown }, ref) {
  const entities = [
    ...Object.entries(players).map(([k, p]) => ({ type: 'player', key: k, ...p })),
    { type: 'ball', key: 'ball', ...ball },
  ].sort((a, b) => b.y - a.y)

  return (
    <div
      ref={ref}
      style={{ borderRadius: 10, overflow: 'hidden', boxShadow: '0 8px 40px rgba(0,0,0,0.6)' }}
    >
      <svg
        width={SVG_W}
        height={SVG_H}
        viewBox={`0 0 ${SVG_W} ${SVG_H}`}
        style={{ display: 'block', width: '100%', height: 'auto', touchAction: 'none' }}
      >
        <image
          href="/court.jpg"
          x={0}
          y={0}
          width={SVG_W}
          height={SVG_H}
          preserveAspectRatio="none"
        />

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
