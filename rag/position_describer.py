"""
Translates GameState coordinates (in feet) into natural-language tactical descriptions.

Court coordinate system (from CLAUDE.md):
  x: 0 (left sideline) to 20 (right sideline)
  y: 0 (far baseline / opponents) to 44 (near baseline / our side)
  Net: y = 22
  Kitchen lines: y = 15 (far side, opponents) and y = 29 (near side, ours)
  Court width: 20 ft, divided at x=10 (center)

"Left" and "right" are always from the perspective of the team on OUR side (y >= 22).
"""

from typing import Literal

# Court constants
COURT_WIDTH = 20.0
COURT_LENGTH = 44.0
NET_Y = 22.0
KITCHEN_FAR = 15.0   # opponent's kitchen line (y < NET_Y side)
KITCHEN_NEAR = 29.0  # our kitchen line (y > NET_Y side)
CENTER_X = 10.0


# ---------------------------------------------------------------------------
# Zone helpers
# ---------------------------------------------------------------------------


def _x_label(x: float) -> str:
    """Return a human-readable lateral position label."""
    fraction = x / COURT_WIDTH
    if fraction < 0.2:
        return "near the left sideline"
    elif fraction < 0.4:
        return "left of center"
    elif fraction < 0.6:
        return "near center"
    elif fraction < 0.8:
        return "right of center"
    else:
        return "near the right sideline"


def _our_zone(y: float) -> str:
    """Zone label for a player/ball on our side (y >= NET_Y)."""
    dist_from_net = y - NET_Y  # 0 at net, positive moving to our baseline
    if dist_from_net <= 1:
        return "at the kitchen line"
    elif y <= KITCHEN_NEAR:
        # Between net and our kitchen line — this is the NVZ on our side
        return f"{dist_from_net:.0f}ft from the net (in the kitchen)"
    elif y <= KITCHEN_NEAR + 2:
        return "just behind the kitchen line"
    elif y <= NET_Y + 10:
        return f"{dist_from_net:.0f}ft behind the kitchen line"
    elif y <= NET_Y + 18:
        return "in the transition zone (mid-court)"
    else:
        return "at the baseline"


def _opp_zone(y: float) -> str:
    """Zone label for an opponent (y <= NET_Y)."""
    dist_from_net = NET_Y - y
    if dist_from_net <= 1:
        return "at the kitchen line"
    elif y >= KITCHEN_FAR:
        return f"{dist_from_net:.0f}ft from the net (in the kitchen)"
    elif y >= KITCHEN_FAR - 2:
        return "just behind their kitchen line"
    elif y >= NET_Y - 10:
        return f"{dist_from_net:.0f}ft behind their kitchen line"
    else:
        return "at the baseline"


def _ball_zone(y: float) -> str:
    """Zone label for the ball."""
    if NET_Y <= y <= KITCHEN_NEAR:
        return "in our kitchen"
    elif y > KITCHEN_NEAR:
        return f"{y - NET_Y:.0f}ft on our side of the net"
    elif NET_Y - 1 <= y < NET_Y:
        return "just over the net on the opponent side"
    else:
        return f"{NET_Y - y:.0f}ft into the opponent's court"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def describe_player(
    x: float,
    y: float,
    role: Literal["my_left", "my_right", "opp_left", "opp_right"],
    my_side: Literal["left", "right"] = "left",
) -> str:
    """
    Return a natural-language description of one player's position.

    *role* is the key from the GameState players dict.
    *my_side* indicates which player is "ME" (left or right).
    """
    is_ours = role.startswith("my_")
    is_me = (role == "my_left" and my_side == "left") or (
        role == "my_right" and my_side == "right"
    )

    lateral = _x_label(x)
    zone = _our_zone(y) if is_ours else _opp_zone(y)

    if is_me:
        label = "You (ME)"
    elif role == "my_left":
        label = "Your partner (left side)"
    elif role == "my_right":
        label = "Your partner (right side)"
    elif role == "opp_left":
        label = "Opponent left"
    else:
        label = "Opponent right"

    return f"{label}: {zone}, {lateral}"


def describe_ball(ball: dict) -> str:
    """
    Return a natural-language description of the ball's position and parameters.

    ball = {"x": float, "y": float, "height": str, "speed": str, "spin": str|None}
    """
    x, y = ball["x"], ball["y"]
    lateral = _x_label(x)
    zone = _ball_zone(y)

    parts = [f"Ball: {zone}, {lateral}"]
    parts.append(f"Height: {ball['height']}")
    parts.append(f"Speed: {ball['speed']}")
    if ball.get("spin"):
        parts.append(f"Spin: {ball['spin']}")

    return " | ".join(parts)


def describe_situation(game_state: dict) -> str:
    """
    Convert a full GameState dict into a multi-line natural-language situation summary.

    Used both as a retrieval query and as part of the Claude prompt.
    """
    my_side: str = game_state.get("my_side", "left")
    players = game_state["players"]
    ball = game_state["ball"]

    lines = ["--- Tactical Situation ---"]

    for role, pos in players.items():
        lines.append(describe_player(pos["x"], pos["y"], role, my_side))

    lines.append(describe_ball(ball))

    # Infer high-level tactical context
    lines.append("")
    lines.append(_tactical_context(game_state, my_side))

    return "\n".join(lines)


def make_retrieval_query(game_state: dict) -> str:
    """
    Build a compact query string for ChromaDB similarity search.

    Focuses on the tactically relevant elements rather than raw coordinates.
    """
    my_side = game_state.get("my_side", "left")
    players = game_state["players"]
    ball = game_state["ball"]

    my_left_y = players["my_left"]["y"]
    my_right_y = players["my_right"]["y"]
    opp_left_y = players["opp_left"]["y"]
    opp_right_y = players["opp_right"]["y"]
    ball_y = ball["y"]

    parts = []

    # Our team zone
    our_avg_y = (my_left_y + my_right_y) / 2
    if our_avg_y <= KITCHEN_NEAR + 1:
        parts.append("both players at kitchen line")
    elif our_avg_y <= NET_Y + 10:
        parts.append("team in transition zone approaching kitchen")
    else:
        parts.append("team at baseline")

    # Opponent zone
    opp_avg_y = (opp_left_y + opp_right_y) / 2
    if opp_avg_y >= KITCHEN_FAR - 1:
        parts.append("opponents at kitchen line")
    elif opp_avg_y >= NET_Y - 10:
        parts.append("opponents in transition")
    else:
        parts.append("opponents at their baseline")

    # Ball zone
    if NET_Y <= ball_y <= KITCHEN_NEAR:
        parts.append("ball in kitchen")
    elif ball_y > KITCHEN_NEAR:
        dist = ball_y - NET_Y
        parts.append(f"ball {dist:.0f}ft from net on our side")

    # Ball params
    parts.append(f"{ball['height']} ball")
    parts.append(f"{ball['speed']} speed")
    if ball.get("spin"):
        parts.append(f"{ball['spin']} spin")

    return ", ".join(parts)


def _tactical_context(game_state: dict, my_side: str) -> str:
    """One-line tactical summary for the top of the Claude prompt."""
    players = game_state["players"]
    ball = game_state["ball"]

    our_avg_y = (players["my_left"]["y"] + players["my_right"]["y"]) / 2
    opp_avg_y = (players["opp_left"]["y"] + players["opp_right"]["y"]) / 2

    if our_avg_y <= KITCHEN_NEAR + 1 and opp_avg_y >= KITCHEN_FAR - 1:
        phase = "Full kitchen battle — both teams at the NVZ line."
    elif our_avg_y > NET_Y + 15:
        phase = "Transition phase — your team is working up from the baseline."
    elif our_avg_y > KITCHEN_NEAR + 2:
        phase = "Transition zone — approaching the kitchen line."
    else:
        phase = "Mixed positioning."

    height = ball["height"]
    if height == "low":
        attack = "Ball is low — reset or dink recommended over attacking."
    elif height == "high":
        attack = "Ball is high — attack or speed-up opportunity."
    else:
        attack = "Ball is mid-height — evaluate carefully before attacking."

    return f"Phase: {phase} {attack}"
