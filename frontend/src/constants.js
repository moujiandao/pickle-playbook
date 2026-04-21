// Court dimensions in feet — see CLAUDE.md "Coordinate System"
export const COURT_W = 20
export const COURT_L = 44
export const KITCHEN = 7
export const NET_Y = COURT_L / 2

// SVG viewport & trapezoid geometry for the 3D-perspective court.
//   - near baseline width = 680px, centered in SVG with 100px
//     out-of-bounds margin on each side (slightly wider green than
//     the previous 60px)
//   - far baseline = 50% of near baseline (trapezoid foreshortening)
//   - 120px out-of-bounds margin above the far baseline so far-side
//     stick-figure heads are not clipped at the top of the SVG
//   - 120px out-of-bounds margin below the near baseline (3x the
//     previous 40px) to give the near-side player more visual runway
//   - DEPTH_EXP tuned so the near half (net → near baseline) is 10%
//     taller on screen than the far half (net → far baseline); with
//     screen_y = NEAR_Y - 0.5^E * (NEAR_Y - FAR_Y) at the net line,
//     solving near/far = 1.10 gives E ≈ 0.93
export const SVG_W = 880
export const SVG_H = 617

export const NEAR_LEFT_X = 100
export const NEAR_RIGHT_X = SVG_W - 100
export const NEAR_Y = SVG_H - 120

// Far baseline width = (NEAR_RIGHT_X - NEAR_LEFT_X) / 2 = 340, centered in SVG
export const FAR_LEFT_X = 270
export const FAR_RIGHT_X = SVG_W - 270
export const FAR_Y = 120

export const DEPTH_EXP = 0.93

// Base player height in SVG units at scale=1. Sized per skill's
// 40px hard minimum: far-side players use depth scale 0.55, so base
// must be ≥ 40 / 0.55 ≈ 73. Using 75 gives a small safety margin.
export const PLAYER_HEIGHT = 195
export const BALL_RADIUS = 12

// Visual elevation of the ball above its ground position, at scale=1.
// 'low' = 1x, 'mid' = 2x, 'high' = 4x (see BALL_ELEVATION_MULT in Court3D).
// Scaled by depth so far-side balls rise fewer pixels in perspective.
export const NET_PIXEL_HEIGHT = 40

export const COLORS = {
  courtMain: '#1E93D6',
  serviceBox: '#355392',
  kitchenFar: '#1E93D6',
  kitchenNear: '#1E93D6',
  outOfBounds: '#1E93D6',
  lines: '#FFFFFF',
  myTeam: '#F5A623',
  oppTeam: '#E74C3C',
  ballFill: '#C8E636',
  ballStroke: '#2C3E50',
  netFill: '#2C3E50',
  netMesh: 'rgba(255,255,255,0.95)',
  accent: '#f59e0b',
  bg: '#0e1117',
  panel: '#1c2530',
  text: '#e8e4dd',
}

export const BALL_HEIGHTS = ['low', 'mid', 'high']
export const BALL_SPEEDS = ['slow', 'fast']
export const BALL_SPINS = ['topspin', 'flat', 'slice']
export const SKILL_LEVELS = ['3.0', '3.5', '4.0', '4.5', '5.0']

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
