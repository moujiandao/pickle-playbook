"""llm_judge.py — Blind LLM-as-judge for the one failure mode that needs it.

After two rounds of failure-mode review (see evals/failure_modes.md), four of
the five original modes have either become deterministic or been retired:

  M1 wrong shot family       → deterministic (shot_taxonomy.classify)
  M2 skill-level overreach   → retired round 2 (too narrow to be load-bearing)
  M3 state-blind reasoning   → retired round 2 (one Likert can't grade both
                                generic language and position-reasoning;
                                future replacement should be narrow binary
                                judges driven by real traces)
  M4 misreads ball state     → judge (this file)
  M5 wrong tactical mode     → deterministic (expected_tactical_mode)

So the judge's only job is M4. 1–5 Likert with concrete anchors at 1, 3, 5
to keep judges from drifting between runs. Pass criterion: `score >= 3`.

Blind grading: the judge sees state + recommendations only. Never the expert
answer. This eliminates the v1 risk where a judge could rationalize a bad
recommendation as "matching what was expected."
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Any

_FENCE_RE = re.compile(r"```(?:json)?\s*|\s*```", re.MULTILINE)
_JSON_BLOCK_RE = re.compile(r"\{[^{}]*\}", re.DOTALL)
_DIMENSION_PASS_THRESHOLD = 3  # ball_state_reading must clear this to pass

MODEL_SONNET = "claude-sonnet-4-6"
MODEL_OPUS = "claude-opus-4-6"
_DEFAULT_MODEL = MODEL_SONNET


@dataclass
class JudgeResult:
    ball_state_reading: int       # 1-5 (M4)
    m4_passed: bool               # ball_state_reading >= threshold
    passed: bool                  # alias for m4_passed (judge-level pass)
    score: float                  # 0.0–1.0 normalized for ranking/aggregation
    notes: str
    model: str


def score_response(
    response: list[dict],
    state: dict,
    skill_level: str | float,    # kept for backward signature compatibility; unused now
    model: str = _DEFAULT_MODEL,
) -> JudgeResult:
    """Blind-grade a /api/analyze response on M4 only.

    `state` is the eval-schema state dict. The expert answer is intentionally
    NOT a parameter — blind grading means the judge does not see the golden
    answer, so it can't rationalize a wrong call as "matching expectations".

    `skill_level` is unused by the judge (M2 was retired) but kept in the
    signature to avoid breaking the call site in run_eval.py.
    """
    del skill_level  # explicitly unused — silenced for linters
    try:
        import anthropic
    except ImportError as e:
        raise RuntimeError("anthropic SDK not installed; run: pip install anthropic") from e

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set")

    client = anthropic.Anthropic(api_key=api_key)
    prompt = build_judge_prompt(response, state)

    last_exc: Exception | None = None
    for _ in range(3):
        message = client.messages.create(
            model=model,
            max_tokens=256,
            temperature=0.0,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = message.content[0].text
        try:
            return parse_judge_output(raw, model=model)
        except ValueError as exc:
            last_exc = exc

    raise ValueError(f"Judge returned unparseable output after 3 attempts: {last_exc}")


def _format_state(state: dict) -> str:
    """Render the eval-schema state dict as a structured block for the judge."""
    ball = state.get("ball_position", {})
    spin = state.get("ball_spin")
    spin_line = f", spin={spin}" if spin else ""
    me_side = state.get("me_position", "").split("_")[0] or "?"

    return (
        f"- Your side: {me_side}\n"
        f"- Skill level: {state.get('skill_level', '?')}\n"
        f"- Positions:\n"
        f"    YOU:            {state.get('me_position', '?')}\n"
        f"    Your partner:   {state.get('partner_position', '?')}\n"
        f"    Opponent left:  {state.get('opp_left_position', '?')}\n"
        f"    Opponent right: {state.get('opp_right_position', '?')}\n"
        f"- Ball: x={ball.get('x', '?')}, y={ball.get('y', '?')}, "
        f"height={state.get('ball_height', '?')}, "
        f"speed={state.get('ball_speed', '?')}{spin_line}"
    )


def build_judge_prompt(response: list[dict], state: dict) -> str:
    """Build the blind-grade prompt for M4 only."""
    rec_text = "\n\n".join(
        f"Shot: {r.get('name', '?')}\nWhy: {r.get('why', '?')}"
        for r in response
    )
    state_block = _format_state(state)

    return f"""You are evaluating a pickleball shot recommendation system.

Grade BLIND on the merit of the recommendation alone. You are NOT given an
expert's preferred answer. One dimension, 1–5 with concrete anchors.

COORDINATE LEGEND
  Court is 20ft wide (x), 44ft long (y). y=0 is the opponents' baseline,
  y=22 is the net, y=44 is your baseline. x=0 is the left sideline, x=20
  is the right sideline. Zones: '{{side}}_kitchen' ≈ at the kitchen line,
  '{{side}}_transition' ≈ midway, '{{side}}_baseline' ≈ deep.

GAME STATE
{state_block}

SYSTEM RECOMMENDED
{rec_text}

DIMENSION — ball_state_reading (M4: misreads ball state)
  Does the recommended primary shot correctly match the offensive/defensive
  opportunity implied by the ball's height and speed? This is about reading
  the ball, not picking the optimal shot family.

  ANCHORS (rate 1, 3, or 5 if it fits cleanly; 2 or 4 if between):
    1 = Wrong. Recommendation contradicts ball physics. Examples:
        - Soft dink reset on a high slow ball at the kitchen (sitter — should attack)
        - Aggressive drive at the body on a low fast ball at transition (should defend)
        - Drop attempt on a high ball that is begging to be put away
    3 = Plausible. Recommendation isn't contradicted by the ball state, but
        the "Why" doesn't actually use ball height/speed in its reasoning.
        Got the right call by coincidence or generic prior, not by reading.
    5 = Correct. Recommendation explicitly matches the ball's offensive or
        defensive nature (height + speed), and the "Why" cites that read.

Return JSON only, no extra text:
{{"ball_state_reading": N, "notes": "one sentence describing the call"}}"""


def parse_judge_output(raw: str, model: str = _DEFAULT_MODEL) -> JudgeResult:
    """Parse raw Claude output into a JudgeResult. Raises ValueError on bad output."""
    cleaned = _FENCE_RE.sub("", raw).strip()

    match = _JSON_BLOCK_RE.search(cleaned)
    if not match:
        raise ValueError(f"No JSON object found in judge output: {raw[:120]!r}")

    data: dict[str, Any] = json.loads(match.group())

    if "ball_state_reading" not in data:
        raise ValueError("Judge output missing field: ball_state_reading")
    bsr = int(data["ball_state_reading"])
    if not (1 <= bsr <= 5):
        raise ValueError(f"Judge score out of range: ball_state_reading={bsr}")

    m4 = bsr >= _DIMENSION_PASS_THRESHOLD

    return JudgeResult(
        ball_state_reading=bsr,
        m4_passed=m4,
        passed=m4,
        score=round((bsr - 1) / 4, 3),
        notes=str(data.get("notes", "")),
        model=model,
    )
