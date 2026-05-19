import { PLAYER_HEIGHT } from '../constants'

// Proportions per pickleball-court-rendering skill:
//   head diameter = 0.18 × player_height
//   body length   = 0.40 × player_height
//   leg length    = 0.35 × player_height (each)
//   leg spread    = 0.25 × player_height
//   arm span      = 0.40 × player_height
//   arms attach   = 0.30 × body length from top of body
export default function StickFigure({ cx, cy, color, label, isSelected, isMe, isPartner, scale, reachRx, inAttackPosition, handedness, verticalFlip, forceShowZones }) {
  // Either being dragged, or the global "always on" toggle is enabled.
  const ringVisible = isSelected || forceShowZones
  // vFlip = -1 reflects wedges vertically for opps (zones face the net, not away).
  // Opps also face us, so their right hand is on screen-left → invert hand mirror
  // for opps so the handedness UI reads from the *player's* POV, not the camera's.
  const vFlip = verticalFlip === -1 ? -1 : 1
  const baseHandMirror = handedness === 'left' ? -1 : 1
  const mirror = baseHandMirror * vFlip
  const h = PLAYER_HEIGHT * (scale || 1)
  const headR = (h * 0.18) / 2
  const bodyLen = h * 0.40
  const legLen = h * 0.35
  const legSpread = h * 0.25
  const armSpan = h * 0.40
  const armOffsetY = bodyLen * 0.30
  const stroke = Math.max(2, h * 0.04)
  // Match the BallIcon spin-label sizing so 'Leftside Player' reads
  // at the same visual weight as 'Has Topspin'.
  const labelSize = Math.max(11, 16 * (scale || 1))

  const feetY = cy
  const hipY = feetY - legLen
  const shoulderY = hipY - bodyLen
  const headCY = shoulderY - headR

  // Paddle dimensions relative to player height
  const paddleHandleLen = h * 0.132
  const paddleFaceH = h * 0.204
  const paddleFaceW = h * 0.156
  const paddleHandleW = h * 0.0456
  const paddleRx = paddleFaceW * 0.22
  const paddleStroke = Math.max(1, h * 0.0192)
  const handX = cx + (mirror * armSpan) / 2
  const handY = shoulderY + armOffsetY

  const reachCx = cx
  const reachCy = feetY + h * 0.04
  const reachRxVal = reachRx ?? h * 0.32
  // Wedges keep the original (pre-stretch) ry; the dashed ring is 30% taller.
  const wedgeRyVal = reachRx != null ? reachRx * 0.338688 : h * 0.108864
  const reachRyVal = wedgeRyVal * 1.3

  return (
    <g style={{ cursor: 'grab' }}>
      {ringVisible && (inAttackPosition || forceShowZones) && (
        <>
          {/* Forehand attackable zone — full reach, on dominant-hand side */}
          <path
            d={`M ${reachCx} ${reachCy} L ${reachCx} ${reachCy - vFlip * wedgeRyVal} A ${reachRxVal} ${wedgeRyVal} 0 0 ${mirror * vFlip === 1 ? 1 : 0} ${reachCx + mirror * reachRxVal} ${reachCy} Z`}
            fill="#f97316"
            stroke="#f97316"
            strokeWidth={stroke * 0.6}
          >
            <animate attributeName="fill-opacity" values="0.25;0.65;0.25" dur="0.9s" repeatCount="indefinite" />
            <animate attributeName="stroke-opacity" values="0.6;1;0.6" dur="0.9s" repeatCount="indefinite" />
          </path>
          {/* Backhand attackable zone — ~30% less reach, opposite of forehand */}
          <path
            d={`M ${reachCx} ${reachCy} L ${reachCx} ${reachCy - vFlip * wedgeRyVal * 0.7} A ${reachRxVal * 0.7} ${wedgeRyVal * 0.7} 0 0 ${mirror * vFlip === 1 ? 0 : 1} ${reachCx - mirror * reachRxVal * 0.7} ${reachCy} Z`}
            fill="#38bdf8"
            stroke="#38bdf8"
            strokeWidth={stroke * 0.6}
          >
            <animate attributeName="fill-opacity" values="0.25;0.65;0.25" dur="0.9s" repeatCount="indefinite" />
            <animate attributeName="stroke-opacity" values="0.6;1;0.6" dur="0.9s" repeatCount="indefinite" />
          </path>
        </>
      )}
      {ringVisible && (
        <ellipse
          cx={reachCx}
          cy={reachCy}
          rx={reachRxVal}
          ry={reachRyVal}
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

      {/* Paddle at dominant hand */}
      <g transform={`translate(${handX},${handY}) rotate(${mirror * 38})`}>
        {/* Grip cap */}
        <rect
          x={-paddleHandleW * 0.7}
          y={0}
          width={paddleHandleW * 1.4}
          height={paddleHandleLen * 0.22}
          rx={paddleHandleW * 0.3}
          fill="#1a1a1a"
        />
        {/* Handle */}
        <rect
          x={-paddleHandleW / 2}
          y={-paddleHandleLen}
          width={paddleHandleW}
          height={paddleHandleLen}
          fill="#333"
          stroke="#111"
          strokeWidth={paddleStroke * 0.6}
        />
        {/* Face */}
        <rect
          x={-paddleFaceW / 2}
          y={-paddleHandleLen - paddleFaceH}
          width={paddleFaceW}
          height={paddleFaceH}
          rx={paddleRx}
          ry={paddleRx}
          fill={color}
          stroke="rgba(0,0,0,0.65)"
          strokeWidth={paddleStroke * 1.5}
        />
        {/* Edge guard at throat */}
        <rect
          x={-paddleFaceW / 2}
          y={-paddleHandleLen - paddleStroke * 2}
          width={paddleFaceW}
          height={paddleStroke * 2.5}
          fill="#222"
        />
      </g>

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
      {label && (
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
      )}

      {/* Attack-zone labels — rendered last so they sit above the dashed ring */}
      {ringVisible && (inAttackPosition || forceShowZones) && (() => {
        const zoneFont = h * 0.058
        const lineH = zoneFont * 1.05
        const bhCenterX = reachCx - mirror * reachRxVal * 0.35
        const fhCenterX = reachCx + mirror * reachRxVal * 0.5
        // For south players (vFlip=1) wedges occupy the upper half and labels
        // sit just below midline. For opps (vFlip=-1) wedges occupy the lower
        // half and labels stack just above midline (last line ends near cy).
        const firstLineY =
          vFlip === 1 ? reachCy + zoneFont * 0.95 : reachCy - 2 * lineH - zoneFont * 0.1
        const textProps = {
          textAnchor: 'middle',
          fontSize: zoneFont,
          fontWeight: 700,
          fill: '#fff',
          fontFamily: "'DM Mono', monospace",
          letterSpacing: '0.3px',
        }
        return (
          <g style={{ filter: 'drop-shadow(0 1.5px 2.5px rgba(0,0,0,0.85))' }}>
            <text x={bhCenterX} y={firstLineY} {...textProps}>
              <tspan x={bhCenterX}>bh</tspan>
              <tspan x={bhCenterX} dy={lineH}>attackable</tspan>
              <tspan x={bhCenterX} dy={lineH}>zone</tspan>
            </text>
            <text x={fhCenterX} y={firstLineY} {...textProps}>
              <tspan x={fhCenterX}>fh</tspan>
              <tspan x={fhCenterX} dy={lineH}>attackable</tspan>
              <tspan x={fhCenterX} dy={lineH}>zone</tspan>
            </text>
          </g>
        )
      })()}
    </g>
  )
}
