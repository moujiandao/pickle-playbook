import {
  COURT_W,
  COURT_L,
  NEAR_LEFT_X,
  NEAR_RIGHT_X,
  NEAR_Y,
  FAR_LEFT_X,
  FAR_RIGHT_X,
  FAR_Y,
  DEPTH_EXP,
} from '../constants'

export function courtToScreen(ftX, ftY) {
  const t = 1 - ftY / COURT_L
  const depth = Math.pow(t, DEPTH_EXP)
  const screenY = NEAR_Y - depth * (NEAR_Y - FAR_Y)
  const leftX = NEAR_LEFT_X + depth * (FAR_LEFT_X - NEAR_LEFT_X)
  const rightX = NEAR_RIGHT_X + depth * (FAR_RIGHT_X - NEAR_RIGHT_X)
  return [leftX + (ftX / COURT_W) * (rightX - leftX), screenY]
}

export function screenToCourt(sx, sy) {
  const depth = Math.max(0, Math.min(1, (NEAR_Y - sy) / (NEAR_Y - FAR_Y)))
  const t = Math.pow(depth, 1 / DEPTH_EXP)
  const ftY = (1 - t) * COURT_L
  const leftX = NEAR_LEFT_X + depth * (FAR_LEFT_X - NEAR_LEFT_X)
  const rightX = NEAR_RIGHT_X + depth * (FAR_RIGHT_X - NEAR_RIGHT_X)
  return [
    Math.max(0, Math.min(COURT_W, ((sx - leftX) / (rightX - leftX)) * COURT_W)),
    Math.max(0, Math.min(COURT_L, ftY)),
  ]
}

// Build an SVG path string for a court-space rectangle, projected through perspective.
export function quadPath(x1, y1, x2, y2) {
  const [ax, ay] = courtToScreen(x1, y1)
  const [bx, by] = courtToScreen(x2, y1)
  const [cx, cy] = courtToScreen(x2, y2)
  const [dx, dy] = courtToScreen(x1, y2)
  return `M${ax},${ay} L${bx},${by} L${cx},${cy} L${dx},${dy} Z`
}

// Project a line from court coords into screen-space line endpoints.
export function courtLine(x1, y1, x2, y2) {
  const [a, b] = courtToScreen(x1, y1)
  const [c, d] = courtToScreen(x2, y2)
  return { x1: a, y1: b, x2: c, y2: d }
}

// Players far from the camera appear smaller.
// Per pickleball-court-rendering skill: scale = 0.55 + depth_ratio * 0.45
// where depth_ratio is 0.0 at the far baseline and 1.0 at the near baseline.
export function depthScale(ftY) {
  const depthRatio = ftY / COURT_L
  return 0.55 + depthRatio * 0.45
}
