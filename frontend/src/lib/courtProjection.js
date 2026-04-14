import {
  COURT_W,
  COURT_L,
  NET_Y,
  NEAR_LEFT_X,
  NEAR_RIGHT_X,
  NEAR_Y,
  FAR_LEFT_X,
  FAR_RIGHT_X,
  FAR_Y,
  NET_SCREEN_Y,
} from '../constants'

// The reference court image uses non-physical perspective: the far half is
// drawn as a rectangle and the near half as a trapezoid, meeting at the net
// line. We honor that structure so players/ball land on the image exactly.
//
// Y mapping (piecewise linear, split at courtY = NET_Y):
//   courtY in [0, NET_Y]  -> screenY in [FAR_Y, NET_SCREEN_Y]
//   courtY in [NET_Y, 44] -> screenY in [NET_SCREEN_Y, NEAR_Y]
//
// X mapping:
//   far half  -> rectangle between FAR_LEFT_X and FAR_RIGHT_X
//   near half -> trapezoid tapering from (FAR_LEFT_X, FAR_RIGHT_X) at the net
//                to (NEAR_LEFT_X, NEAR_RIGHT_X) at the near baseline

function sidelinesAt(ftY) {
  if (ftY <= NET_Y) {
    return [FAR_LEFT_X, FAR_RIGHT_X]
  }
  const d = (ftY - NET_Y) / (COURT_L - NET_Y)
  return [
    FAR_LEFT_X + (NEAR_LEFT_X - FAR_LEFT_X) * d,
    FAR_RIGHT_X + (NEAR_RIGHT_X - FAR_RIGHT_X) * d,
  ]
}

function ftYToScreenY(ftY) {
  if (ftY <= NET_Y) {
    return FAR_Y + (ftY / NET_Y) * (NET_SCREEN_Y - FAR_Y)
  }
  return NET_SCREEN_Y + ((ftY - NET_Y) / (COURT_L - NET_Y)) * (NEAR_Y - NET_SCREEN_Y)
}

function screenYToFtY(sy) {
  if (sy <= NET_SCREEN_Y) {
    return ((sy - FAR_Y) / (NET_SCREEN_Y - FAR_Y)) * NET_Y
  }
  return NET_Y + ((sy - NET_SCREEN_Y) / (NEAR_Y - NET_SCREEN_Y)) * (COURT_L - NET_Y)
}

export function courtToScreen(ftX, ftY) {
  const screenY = ftYToScreenY(ftY)
  const [leftX, rightX] = sidelinesAt(ftY)
  const screenX = leftX + (ftX / COURT_W) * (rightX - leftX)
  return [screenX, screenY]
}

export function screenToCourt(sx, sy) {
  const clampedSY = Math.max(FAR_Y, Math.min(NEAR_Y, sy))
  const ftY = Math.max(0, Math.min(COURT_L, screenYToFtY(clampedSY)))
  const [leftX, rightX] = sidelinesAt(ftY)
  const ftX = Math.max(0, Math.min(COURT_W, ((sx - leftX) / (rightX - leftX)) * COURT_W))
  return [ftX, ftY]
}

// Players far from the camera appear smaller.
// Depth ratio: 0 at far baseline, 1 at near baseline.
export function depthScale(ftY) {
  return 0.55 + (ftY / COURT_L) * 0.45
}
