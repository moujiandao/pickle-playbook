"""Converts x/y foot coordinates into tactical English for Claude prompts."""

# Court dimensions (feet)
COURT_WIDTH = 20.0
COURT_LENGTH = 44.0
NET_Y = 22.0
KITCHEN_Y_NEAR = 29.0  # kitchen line on the near (y > 22) half
KITCHEN_Y_FAR = 15.0   # kitchen line on the far (y < 22) half

# Left/right thirds of the 20-ft court
_LEFT_CUTOFF = COURT_WIDTH / 3        # ~6.7 ft
_RIGHT_CUTOFF = COURT_WIDTH * 2 / 3  # ~13.3 ft


def _lateral(x: float) -> str:
    if x <= _LEFT_CUTOFF:
        return "left third of court"
    elif x >= _RIGHT_CUTOFF:
        return "right third of court"
    return "center of court"


def _depth(y: float, is_near_side: bool) -> str:
    """Describe depth relative to the player's own half."""
    if is_near_side:
        # Near side: baseline at y=44, net at y=22, kitchen line at y=29
        dist_from_net = y - NET_Y
        if y <= KITCHEN_Y_NEAR:
            return "at the kitchen line (non-volley zone edge)"
        elif dist_from_net <= 5:
            return f"{dist_from_net:.0f}ft behind the kitchen line"
        elif y >= 40:
            return "at the baseline"
        else:
            return f"{dist_from_net:.0f}ft behind the net"
    else:
        # Far side: baseline at y=0, net at y=22, kitchen line at y=15
        dist_from_net = NET_Y - y
        if y >= KITCHEN_Y_FAR:
            return "at the kitchen line (non-volley zone edge)"
        elif dist_from_net <= 5:
            return f"{dist_from_net:.0f}ft behind the kitchen line"
        elif y <= 4:
            return "at the baseline"
        else:
            return f"{dist_from_net:.0f}ft behind the net"


def describe_position(x: float, y: float, is_near_side: bool) -> str:
    """Return a short tactical description of a position."""
    lateral = _lateral(x)
    depth = _depth(y, is_near_side)
    return f"{lateral}, {depth}"
