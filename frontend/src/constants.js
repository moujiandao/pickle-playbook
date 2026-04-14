// Court dimensions in feet — see CLAUDE.md "Coordinate System"
export const COURT_W = 20
export const COURT_L = 44
export const KITCHEN = 7
export const NET_Y = COURT_L / 2

// SVG viewport matches reference-court.jpg (frontend/public/court.jpg) 1000x556
// so corner pixel coords can be used directly as SVG units.
export const SVG_W = 1000
export const SVG_H = 556

// Court corners measured from the reference image. The image is drawn with
// non-physical perspective: the near half is a trapezoid, the far half is
// essentially a rectangle, and the two meet at the net line (y_screen = 245).
// Players/ball project piecewise around NET_SCREEN_Y — see courtProjection.js.
export const NEAR_LEFT_X = 141
export const NEAR_RIGHT_X = 858
export const NEAR_Y = 430

export const FAR_LEFT_X = 253
export const FAR_RIGHT_X = 750
export const FAR_Y = 175

// Screen y where courtY = NET_Y (22). Junction of far rectangle and near
// trapezoid in the image; player/ball movement is restricted against this.
export const NET_SCREEN_Y = 245

// Base player height in SVG units at scale=1. Sized per skill's
// 40px hard minimum: far-side players use depth scale 0.55, so base
// must be ≥ 40 / 0.55 ≈ 73. Using 75 gives a small safety margin.
export const PLAYER_HEIGHT = 195
export const BALL_RADIUS = 12

// Visual elevation of the ball above its ground position, at scale=1.
// 'mid' raises the ball one NET_PIXEL_HEIGHT (approximately the net-tape
// height in the image), 'high' raises it 2x. Scaled by depth so far-side
// balls rise less in pixels, matching perspective.
export const NET_PIXEL_HEIGHT = 40

export const COLORS = {
  courtMain: '#2563EB',
  kitchenFar: '#2563EB',
  kitchenNear: '#2563EB',
  outOfBounds: '#991B1B',
  lines: '#FFFFFF',
  myTeam: '#F5A623',
  oppTeam: '#E74C3C',
  ballFill: '#C8E636',
  ballStroke: '#2C3E50',
  netFill: '#2C3E50',
  netMesh: 'rgba(255,255,255,0.5)',
  accent: '#f59e0b',
  bg: '#0e1117',
  panel: '#1c2530',
  text: '#e8e4dd',
}

export const BALL_HEIGHTS = ['low', 'mid', 'high']
export const BALL_SPEEDS = ['slow', 'fast']
export const BALL_SPINS = ['topspin', 'flat', 'slice']

export const INITIAL_PLAYERS = {
  opp_left: { x: 5, y: 7 },
  opp_right: { x: 15, y: 7 },
  my_left: { x: 5, y: 37 },
  my_right: { x: 15, y: 37 },
}

export const INITIAL_BALL = { x: 10, y: 33, height: 'mid', speed: 'slow', spin: null }

export function describePosition(ftX, ftY, side) {
  const lr =
    ftX < COURT_W / 3 ? 'left sideline' : ftX > (COURT_W * 2) / 3 ? 'right sideline' : 'center'
  const dist = side === 'my' ? ftY - NET_Y : NET_Y - ftY
  const depth =
    dist <= KITCHEN ? 'kitchen line' : dist <= KITCHEN + 5 ? 'transition zone' : 'baseline'
  return `${depth}, ${lr}`
}

export function describeBallZone(ftY) {
  if (ftY >= NET_Y + KITCHEN) return 'baseline'
  if (ftY >= NET_Y) return 'your kitchen'
  if (ftY >= NET_Y - KITCHEN) return 'opponent kitchen'
  return 'opponent baseline'
}
