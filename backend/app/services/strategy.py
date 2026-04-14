"""Orchestrates RAG retrieval -> Claude API -> 3-shot rally recommendations."""

import json
import os
import re

import anthropic
from dotenv import load_dotenv

from rag.prompt_builder import build_prompt, get_system_prompt
from rag.retrieval import retrieve

load_dotenv()

_client: anthropic.AsyncAnthropic | None = None


def _get_client() -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:
        _client = anthropic.AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    return _client


def _build_position_query(game_state: dict) -> str:
    """Produce a concise query string for RAG retrieval from the game state."""
    ball = game_state["ball"]
    players = game_state["players"]

    # Determine tactical context from positions
    parts = []

    # Ball position hints
    if ball["height"] == "low":
        parts.append("low ball kitchen dink")
    elif ball["height"] == "high":
        parts.append("high ball overhead attack")
    else:
        parts.append("mid ball transition")

    # Speed
    if ball["speed"] == "slow":
        parts.append("soft game dinking")
    else:
        parts.append("speed up attack drive")

    # Are my players at the kitchen?
    my_left_y = players["my_left"]["y"]
    my_right_y = players["my_right"]["y"]
    if my_left_y <= 30 and my_right_y <= 30:
        parts.append("both at kitchen line")
    else:
        parts.append("transition zone positioning")

    return " ".join(parts)


async def recommend(game_state: dict) -> list[dict]:
    """Return 3 rally recommendations for the given game state."""
    query = _build_position_query(game_state)
    chunks = retrieve(query, k=5)
    user_prompt = build_prompt(game_state, chunks)
    system_prompt = get_system_prompt()

    client = _get_client()

    response = await client.messages.create(
        model="claude-opus-4-6",
        max_tokens=4096,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )

    # Extract the text content
    text = next(
        (block.text for block in response.content if block.type == "text"),
        "[]",
    )

    # Strip any markdown fencing Claude might add despite instructions
    text = re.sub(r"^```(?:json)?\s*", "", text.strip())
    text = re.sub(r"\s*```$", "", text)

    try:
        recommendations = json.loads(text)
    except json.JSONDecodeError:
        # Fallback: return empty list so the endpoint stays functional
        recommendations = []

    return recommendations
