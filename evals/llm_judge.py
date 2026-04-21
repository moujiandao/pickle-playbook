"""
llm_judge.py — LLM-as-judge scorer for strategy recommendations.

Given a golden scenario's expected fields and the actual API response,
asks Claude to score the response on three dimensions:

  1. shot_type_match   (bool)   — recommended shot matches expected shot type
  2. keyword_coverage (float)  — fraction of must_mention keywords present
  3. reasoning_quality (float) — 0.0–1.0, does the "why" field explain the tactic clearly?

Overall score = average of the three normalized dimensions.

Claude is prompted with a structured rubric to minimise variance between runs.
The judge uses claude-haiku-4-5 for cost efficiency on large golden sets.

TODO: implement score_response(response, expected) -> JudgeResult
TODO: implement build_judge_prompt(response, expected) -> str
TODO: implement parse_judge_output(raw: str) -> JudgeResult
TODO: add retry logic for malformed judge output (max 2 retries)
"""

from dataclasses import dataclass


@dataclass
class JudgeResult:
    passed: bool
    score: float                # 0.0 – 1.0
    shot_type_match: bool
    keyword_coverage: float     # 0.0 – 1.0
    reasoning_quality: float    # 0.0 – 1.0
    reasoning_coverage: bool    # True if reasoning_quality >= 0.6
    judge_notes: str


def score_response(response: list[dict], expected: dict) -> JudgeResult:
    """Score a /api/analyze response against the golden expected fields."""
    # TODO: build prompt, call Claude, parse result
    raise NotImplementedError


def build_judge_prompt(response: list[dict], expected: dict) -> str:
    """Construct the rubric prompt sent to the LLM judge."""
    # TODO: format response as readable text
    # TODO: inject expected.must_mention, expected.shot_type, expected.positioning_cue
    # TODO: ask Claude to return JSON: { shot_type_match, keyword_coverage, reasoning_quality, notes }
    raise NotImplementedError


def parse_judge_output(raw: str) -> JudgeResult:
    """Parse raw Claude output into a JudgeResult. Raises ValueError on bad output."""
    # TODO: extract JSON block from raw string
    # TODO: validate required fields
    # TODO: compute passed = score >= 0.7
    raise NotImplementedError
