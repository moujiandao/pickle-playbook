// StickFigure — player stick figure component. Placeholder.

export default function StickFigure({ color = '#3b82f6', label = '' }) {
  return (
    <g>
      <circle r="6" fill={color} />
      {label && <text y="-10" textAnchor="middle" fill="#fff" fontSize="10">{label}</text>}
    </g>
  )
}
