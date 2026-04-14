import { BALL_RADIUS, COLORS } from '../constants'

// Pickleball: neon yellow-green, dark outline.
// cx/cy are the *ground* position. If elevation > 0, the ball body renders
// that many SVG units above the ground, with a vertical tether line showing
// the lift; the ground shadow stays pinned to cy.
export default function BallIcon({ cx, cy, elevation = 0, spin, isSelected, scale }) {
  const r = Math.max(4, BALL_RADIUS * (scale || 1))
  const stroke = Math.max(1.5, r * 0.18)
  const cyBall = cy - elevation
  const spinLabel = spin === 'topspin' ? 'Has Topspin' : spin === 'slice' ? 'Has Slice' : null
  const spinFontSize = Math.max(11, 16 * (scale || 1))

  return (
    <g style={{ cursor: 'grab' }}>
      {/* Ground shadow stays at the court contact point */}
      <ellipse cx={cx} cy={cy + r * 0.2} rx={r * 0.6} ry={r * 0.18} fill="rgba(0,0,0,0.38)" />

      {/* Vertical height tether from ground to elevated ball */}
      {elevation > 0 && (
        <line
          x1={cx}
          y1={cy}
          x2={cx}
          y2={cyBall}
          stroke="rgba(255,255,255,0.85)"
          strokeWidth={Math.max(1.2, r * 0.16)}
          strokeDasharray={`${Math.max(3, r * 0.5)},${Math.max(2, r * 0.35)}`}
          strokeLinecap="round"
        />
      )}

      {isSelected && (
        <circle
          cx={cx}
          cy={cyBall}
          r={r + 6}
          fill="none"
          stroke="#f59e0b"
          strokeWidth={2}
          strokeDasharray="5,3"
          opacity={0.85}
        >
          <animate attributeName="stroke-dashoffset" from="0" to="16" dur="0.8s" repeatCount="indefinite" />
        </circle>
      )}

      {/* Ball body */}
      <circle
        cx={cx}
        cy={cyBall}
        r={r}
        fill={COLORS.ballFill}
        stroke={COLORS.ballStroke}
        strokeWidth={stroke}
      />

      {/* Ball holes (pickleball signature) */}
      <circle cx={cx - r * 0.35} cy={cyBall - r * 0.15} r={r * 0.12} fill={COLORS.ballStroke} opacity={0.55} />
      <circle cx={cx + r * 0.30} cy={cyBall + r * 0.10} r={r * 0.12} fill={COLORS.ballStroke} opacity={0.55} />
      <circle cx={cx + r * 0.05} cy={cyBall - r * 0.40} r={r * 0.10} fill={COLORS.ballStroke} opacity={0.55} />

      {spinLabel && (
        <text
          x={cx}
          y={cyBall - r - spinFontSize * 0.5}
          textAnchor="middle"
          fontSize={spinFontSize}
          fontWeight="700"
          fill="#ffffff"
          fontFamily="'DM Mono', monospace"
          stroke="rgba(0,0,0,0.8)"
          strokeWidth={3}
          paintOrder="stroke"
        >
          {spinLabel}
        </text>
      )}
    </g>
  )
}
