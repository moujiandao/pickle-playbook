import { BALL_RADIUS, COLORS } from '../constants'

// Pickleball: neon yellow-green, dark outline.
// Sized per skill: max(8px, court_width * 0.025). Base radius is BALL_RADIUS
// SVG units; depth-scaled by Court3D so far-side balls read smaller but stay
// above the 8px minimum.
export default function BallIcon({ cx, cy, isSelected, scale }) {
  const r = Math.max(4, BALL_RADIUS * (scale || 1))
  const stroke = Math.max(1.5, r * 0.18)

  return (
    <g style={{ cursor: 'grab' }}>
      {isSelected && (
        <circle
          cx={cx}
          cy={cy}
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

      {/* Ground shadow */}
      <ellipse cx={cx} cy={cy + r + 2} rx={r * 0.6} ry={r * 0.18} fill="rgba(0,0,0,0.28)" />

      {/* Ball body */}
      <circle
        cx={cx}
        cy={cy}
        r={r}
        fill={COLORS.ballFill}
        stroke={COLORS.ballStroke}
        strokeWidth={stroke}
      />

      {/* Ball holes (pickleball signature) */}
      <circle cx={cx - r * 0.35} cy={cy - r * 0.15} r={r * 0.12} fill={COLORS.ballStroke} opacity={0.55} />
      <circle cx={cx + r * 0.30} cy={cy + r * 0.10} r={r * 0.12} fill={COLORS.ballStroke} opacity={0.55} />
      <circle cx={cx + r * 0.05} cy={cy - r * 0.40} r={r * 0.10} fill={COLORS.ballStroke} opacity={0.55} />
    </g>
  )
}
