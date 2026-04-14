"""Build the Claude system prompt from game state + retrieved strategy chunks."""

import json

from app.services.position_describer import describe_position

# Near side is y > 22 (my side when my_side drives perspective)
_MY_SIDE_Y_CENTER = 33.0  # typical starting y for near-side players


def _game_state_to_text(game_state: dict) -> str:
    """Convert raw coordinate dict to tactical English."""
    players = game_state["players"]
    ball = game_state["ball"]
    my_side = game_state.get("my_side", "left")

    # Near side = higher y values (closer to y=44 baseline)
    my_left = describe_position(players["my_left"]["x"], players["my_left"]["y"], is_near_side=True)
    my_right = describe_position(players["my_right"]["x"], players["my_right"]["y"], is_near_side=True)
    opp_left = describe_position(players["opp_left"]["x"], players["opp_left"]["y"], is_near_side=False)
    opp_right = describe_position(players["opp_right"]["x"], players["opp_right"]["y"], is_near_side=False)
    ball_pos = describe_position(ball["x"], ball["y"], is_near_side=True)

    spin_str = ball.get("spin") or "flat"

    lines = [
        f"My team ({my_side} perspective):",
        f"  - My left player: {my_left}",
        f"  - My right player: {my_right}",
        f"Opponents:",
        f"  - Their left player: {opp_left}",
        f"  - Their right player: {opp_right}",
        f"Ball: {ball_pos}, height={ball['height']}, speed={ball['speed']}, spin={spin_str}",
    ]
    return "\n".join(lines)


def _format_chunks(chunks: list[dict]) -> str:
    if not chunks:
        return "No strategy context retrieved."
    sections = []
    for i, chunk in enumerate(chunks, 1):
        source = chunk.get("source", "unknown")
        content = chunk.get("content", "").strip()
        sections.append(f"[{i}] Source: {source}\n{content}")
    return "\n\n".join(sections)


SYSTEM_PROMPT = """\
You are a pickleball strategy expert. You will receive the current court position \
of all four players and the ball, plus relevant strategy excerpts from a coaching corpus.

Your task is to recommend 3 distinct tactical options, each with a 3-shot rally sequence.

Return ONLY a JSON array with exactly 3 objects. Each object must match this schema:
{
  "name": "<short tactic name>",
  "why": "<one sentence explaining why this tactic fits the current situation>",
  "rally": [
    {"shot": 1, "who": "<You|Partner|Opponent>", "action": "<what they do>", "result": "<outcome>"},
    {"shot": 2, "who": "<You|Partner|Opponent>", "action": "<what they do>", "result": "<outcome>"},
    {"shot": 3, "who": "<You|Partner|Opponent>", "action": "<what they do>", "result": "<outcome>"}
  ]
}

Do not include any text outside the JSON array. No markdown, no explanation.\
"""


def build_prompt(game_state: dict, chunks: list[dict]) -> str:
    """Assemble the full user message for the Claude API call."""
    situation = _game_state_to_text(game_state)
    context = _format_chunks(chunks)

    return (
        f"## Current Court Situation\n{situation}\n\n"
        f"## Strategy Context\n{context}\n\n"
        "Based on the situation and strategy context above, recommend 3 tactical options "
        "as a JSON array."
    )


def get_system_prompt() -> str:
    return SYSTEM_PROMPT
