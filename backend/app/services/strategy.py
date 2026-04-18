"""Strategy engine.

Orchestrates RAG retrieval + Claude generation to produce shot recommendations.
Falls back to a deterministic heuristic when the API key, RAG modules, or
ChromaDB index are not available, so the endpoint stays usable in tests and
in offline development.
"""

from __future__ import annotations

import json
import logging
import os
import re
import sys
from pathlib import Path

from app.schemas.game_state import GameState, RallyStep, ShotRecommendation
from app.services.position_describer import (
    ball_zone,
    describe_position,
    lateral_label,
    zone_of,
)

logger = logging.getLogger(__name__)

_RECS_SCHEMA = {
    "type": "object",
    "properties": {
        "recommendations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "why": {"type": "string"},
                    "rally": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "shot": {"type": "integer"},
                                "who": {"type": "string"},
                                "action": {"type": "string"},
                                "result": {"type": "string"},
                            },
                            "required": ["shot", "who", "action", "result"],
                            "additionalProperties": False,
                        },
                    },
                },
                "required": ["name", "why", "rally"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["recommendations"],
    "additionalProperties": False,
}

# The rag/ package uses absolute imports between its own modules
# (e.g. `from embeddings import embed`), so we put its directory on sys.path
# rather than importing it as a package.
_env_rag_dir = os.environ.get("PICKLE_RAG_DIR")
_RAG_DIR = (
    Path(_env_rag_dir).expanduser().resolve()
    if _env_rag_dir
    else Path(__file__).resolve().parents[3] / "rag"
)
if _RAG_DIR.is_dir() and str(_RAG_DIR) not in sys.path:
    sys.path.insert(0, str(_RAG_DIR))


def recommend(state: GameState) -> list[ShotRecommendation]:
    """Return shot recommendations for the given game state.

    Uses the RAG + Claude pipeline when an Anthropic API key is configured.
    Falls back to the deterministic heuristic when the key, the RAG modules,
    or any step in the live pipeline is unavailable.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return _heuristic_recommend(state)

    anthropic_mod = _try_import_anthropic()
    retrieve_fn, build_prompt_fn = _try_import_rag()
    if anthropic_mod is None or retrieve_fn is None or build_prompt_fn is None:
        return _heuristic_recommend(state)

    try:
        state_dict = state.model_dump()
        try:
            chunks = retrieve_fn(state_dict, k=5)
        except Exception as exc:
            logger.warning("RAG retrieval failed, continuing with no context: %s", exc)
            chunks = []

        prompt = build_prompt_fn(state_dict, chunks)
        client = anthropic_mod.Anthropic(api_key=api_key)
        model = os.environ.get("ANTHROPIC_MODEL", "claude-opus-4-6")

        message = client.messages.create(
            model=model,
            max_tokens=4096,
            system=prompt["system"],
            messages=[{"role": "user", "content": prompt["user"]}],
            output_config={"format": {"type": "json_schema", "schema": _RECS_SCHEMA}},
        )
        text = "".join(
            block.text
            for block in message.content
            if getattr(block, "type", "") == "text"
        )
        return _parse_recommendations(text)
    except Exception as exc:
        logger.exception("Claude pipeline failed, falling back to heuristic: %s", exc)
        return _heuristic_recommend(state)


def _try_import_rag():
    try:
        from retrieval import retrieve  # type: ignore
        from prompt_builder import build_prompt  # type: ignore
        return retrieve, build_prompt
    except Exception as exc:
        logger.warning("RAG modules unavailable: %s", exc)
        return None, None


def _try_import_anthropic():
    try:
        import anthropic  # type: ignore
        return anthropic
    except Exception as exc:
        logger.warning("anthropic SDK unavailable: %s", exc)
        return None


_FENCE_RE = re.compile(r"```(?:json)?\s*|\s*```", re.MULTILINE)


def _strip_markdown_fences(text: str) -> str:
    return _FENCE_RE.sub("", text).strip()


def _parse_recommendations(text: str) -> list[ShotRecommendation]:
    cleaned = _strip_markdown_fences(text)
    data = json.loads(cleaned)
    items = data.get("recommendations", data) if isinstance(data, dict) else data
    if not isinstance(items, list):
        raise ValueError("Claude response was not a JSON array")
    return [ShotRecommendation.model_validate(item) for item in items]


# ---------------------------------------------------------------------------
# Heuristic fallback — used when the live RAG+Claude pipeline is unavailable.
# Keeps the analyze endpoint usable in tests and offline development.
# ---------------------------------------------------------------------------


def _opponent_pressure(state: GameState) -> str:
    opp_left_zone = zone_of(state.players.opp_left.y, "far")
    opp_right_zone = zone_of(state.players.opp_right.y, "far")
    if opp_left_zone == "kitchen" and opp_right_zone == "kitchen":
        return "both_kitchen"
    if opp_left_zone == "baseline" or opp_right_zone == "baseline":
        return "one_back"
    return "mixed"


def _middle_gap(state: GameState) -> float:
    return abs(state.players.opp_right.x - state.players.opp_left.x)


def _heuristic_recommend(state: GameState) -> list[ShotRecommendation]:
    b = state.ball
    zone = ball_zone(b.y)
    ball_where = describe_position(b.x, b.y, "near")
    opp_pressure = _opponent_pressure(state)
    gap = _middle_gap(state)
    ball_side = lateral_label(b.x)

    me_label = "You"
    partner_label = "Partner"

    recs: list[ShotRecommendation] = []

    if zone == "kitchen" and b.height == "low":
        why_parts = [f"Ball is low in the kitchen ({ball_where})."]
        if opp_pressure == "both_kitchen":
            why_parts.append("Both opponents are at the kitchen line, so attacks are low-percentage.")
        cross_target = "right" if ball_side == "left sideline" else "left"
        recs.append(
            ShotRecommendation(
                name="Cross-Court Dink",
                why=" ".join(why_parts) + " A cross-court dink has the longest available landing zone and pulls them wide.",
                rally=[
                    RallyStep(
                        shot=1, who=me_label,
                        action=f"Soft cross-court dink to the {cross_target} side of their kitchen.",
                        result="Lands just over the net, forcing a stretched reply.",
                    ),
                    RallyStep(
                        shot=2, who="Opponent",
                        action=f"Opponent on the {cross_target} dinks back, likely to your middle.",
                        result="Ball pops up slightly as they reach wide.",
                    ),
                    RallyStep(
                        shot=3, who=partner_label,
                        action="Partner steps in and redirects the dink to the open middle seam.",
                        result="Splits the defenders and forces a defensive reset.",
                    ),
                ],
            )
        )
        if gap >= 8:
            recs.append(
                ShotRecommendation(
                    name="Middle Dink Probe",
                    why=f"Opponents are spread ({gap:.0f}ft apart). A dink up the middle creates confusion over who takes it.",
                    rally=[
                        RallyStep(shot=1, who=me_label, action="Controlled dink into the middle of their kitchen.", result="Lands between both opponents, causing hesitation."),
                        RallyStep(shot=2, who="Opponent", action="One opponent reaches across and pops the ball up.", result="Weak reply floats above net height."),
                        RallyStep(shot=3, who=me_label, action="Step in and put the ball away with a controlled roll.", result="Point won on the attack."),
                    ],
                )
            )
        recs.append(
            ShotRecommendation(
                name="Reset and Reload",
                why="If the angle is tight, a soft reset into the kitchen keeps you in the point without overcommitting.",
                rally=[
                    RallyStep(shot=1, who=me_label, action="Cushioned reset into the center of their kitchen.", result="Neutralizes pace, buys time to reset your feet."),
                    RallyStep(shot=2, who="Opponent", action="Opponent dinks back to continue the exchange.", result="Neutral kitchen rally."),
                    RallyStep(shot=3, who=partner_label, action="Partner takes over the dink battle from a balanced stance.", result="Maintains neutral rally position."),
                ],
            )
        )
        return recs[:3]

    if zone == "kitchen" and b.height in ("mid", "high"):
        recs.append(
            ShotRecommendation(
                name="Speed-Up Attack",
                why=f"Ball is at {b.height} height in the kitchen ({ball_where}). That's attackable before it drops.",
                rally=[
                    RallyStep(shot=1, who=me_label, action="Short backswing speed-up at the opponent's hip.", result="Forces a reactive, high reply."),
                    RallyStep(shot=2, who="Opponent", action="Opponent blocks upward, ball floats.", result="Ball sits up in the kitchen zone."),
                    RallyStep(shot=3, who=partner_label, action="Partner crashes in and puts the floater away.", result="Point ends on the put-away."),
                ],
            )
        )
        recs.append(
            ShotRecommendation(
                name="Topspin Roll",
                why="Rolling topspin keeps the ball low over the net while still carrying bite.",
                rally=[
                    RallyStep(shot=1, who=me_label, action="Low-to-high topspin roll aimed at the far shoulder.", result="Dips fast into the kitchen, hard to read."),
                    RallyStep(shot=2, who="Opponent", action="Opponent pops the roll up off the paddle face.", result="Short, floaty return."),
                    RallyStep(shot=3, who=me_label, action="Finish overhead into the open court.", result="Unanswered winner."),
                ],
            )
        )
        return recs

    if zone == "transition":
        recs.append(
            ShotRecommendation(
                name="Third-Shot Drop",
                why=f"Ball is in the transition zone ({ball_where}). A drop buys time to get to the kitchen.",
                rally=[
                    RallyStep(shot=1, who=me_label, action="Soft third-shot drop landing in the middle of their kitchen.", result="Forces them to hit up; you advance."),
                    RallyStep(shot=2, who="Opponent", action="Opponent dinks back crosscourt.", result="Neutral kitchen exchange begins."),
                    RallyStep(shot=3, who=partner_label, action="Partner and you reach the kitchen line together.", result="Even kitchen battle established."),
                ],
            )
        )
        if opp_pressure == "one_back":
            recs.append(
                ShotRecommendation(
                    name="Drive at the Deep Opponent",
                    why="One opponent is still back. Drive at their feet before they establish position.",
                    rally=[
                        RallyStep(shot=1, who=me_label, action="Flat drive at the feet of the deeper opponent.", result="Forces a tough half-volley."),
                        RallyStep(shot=2, who="Opponent", action="Deep opponent blocks the drive short and high.", result="Ball sits up in the transition zone."),
                        RallyStep(shot=3, who=partner_label, action="Partner steps in and attacks the floater.", result="Put-away into open court."),
                    ],
                )
            )
        return recs

    # zone == "baseline"
    recs.append(
        ShotRecommendation(
            name="Third-Shot Drop from the Baseline",
            why=f"Ball is near your baseline ({ball_where}). A controlled drop is the highest-percentage advance.",
            rally=[
                RallyStep(shot=1, who=me_label, action="Compact third-shot drop to the middle of their kitchen.", result="Gives you time to advance to the transition zone."),
                RallyStep(shot=2, who="Opponent", action="Opponent dinks the drop back to your partner's side.", result="Neutral kitchen dink begins."),
                RallyStep(shot=3, who=partner_label, action="Partner resets into the kitchen and holds position.", result="Both teams at the kitchen line."),
            ],
        )
    )
    if b.speed == "fast":
        recs.append(
            ShotRecommendation(
                name="Topspin Drive",
                why="A fast ball from the baseline can be converted into a heavy topspin drive that dips at their feet.",
                rally=[
                    RallyStep(shot=1, who=me_label, action="Topspin drive at the weaker opponent's hip.", result="Forces a defensive block."),
                    RallyStep(shot=2, who="Opponent", action="Opponent blocks the drive short.", result="Ball lands mid-court."),
                    RallyStep(shot=3, who=me_label, action="Follow the drive in and put away the short block.", result="Aggressive advance to the kitchen."),
                ],
            )
        )
    return recs
