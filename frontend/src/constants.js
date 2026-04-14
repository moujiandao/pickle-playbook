// Court dimensions in feet — see CLAUDE.md "Coordinate System"
export const COURT_WIDTH_FT = 20
export const COURT_LENGTH_FT = 44
export const NET_Y = 22
export const KITCHEN_DEPTH_FT = 7
export const KITCHEN_NEAR_Y = NET_Y + KITCHEN_DEPTH_FT
export const KITCHEN_FAR_Y = NET_Y - KITCHEN_DEPTH_FT

export const COLORS = {
  court: '#2a5d3a',
  kitchen: '#3a7d4a',
  line: '#ffffff',
  net: '#1a1a1a',
  myTeam: '#3b82f6',
  oppTeam: '#ef4444',
  ball: '#facc15',
}

export const BALL_HEIGHTS = ['low', 'mid', 'high']
export const BALL_SPEEDS = ['slow', 'fast']
export const BALL_SPINS = ['topspin', 'flat', 'slice']
