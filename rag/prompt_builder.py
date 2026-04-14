"""
Builds the full Claude API prompt from a GameState and retrieved chunks.

Output is a dict with "system" and "user" keys, matching Anthropic SDK
message format. The system prompt establishes the pickleball expert persona.
The user message contains the situation + retrieved context + output spec.
"""

from position_describer import describe_situation

SYSTEM_PROMPT = """\
You are an expert pickleball coach and strategist with deep knowledge of doubles play,
kitchen tactics, shot mechanics, and rally construction. You analyze court positions and
ball parameters to recommend tactically sound shot sequences.

When given a court situation, you respond with EXACTLY 3 shot recommendations. Each
recommendation includes a 3-shot rally sequence showing what you should hit, how the
opponent is likely to respond based on their actual positions, and your follow-up.

You always ground your advice in the specific positions and ball parameters given.
You never recommend shots that are physically implausible given the described positions.
"""

OUTPUT_FORMAT = """\
Respond with a JSON array of exactly 3 recommendation objects. Each object must have:
- "name": short name for the shot strategy (e.g., "Cross-Court Dink")
- "why": 1-2 sentences explaining why this shot fits the situation
- "rally": array of exactly 3 objects, each with:
  - "shot": integer (1, 2, or 3)
  - "who": "You" | "Your partner" | "Opponent L" | "Opponent R"
  - "action": what they do (verb phrase, e.g., "Soft cross-court dink to opponent's backhand")
  - "result": tactical outcome (e.g., "Ball lands near opponent's feet, forcing a reset")

Return only the JSON array — no markdown fences, no extra commentary.
"""


def build_prompt(game_state: dict, chunks: list[dict]) -> dict:
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

    user_message = f"""{situation}

{context_section}

--- Task ---
Based on the court situation above and the strategy context provided, recommend the 3 best
shot strategies for this moment in the rally.

{OUTPUT_FORMAT}"""

    return {
        "system": SYSTEM_PROMPT,
        "user": user_message,
    }
