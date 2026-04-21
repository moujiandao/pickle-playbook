#!/usr/bin/env python3
"""
run_eval.py — Batch eval runner for Pickle Playbook strategy recommendations.

Usage:
    python evals/run_eval.py evals/golden_scenarios.jsonl evals/results/baseline.json
    python evals/run_eval.py evals/golden_scenarios.jsonl evals/results/out.json --sample 10
    python evals/run_eval.py evals/golden_scenarios.jsonl evals/results/out.json --judge
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_EVALS_DIR = Path(__file__).resolve().parent
_BACKEND_DIR = _REPO_ROOT / "backend"

for _p in (_BACKEND_DIR, _EVALS_DIR):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

try:
    from tqdm import tqdm
except ImportError:
    def tqdm(iterable, **kwargs):  # type: ignore[misc]
        return iterable

# ── court layout constants ─────────────────────────────────────────────────
# eval schema uses zone names; these map to approximate x,y foot coordinates.
# y=0  opp baseline  |  y=15 opp kitchen  |  y=22 net  |  y=29 my kitchen  |  y=44 my baseline
_ZONE_Y_MY = {"kitchen": 29.0, "transition": 35.0, "baseline": 40.0}
_ZONE_Y_OPP = {"kitchen": 15.0, "transition": 9.0, "baseline": 4.0}
_SIDE_X = {"left": 5.0, "right": 15.0}


def _pos_xy(pos_str: str, team: str) -> tuple[float, float]:
    """'left_kitchen' + 'my'|'opp' → (x_ft, y_ft)."""
    side, zone = pos_str.split("_", 1)
    y_map = _ZONE_Y_MY if team == "my" else _ZONE_Y_OPP
    return _SIDE_X[side], y_map[zone]


def eval_state_to_game_state(state: dict):
    """Translate eval schema state dict → GameState for recommend().

    Eval positions are zone strings ('left_kitchen'); GameState needs x,y floats.
    Stacking (both players same side) is handled by offsetting partner 2ft left.
    """
    from app.schemas.game_state import Ball, GameState, Players, Position

    me_str = state["me_position"]
    partner_str = state["partner_position"]
    me_side = me_str.split("_")[0]  # "left" or "right"

    me_x, me_y = _pos_xy(me_str, "my")
    p_x, p_y = _pos_xy(partner_str, "my")

    # GameState validator requires my_left.x < my_right.x.
    # If stacking puts both players at the same x, offset partner 2ft to satisfy it.
    if me_side == "left":
        if p_x <= me_x:
            p_x = min(me_x + 2.0, 19.0)
        my_left = Position(x=me_x, y=me_y)
        my_right = Position(x=p_x, y=p_y)
    else:
        if p_x >= me_x:
            p_x = max(me_x - 2.0, 1.0)
        my_left = Position(x=p_x, y=p_y)
        my_right = Position(x=me_x, y=me_y)

    opp_l_x, opp_l_y = _pos_xy(state["opp_left_position"], "opp")
    opp_r_x, opp_r_y = _pos_xy(state["opp_right_position"], "opp")
    if opp_l_x >= opp_r_x:
        opp_r_x = min(opp_l_x + 2.0, 19.0)

    players = Players(
        my_left=my_left,
        my_right=my_right,
        opp_left=Position(x=opp_l_x, y=opp_l_y),
        opp_right=Position(x=opp_r_x, y=opp_r_y),
    )
    ball = Ball(
        x=state["ball_position"]["x"],
        y=state["ball_position"]["y"],
        height=state["ball_height"],
        speed=state["ball_speed"],
        spin=None,
    )
    return GameState(
        my_side=me_side,
        players=players,
        ball=ball,
        skill_level=str(state["skill_level"]),
    )


# ── scoring ────────────────────────────────────────────────────────────────

def _normalize_shot(s: str) -> str:
    """Strip non-alphanumeric chars and lowercase for fuzzy shot-name matching."""
    return re.sub(r"[^a-z0-9]", "", s.lower())


def score_scenario(scenario: dict, recs: list) -> dict:
    """Score a list of ShotRecommendation objects against a golden expert_answer.

    shot_match  — True if first rec name fuzzy-matches primary or any alternative.
    reasoning_coverage — fraction of must_mention keywords found across all why fields.
    """
    expert = scenario["expert_answer"]
    primary = expert["primary_shot"]
    alternatives = expert.get("acceptable_alternatives", [])
    must_mention = expert.get("reasoning_must_mention", [])

    shot_match = False
    predicted_shot = None
    if recs:
        first_name = recs[0].name if hasattr(recs[0], "name") else recs[0].get("name", "")
        predicted_shot = first_name
        pred_norm = _normalize_shot(first_name)
        candidates = [_normalize_shot(primary)] + [_normalize_shot(a) for a in alternatives]
        shot_match = any(pred_norm == c or pred_norm in c or c in pred_norm for c in candidates)

    all_why = " ".join(
        (r.why if hasattr(r, "why") else r.get("why", "")) for r in recs
    ).lower()
    mentions = {kw: kw.lower() in all_why for kw in must_mention}
    reasoning_coverage = sum(mentions.values()) / len(mentions) if mentions else 0.0

    return {
        "scenario_id": scenario["id"],
        "difficulty": scenario.get("difficulty", "unknown"),
        "shot_match": shot_match,
        "reasoning_coverage": round(reasoning_coverage, 3),
        "mentions": mentions,
        "predicted_shot": predicted_shot,
        "expected_shot": primary,
    }


# ── runner ─────────────────────────────────────────────────────────────────

def run(
    scenarios_path: str,
    output_path: str,
    sample: int | None = None,
    use_judge: bool = False,
) -> dict:
    from app.services.strategy import recommend

    scenarios: list[dict] = []
    with open(scenarios_path) as f:
        for line in f:
            line = line.strip()
            if line:
                scenarios.append(json.loads(line))

    if sample is not None:
        import random
        scenarios = random.sample(scenarios, min(sample, len(scenarios)))

    results: list[dict] = []
    errors: list[dict] = []

    for scenario in tqdm(scenarios, desc="Evaluating"):
        try:
            game_state = eval_state_to_game_state(scenario["state"])
            recs, warning = recommend(game_state)
            result = score_scenario(scenario, recs)
            if warning:
                result["warning"] = warning

            if use_judge:
                from llm_judge import score_response  # noqa: PLC0415
                recs_dicts = [
                    r.model_dump() if hasattr(r, "model_dump") else dict(r) for r in recs
                ]
                jr = score_response(recs_dicts, scenario["expert_answer"])
                result["judge"] = {
                    "strategic_soundness": jr.strategic_soundness,
                    "reasoning_quality": jr.reasoning_quality,
                    "specificity": jr.specificity,
                    "notes": jr.notes,
                    "passed": jr.passed,
                }
            results.append(result)
        except Exception as exc:
            errors.append({"scenario_id": scenario.get("id", "?"), "error": str(exc)})

    # ── aggregate ──────────────────────────────────────────────────────────
    passed = [r for r in results if r["shot_match"]]
    overall_pass_rate = len(passed) / len(results) if results else 0.0
    avg_reasoning = (
        sum(r["reasoning_coverage"] for r in results) / len(results) if results else 0.0
    )

    by_difficulty: dict[str, dict] = {}
    for r in results:
        d = r["difficulty"]
        bucket = by_difficulty.setdefault(d, {"total": 0, "passed": 0})
        bucket["total"] += 1
        if r["shot_match"]:
            bucket["passed"] += 1
    for d in by_difficulty:
        t = by_difficulty[d]["total"]
        by_difficulty[d]["pass_rate"] = round(by_difficulty[d]["passed"] / t, 3)

    summary: dict = {
        "total": len(results),
        "passed": len(passed),
        "errors": len(errors),
        "overall_pass_rate": round(overall_pass_rate, 3),
        "avg_reasoning_coverage": round(avg_reasoning, 3),
        "by_difficulty": by_difficulty,
    }

    if use_judge:
        judge_rows = [r["judge"] for r in results if "judge" in r]
        if judge_rows:
            summary["avg_judge_scores"] = {
                k: round(sum(j[k] for j in judge_rows) / len(judge_rows), 2)
                for k in ("strategic_soundness", "reasoning_quality", "specificity")
            }

    output = {"summary": summary, "results": results, "errors": errors}
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(json.dumps(output, indent=2))
    print(json.dumps(summary, indent=2))
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Pickle Playbook eval suite")
    parser.add_argument("scenarios_path", help="Path to golden_scenarios.jsonl")
    parser.add_argument("output_path", help="Path to write results JSON")
    parser.add_argument(
        "--sample", type=int, default=None, metavar="N",
        help="Run on N randomly sampled scenarios instead of the full set",
    )
    parser.add_argument(
        "--judge", action="store_true",
        help="Enable LLM-as-judge scoring via claude-sonnet-4-6 (~$0.50/full run)",
    )
    args = parser.parse_args()
    run(args.scenarios_path, args.output_path, sample=args.sample, use_judge=args.judge)


if __name__ == "__main__":
    main()
