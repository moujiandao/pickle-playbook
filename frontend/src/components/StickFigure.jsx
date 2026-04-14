import { PLAYER_HEIGHT } from '../constants'

// Proportions per pickleball-court-rendering skill:
//   head diameter = 0.18 × player_height
//   body length   = 0.40 × player_height
//   leg length    = 0.35 × player_height (each)
//   leg spread    = 0.25 × player_height
//   arm span      = 0.40 × player_height
//   arms attach   = 0.30 × body length from top of body
export default function StickFigure({ cx, cy, color, label, isSelected, isMe, scale }) {
  const h = PLAYER_HEIGHT * (scale || 1)
  const headR = (h * 0.18) / 2
  const bodyLen = h * 0.40
  const legLen = h * 0.35
  const legSpread = h * 0.25
  const armSpan = h * 0.40
  const armOffsetY = bodyLen * 0.30
  const stroke = Math.max(2, h * 0.04)
  const labelSize = Math.max(12, h * 0.18)

  const feetY = cy
  const hipY = feetY - legLen
  const shoulderY = hipY - bodyLen
  const headCY = shoulderY - headR

  return (
    <g style={{ cursor: 'grab' }}>
      {isSelected && (
        <ellipse
          cx={cx}
          cy={feetY + h * 0.04}
          rx={h * 0.32}
          ry={h * 0.09}
          fill="none"
          stroke={color}
          strokeWidth={stroke * 0.9}
          strokeDasharray="6,4"
          opacity={0.85}
        >
          <animate attributeName="stroke-dashoffset" from="0" to="20" dur="1s" repeatCount="indefinite" />
        </ellipse>
      )}

      {/* Ground shadow */}
      <ellipse cx={cx} cy={feetY + h * 0.03} rx={h * 0.16} ry={h * 0.04} fill="rgba(0,0,0,0.28)" />

      {/* Head */}
      <circle
        cx={cx}
        cy={headCY}
        r={headR}
        fill={color}
        stroke="rgba(0,0,0,0.55)"
        strokeWidth={stroke * 0.7}
      />

      {/* Body */}
      <line
        x1={cx}
        y1={shoulderY}
        x2={cx}
        y2={hipY}
        stroke={color}
        strokeWidth={stroke}
        strokeLinecap="round"
      />

      {/* Arms */}
      <line
        x1={cx - armSpan / 2}
        y1={shoulderY + armOffsetY}
        x2={cx + armSpan / 2}
        y2={shoulderY + armOffsetY}
        stroke={color}
        strokeWidth={stroke}
        strokeLinecap="round"
      />

      {/* Paddle (short line from right hand) */}
      <line
        x1={cx + armSpan / 2}
        y1={shoulderY + armOffsetY}
        x2={cx + armSpan / 2 + h * 0.18}
        y2={shoulderY + armOffsetY - h * 0.05}
        stroke="#d4a373"
        strokeWidth={stroke * 1.2}
        strokeLinecap="round"
      />

      {/* Legs */}
      <line
        x1={cx}
        y1={hipY}
        x2={cx - legSpread / 2}
        y2={feetY}
        stroke={color}
        strokeWidth={stroke}
        strokeLinecap="round"
      />
      <line
        x1={cx}
        y1={hipY}
        x2={cx + legSpread / 2}
        y2={feetY}
        stroke={color}
        strokeWidth={stroke}
        strokeLinecap="round"
      />

      {isMe && (
        <g>
          <rect
            x={cx - h * 0.16}
            y={headCY - headR - h * 0.22}
            width={h * 0.32}
            height={h * 0.16}
            rx={h * 0.03}
            fill="#f59e0b"
            stroke="#b45309"
            strokeWidth={stroke * 0.5}
          />
          <text
            x={cx}
            y={headCY - headR - h * 0.10}
            textAnchor="middle"
            fontSize={h * 0.12}
            fontWeight="800"
            fill="#1a1a1a"
            fontFamily="'DM Mono', monospace"
          >
            ME
          </text>
        </g>
      )}

      {/* Label below figure, in team color */}
      <text
        x={cx}
        y={feetY + h * 0.22 + labelSize}
        textAnchor="middle"
        fontSize={labelSize}
        fontWeight="700"
        fill={color}
        fontFamily="'DM Mono', monospace"
        letterSpacing="0.5px"
        stroke="rgba(0,0,0,0.75)"
        strokeWidth={3}
        paintOrder="stroke"
      >
        {label}
      </text>
    </g>
  )
}
