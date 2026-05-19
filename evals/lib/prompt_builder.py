"""
Builds the full Claude API prompt from a GameState and retrieved chunks.

Output is a dict with "system" and "user" keys, matching Anthropic SDK
message format. The system prompt establishes the pickleball expert persona.
The user message contains the situation + retrieved context + output spec.
"""

from situation_describer import describe_situation

SYSTEM_PROMPT = """\
You are an expert pickleball coach and strategist with deep knowledge of doubles play,
kitchen tactics, shot mechanics, and rally construction. You analyze court positions and
ball parameters to recommend tactically sound shots.

When given a court situation, you respond with EXACTLY 3 shot recommendations. Each
recommendation describes a single shot — what you should hit and its immediate result.

You always ground your advice in the specific positions and ball parameters given.
You never recommend shots that are physically implausible given the described positions.
"""

OUTPUT_FORMAT = """\
Return only a JSON object with a "recommendations" key containing an array of exactly 3 \
recommendation objects. Each object must have "name" (string), "why" (string), and "rally" \
(array of exactly 1 object with "shot" (integer, always 1), "who" (string), "action" (string), \
"result" (string)).
"""


def build_prompt(game_state: dict, chunks: list[dict], level: str | None = None) -> dict:
    """
    Assemble the Claude API prompt.

    Returns {"system": str, "user": str} suitable for the Anthropic messages API.
    """
    situation = describe_situation(game_state)

    # Format retrieved context chunks
    if chunks:
        context_lines = ["--- Relevant Strategy Context ---"]
        for i, chunk in enumerate(chunks, 1):
            source = chunk.get("source", "unknown")
            text = chunk["text"].strip()
            context_lines.append(f"\n[{i}] Source: {source}\n{text}")
        context_section = "\n".join(context_lines)
    else:
        context_section = "--- No additional strategy context retrieved ---"

    level_note = f"\nThe player is rated {level}. Tailor shot complexity and terminology to this skill level." if level else ""

    user_message = f"""{situation}
{level_note}

{context_section}

--- Task ---
Based on the court situation above and the strategy context provided, recommend the 3 best
shot strategies for this moment in the rally.

{OUTPUT_FORMAT}"""

    return {
        "system": SYSTEM_PROMPT,
        "user": user_message,
    }
