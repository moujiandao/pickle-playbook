// Court dimensions in feet — see CLAUDE.md "Coordinate System"
export const COURT_W = 20
export const COURT_L = 44
export const KITCHEN = 7
export const NET_Y = COURT_L / 2

// SVG viewport & trapezoid geometry for the 3D-perspective court.
export const SVG_W = 800
export const SVG_H = 440

export const NEAR_LEFT_X = 30
export const NEAR_RIGHT_X = SVG_W - 30
export const NEAR_Y = SVG_H - 25

export const FAR_LEFT_X = 185
export const FAR_RIGHT_X = SVG_W - 185
export const FAR_Y = 65

export const DEPTH_EXP = 1.12

export const COLORS = {
  courtMain: '#2e8ab8',
  kitchenFar: '#2980aa',
  kitchenNear: '#2b84b0',
  lines: 'rgba(255,255,255,0.92)',
  myTeam: '#48bfe3',
  oppTeam: '#ef6461',
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
