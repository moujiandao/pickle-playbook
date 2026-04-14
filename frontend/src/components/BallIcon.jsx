export default function BallIcon({ cx, cy, isSelected, scale }) {
  const s = (scale || 1) * 0.55
  const r = 4.5 * s
  return (
    <g style={{ cursor: 'grab' }}>
      {isSelected && (
        <circle
          cx={cx}
          cy={cy}
          r={r + 5 * s}
          fill="none"
          stroke="#f59e0b"
          strokeWidth={1.5}
          strokeDasharray="4,3"
          opacity={0.8}
        >
          <animate attributeName="stroke-dashoffset" from="0" to="14" dur="0.8s" repeatCount="indefinite" />
        </circle>
      )}
      <ellipse cx={cx} cy={cy + r + 1.5 * s} rx={r * 0.5} ry={1.2 * s} fill="rgba(0,0,0,0.15)" />
      <circle cx={cx} cy={cy} r={r} fill="#c8e64a" stroke="#5a6e1a" strokeWidth={0.9 * s} />
      <circle cx={cx - 1 * s} cy={cy - 1 * s} r={0.9 * s} fill="#b0d63a" />
      <circle cx={cx + 1.8 * s} cy={cy + 0.5 * s} r={0.7 * s} fill="#b0d63a" />
    </g>
  )
}
