"""llm_judge.py — Blind LLM-as-judge scorer for strategy recommendations.

The judge sees the game state + recommendations ONLY. It does NOT see the
expected primary shot, acceptable alternatives, or must-mention keywords.
This eliminates reference leakage — the judge can no longer rationalize a
wrong recommendation as "matching what the expert expected".

Dimensions:
  Likert (1-5):
    strategic_soundness     Is the shot choice strategically sound for this state?
    reasoning_quality       Does the reasoning show real pickleball understanding?
    specificity             Specific to this scenario, not generic advice?
  Binary:
    skill_level_feasible    Can a player at the stated skill level realistically
                            execute the recommended primary shot?

Pass criterion:
  avg(Likert) >= 3.0 AND min(Likert) >= 2 AND skill_level_feasible == True.

Model is selectable (Sonnet default) to support cross-check runs on Opus for
judge-bias calibration.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Any

_FENCE_RE = re.compile(r"```(?:json)?\s*|\s*```", re.MULTILINE)
_JSON_BLOCK_RE = re.compile(r"\{[^{}]*\}", re.DOTALL)
_PASS_THRESHOLD = 3.0

MODEL_SONNET = "claude-sonnet-4-6"
MODEL_OPUS = "claude-opus-4-6"
_DEFAULT_MODEL = MODEL_SONNET


@dataclass
class JudgeResult:
    passed: bool
    score: float                  # 0.0–1.0 normalized Likert average
    strategic_soundness: int      # 1-5
    reasoning_quality: int        # 1-5
    specificity: int              # 1-5
    skill_level_feasible: bool    # True if shot is executable at stated level
    notes: str
    model: str                    # which judge model produced this score


def score_response(
    response: list[dict],
    state: dict,
    skill_level: str | float,
    model: str = _DEFAULT_MODEL,
) -> JudgeResult:
    """Blind-grade a /api/analyze response against the game state only.

    `state` is the eval-schema state dict (not GameState). `expected` is
    intentionally NOT a parameter — blind grading means the judge does not
    see the golden expert answer.
    """
    try:
        import anthropic
    except ImportError as e:
        raise RuntimeError("anthropic SDK not installed; run: pip install anthropic") from e

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set")

    client = anthropic.Anthropic(api_key=api_key)
    prompt = build_judge_prompt(response, state, skill_level)

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
    """Render the eval-schema state dict as a structured block for the judge.

    Uses zone strings (e.g. 'left_kitchen') as-is rather than translating to
    natural language — keeps the judge's view of the state independent of
    the strategy engine's tactical descriptions.
    """
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


def build_judge_prompt(response: list[dict], state: dict, skill_level: str | float) -> str:
    """Build the blind-grade prompt. State only — no expected answer leaks in."""
    rec_text = "\n\n".join(
        f"Shot: {r.get('name', '?')}\nWhy: {r.get('why', '?')}"
        for r in response
    )
    state_block = _format_state(state)

    return f"""You are evaluating a pickleball shot recommendation system.

Grade the recommendations BLIND — judge them on pickleball merit alone from the
state below. You are NOT given an expert's preferred answer; any shot that is
strategically sound for this state should score well regardless of whether it
matches some canonical preference.

COORDINATE LEGEND
  Court is 20ft wide (x), 44ft long (y). y=0 is the opponents' baseline,
  y=22 is the net, y=44 is your baseline. x=0 is the left sideline, x=20
  is the right sideline. Zones: '{{side}}_kitchen' ≈ at the kitchen line,
  '{{side}}_transition' ≈ midway, '{{side}}_baseline' ≈ deep.

GAME STATE
{state_block}

SYSTEM RECOMMENDED
{rec_text}

Rate on a 1-5 scale (1=poor, 5=excellent):
- strategic_soundness: Is the primary shot choice strategically sound given
  ball height/speed/position and player positions? Penalize shots that
  concede offense, target impossible locations, or misread the situation.
- reasoning_quality: Does the "Why" demonstrate real pickleball understanding
  (ball height → attackability, kitchen positioning, offense vs defense)?
  Penalize generic advice that would fit any scenario.
- specificity: Is the advice specific to THIS state (uses ball position,
  opponent positions, height/speed), or generic boilerplate?

Plus one binary call:
- skill_level_feasible (true/false): Can a {skill_level} player realistically
  execute the recommended primary shot?
  What each level can reliably execute:
    3.0-3.5  basic drives, drops, dinks, simple volleys.
             NOT reliable: topspin rolls, Ernes, ATPs, precision spin shots.
    4.0-4.5  add: topspin rolls, purposeful resets under pressure, intentional
             body shots, attack patterns. Ernes possible but not reliable.
    5.0+     Ernes, ATPs, stacking mid-rally adjustments, opponent-specific
             exploits — all in repertoire.
  If the primary shot is beyond what this level can reliably execute → false.
  Judge only on physical/technical executability, not shot-choice wisdom.

Return JSON only, no extra text:
{{"strategic_soundness": N, "reasoning_quality": N, "specificity": N, "skill_level_feasible": true, "notes": "one sentence"}}"""


def parse_judge_output(raw: str, model: str = _DEFAULT_MODEL) -> JudgeResult:
    """Parse raw Claude output into a JudgeResult. Raises ValueError on bad output."""
    cleaned = _FENCE_RE.sub("", raw).strip()

    match = _JSON_BLOCK_RE.search(cleaned)
    if not match:
        raise ValueError(f"No JSON object found in judge output: {raw[:120]!r}")

    data: dict[str, Any] = json.loads(match.group())

    for field in ("strategic_soundness", "reasoning_quality", "specificity"):
        if field not in data:
            raise ValueError(f"Judge output missing field: {field}")
        val = int(data[field])
        if not (1 <= val <= 5):
            raise ValueError(f"Judge score out of range: {field}={val}")

    if "skill_level_feasible" not in data:
        raise ValueError("Judge output missing field: skill_level_feasible")
    if not isinstance(data["skill_level_feasible"], bool):
        raise ValueError(
            f"skill_level_feasible must be bool, got {type(data['skill_level_feasible']).__name__}"
        )

    ss = int(data["strategic_soundness"])
    rq = int(data["reasoning_quality"])
    sp = int(data["specificity"])
    feasible = bool(data["skill_level_feasible"])
    likert = (ss, rq, sp)
    avg = sum(likert) / len(likert)
    passed = avg >= _PASS_THRESHOLD and min(likert) >= 2 and feasible

    return JudgeResult(
        passed=passed,
        score=round((avg - 1) / 4, 3),
        strategic_soundness=ss,
        reasoning_quality=rq,
        specificity=sp,
        skill_level_feasible=feasible,
        notes=str(data.get("notes", "")),
        model=model,
    )
