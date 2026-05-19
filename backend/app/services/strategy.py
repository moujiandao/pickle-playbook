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

# Sonnet 4.6 at medium effort is the speed/quality sweet spot for an
# interactive UI. Override via ANTHROPIC_MODEL env var to use Opus for harder
# scenarios (and pair with ANTHROPIC_EFFORT="high" for more reasoning depth).
_DEFAULT_MODEL = "claude-sonnet-4-6"
_DEFAULT_EFFORT = "medium"

# The rag/ package uses absolute imports between its own modules
# (e.g. `from embeddings import embed`), so we put its directory on sys.path
# rather than importing it as a package.
_EVALS_LIB_DIR = Path(__file__).resolve().parents[3] / "evals" / "lib"
if _EVALS_LIB_DIR.is_dir() and str(_EVALS_LIB_DIR) not in sys.path:
    sys.path.insert(0, str(_EVALS_LIB_DIR))


def recommend(state: GameState) -> tuple[list[ShotRecommendation], str | None]:
    """Return shot recommendations and an optional warning for the given game state.

    Uses the RAG + Claude pipeline when an Anthropic API key is configured.
    Falls back to the deterministic heuristic when the key, the RAG modules,
    or any step in the live pipeline is unavailable.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return (
            _heuristic_recommend(state),
            "ANTHROPIC_API_KEY not set; using deterministic heuristic.",
        )

    anthropic_mod = _try_import_anthropic()
    build_prompt_fn = _try_import_prompt_builder()
    if anthropic_mod is None:
        return (
            _heuristic_recommend(state),
            "anthropic SDK not installed; using deterministic heuristic.",
        )
    if build_prompt_fn is None:
        return (
            _heuristic_recommend(state),
            "prompt_builder not importable from evals/lib; using deterministic heuristic.",
        )

    try:
        state_dict = state.model_dump()
        chunks: list = []

        prompt = build_prompt_fn(state_dict, chunks, level=state_dict.get("skill_level"))
        client = anthropic_mod.Anthropic(api_key=api_key)
        model = os.environ.get("ANTHROPIC_MODEL", _DEFAULT_MODEL)

        # Cache the system prompt — it's identical across requests, so the
        # second + requests pay ~10% of the input price on the shared prefix.
        system_blocks = [
            {
                "type": "text",
                "text": prompt["system"],
                "cache_control": {"type": "ephemeral"},
            }
        ]

        effort = os.environ.get("ANTHROPIC_EFFORT", _DEFAULT_EFFORT)
        message = client.messages.create(
            model=model,
            max_tokens=8192,
            thinking={"type": "adaptive"},
            output_config={
                "format": {"type": "json_schema", "schema": _RECS_SCHEMA},
                "effort": effort,
            },
            system=system_blocks,
            messages=[{"role": "user", "content": prompt["user"]}],
        )
        text = "".join(
            block.text
            for block in message.content
            if getattr(block, "type", "") == "text"
        )
        recs = _parse_recommendations(text)
        return (recs, None)
    except Exception as exc:
        logger.exception("Claude pipeline failed, falling back to heuristic: %s", exc)
        warning = f"Claude pipeline failed; using heuristic fallback ({type(exc).__name__}: {exc})"
        return (_heuristic_recommend(state), warning)


def _try_import_prompt_builder():
    try:
        from prompt_builder import build_prompt  # type: ignore
        return build_prompt
    except Exception as exc:
        logger.warning("prompt_builder unavailable: %s", exc)
        return None


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
                    ],
                )
            )
        recs.append(
            ShotRecommendation(
                name="Reset and Reload",
                why="If the angle is tight, a soft reset into the kitchen keeps you in the point without overcommitting.",
                rally=[
                    RallyStep(shot=1, who=me_label, action="Cushioned reset into the center of their kitchen.", result="Neutralizes pace, buys time to reset your feet."),
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
                ],
            )
        )
        recs.append(
            ShotRecommendation(
                name="Topspin Roll",
                why="Rolling topspin keeps the ball low over the net while still carrying bite.",
                rally=[
                    RallyStep(shot=1, who=me_label, action="Low-to-high topspin roll aimed at the far shoulder.", result="Dips fast into the kitchen, hard to read."),
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
                ],
            )
        )
    return recs
