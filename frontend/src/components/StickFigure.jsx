export default function StickFigure({ cx, cy, facingForward, color, label, isSelected, isMe, scale }) {
  const s = (scale || 1) * 0.55
  const headR = 4.2 * s
  const bodyLen = 12 * s
  const limbLen = 8.5 * s
  const armSpread = 7.5 * s
  const bodyTopY = cy - bodyLen

  return (
    <g style={{ cursor: 'grab' }}>
      {isSelected && (
        <ellipse
          cx={cx}
          cy={cy + 2 * s}
          rx={13 * s}
          ry={5 * s}
          fill="none"
          stroke={color}
          strokeWidth={1.5}
          strokeDasharray="4,3"
          opacity={0.7}
        >
          <animate attributeName="stroke-dashoffset" from="0" to="14" dur="1s" repeatCount="indefinite" />
        </ellipse>
      )}
      {isMe && (
        <>
          <rect
            x={cx + 7 * s}
            y={bodyTopY - headR * 2.2}
            width={19 * s}
            height={11 * s}
            rx={2.5 * s}
            fill="#f59e0b"
            stroke="#b45309"
            strokeWidth={0.8}
          />
          <text
            x={cx + 16.5 * s}
            y={bodyTopY - headR * 2.2 + 8 * s}
            textAnchor="middle"
            fontSize={6.5 * s}
            fontWeight="800"
            fill="#1a1a1a"
            fontFamily="'DM Mono', monospace"
          >
            ME
          </text>
        </>
      )}
      <ellipse cx={cx} cy={cy + 3 * s} rx={5.5 * s} ry={2 * s} fill="rgba(0,0,0,0.2)" />
      <circle cx={cx} cy={bodyTopY - headR} r={headR} fill={color} stroke="rgba(0,0,0,0.2)" strokeWidth={0.8 * s} />
      {facingForward && s > 0.4 && (
        <>
          <circle cx={cx - 1.3 * s} cy={bodyTopY - headR - 0.5 * s} r={0.7 * s} fill="rgba(0,0,0,0.3)" />
          <circle cx={cx + 1.3 * s} cy={bodyTopY - headR - 0.5 * s} r={0.7 * s} fill="rgba(0,0,0,0.3)" />
        </>
      )}
      <line x1={cx} y1={bodyTopY} x2={cx} y2={cy} stroke="rgba(255,255,255,0.7)" strokeWidth={1.6 * s} strokeLinecap="round" />
      <line
        x1={cx - armSpread}
        y1={bodyTopY + bodyLen * 0.3}
        x2={cx + armSpread}
        y2={bodyTopY + bodyLen * 0.33}
        stroke="rgba(255,255,255,0.6)"
        strokeWidth={1.4 * s}
        strokeLinecap="round"
      />
      <line
        x1={cx + armSpread}
        y1={bodyTopY + bodyLen * 0.33}
        x2={cx + armSpread + 3 * s}
        y2={bodyTopY + bodyLen * 0.15}
        stroke="#c4a86a"
        strokeWidth={1.8 * s}
        strokeLinecap="round"
      />
      <line
        x1={cx}
        y1={cy}
        x2={cx - 3.5 * s}
        y2={cy + limbLen * 0.65}
        stroke="rgba(255,255,255,0.6)"
        strokeWidth={1.4 * s}
        strokeLinecap="round"
      />
      <line
        x1={cx}
        y1={cy}
        x2={cx + 3.5 * s}
        y2={cy + limbLen * 0.65}
        stroke="rgba(255,255,255,0.6)"
        strokeWidth={1.4 * s}
        strokeLinecap="round"
      />
      <text
        x={cx}
        y={cy + limbLen * 0.65 + 9 * s}
        textAnchor="middle"
        fontSize={8 * s}
        fontWeight="700"
        fill={color}
        fontFamily="'DM Mono', monospace"
        letterSpacing="0.3px"
        stroke="rgba(0,0,0,0.7)"
        strokeWidth={2.5 * s}
        paintOrder="stroke"
      >
        {label}
      </text>
    </g>
  )
}
