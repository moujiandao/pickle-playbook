"""
llm_judge.py — LLM-as-judge scorer for strategy recommendations.

Asks claude-sonnet-4-6 to evaluate a recommendation on three dimensions:
  strategic_soundness  1-5  Is the shot choice strategically sound?
  reasoning_quality    1-5  Does the reasoning show real pickleball understanding?
  specificity          1-5  Is it specific to this scenario, not generic advice?

A result passes if the average score >= 3.0 (60% of max).
Score is normalized to 0.0–1.0 ((avg - 1) / 4).
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass

_FENCE_RE = re.compile(r"```(?:json)?\s*|\s*```", re.MULTILINE)
_JSON_BLOCK_RE = re.compile(r"\{[^{}]*\}", re.DOTALL)
_PASS_THRESHOLD = 3.0
_MODEL = "claude-sonnet-4-6"


@dataclass
class JudgeResult:
    passed: bool
    score: float              # 0.0–1.0 normalized average
    strategic_soundness: int  # 1-5
    reasoning_quality: int    # 1-5
    specificity: int          # 1-5
    notes: str


def score_response(response: list[dict], expected: dict) -> JudgeResult:
    """Score a /api/analyze response list against the golden expected fields."""
    try:
        import anthropic
    except ImportError as e:
        raise RuntimeError("anthropic SDK not installed; run: pip install anthropic") from e

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set")

    client = anthropic.Anthropic(api_key=api_key)
    prompt = build_judge_prompt(response, expected)

    last_exc: Exception | None = None
    for attempt in range(3):
        message = client.messages.create(
            model=_MODEL,
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = message.content[0].text
        try:
            return parse_judge_output(raw)
        except ValueError as exc:
            last_exc = exc

    raise ValueError(f"Judge returned unparseable output after 3 attempts: {last_exc}")


def build_judge_prompt(response: list[dict], expected: dict) -> str:
    rec_text = "\n\n".join(
        f"Shot: {r.get('name', '?')}\nWhy: {r.get('why', '?')}"
        for r in response
    )
    return f"""You are evaluating a pickleball shot recommendation system.

EXPERT EXPECTS:
- Best shot: {expected['primary_shot']}
- Acceptable alternatives: {', '.join(expected.get('acceptable_alternatives', []))}
- Reasoning should mention: {', '.join(expected.get('reasoning_must_mention', []))}

SYSTEM RECOMMENDED:
{rec_text}

Rate on a 1–5 scale (1=poor, 5=excellent):
- strategic_soundness: Is the shot choice strategically sound for this situation?
- reasoning_quality: Does the reasoning demonstrate real pickleball understanding?
- specificity: Is the advice specific to this scenario, or generic boilerplate?

Return JSON only, no extra text:
{{"strategic_soundness": N, "reasoning_quality": N, "specificity": N, "notes": "one sentence"}}"""


def parse_judge_output(raw: str) -> JudgeResult:
    """Parse raw Claude output into a JudgeResult. Raises ValueError on bad output."""
    cleaned = _FENCE_RE.sub("", raw).strip()

    match = _JSON_BLOCK_RE.search(cleaned)
    if not match:
        raise ValueError(f"No JSON object found in judge output: {raw[:120]!r}")

    data = json.loads(match.group())

    for field in ("strategic_soundness", "reasoning_quality", "specificity"):
        if field not in data:
            raise ValueError(f"Judge output missing field: {field}")
        val = int(data[field])
        if not (1 <= val <= 5):
            raise ValueError(f"Judge score out of range: {field}={val}")

    ss = int(data["strategic_soundness"])
    rq = int(data["reasoning_quality"])
    sp = int(data["specificity"])
    avg = (ss + rq + sp) / 3

    return JudgeResult(
        passed=avg >= _PASS_THRESHOLD,
        score=round((avg - 1) / 4, 3),
        strategic_soundness=ss,
        reasoning_quality=rq,
        specificity=sp,
        notes=str(data.get("notes", "")),
    )
