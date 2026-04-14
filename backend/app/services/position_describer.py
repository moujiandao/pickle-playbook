"""Converts feet coordinates to natural language tactical descriptions."""

from typing import Literal

COURT_WIDTH_FT = 20.0
COURT_LENGTH_FT = 44.0
NET_Y = 22.0
KITCHEN_DEPTH = 7.0

Side = Literal["near", "far"]
Zone = Literal["kitchen", "transition", "baseline"]


def lateral_label(x_ft: float) -> str:
    if x_ft < COURT_WIDTH_FT / 3:
        return "left sideline"
    if x_ft > 2 * COURT_WIDTH_FT / 3:
        return "right sideline"
    return "middle"


def _zone_and_depth(distance_from_net_ft: float) -> tuple[Zone, str]:
    if distance_from_net_ft <= KITCHEN_DEPTH:
        return "kitchen", f"{distance_from_net_ft:.1f}ft from the net (kitchen)"
    if distance_from_net_ft <= 15:
        offset = distance_from_net_ft - KITCHEN_DEPTH
        return "transition", f"{offset:.1f}ft behind the kitchen line (transition zone)"
    return "baseline", f"{distance_from_net_ft:.1f}ft from the net (near baseline)"


def describe_position(x_ft: float, y_ft: float, side: Side) -> str:
    """Return a short tactical phrase for a point on the court.

    side: 'near' = your team (y >= 22), 'far' = opponents (y <= 22).
    """
    if side == "near":
        distance_from_net = y_ft - NET_Y
    else:
        distance_from_net = NET_Y - y_ft
    distance_from_net = max(0.0, distance_from_net)
    _, depth_phrase = _zone_and_depth(distance_from_net)
    return f"{depth_phrase}, {lateral_label(x_ft)}"


def zone_of(y_ft: float, side: Side) -> Zone:
    if side == "near":
        distance_from_net = y_ft - NET_Y
    else:
        distance_from_net = NET_Y - y_ft
    distance_from_net = max(0.0, distance_from_net)
    zone, _ = _zone_and_depth(distance_from_net)
    return zone


def ball_zone(y_ft: float) -> Zone:
    """Ball is always on the near side."""
    return zone_of(y_ft, "near")
