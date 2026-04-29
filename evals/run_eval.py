#!/usr/bin/env python3
"""
run_eval.py — Batch eval runner for Pickle Playbook strategy recommendations.

Two independent pass signals:
  shot_match  — deterministic family-level match via shot_taxonomy.classify().
  judge_pass  — blind LLM-as-judge (no expected answer in prompt).

Overall pass = shot_match AND judge_pass (compound AND gate). The 4-quadrant
failure breakdown (right/wrong shot × good/bad reasoning) tells you which
signal is failing when they disagree.

Usage:
    python evals/run_eval.py evals/golden_scenarios.jsonl evals/results/baseline.json
    python evals/run_eval.py evals/golden_scenarios.jsonl evals/results/out.json --sample 10
    python evals/run_eval.py evals/golden_scenarios.jsonl evals/results/out.json --judge
    python evals/run_eval.py evals/golden_scenarios.jsonl evals/results/out.json --judge --judge-model opus
"""

from __future__ import annotations

import argparse
import json
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

from shot_taxonomy import (  # noqa: E402
    classify,
    expected_families,
    expected_postures,
    expected_tactical_mode,
    is_advanced_shot,
    shot_posture,
)

# Skill levels at or above this threshold are considered capable of advanced
# shots; below it, an advanced shot recommendation is M2 fail.
_ADVANCED_SHOT_THRESHOLD = 4.0

# ── court layout constants ─────────────────────────────────────────────────
_ZONE_Y_MY = {"kitchen": 29.0, "transition": 35.0, "baseline": 40.0}
_ZONE_Y_OPP = {"kitchen": 15.0, "transition": 9.0, "baseline": 4.0}
_SIDE_X = {"left": 5.0, "right": 15.0}


def _pos_xy(pos_str: str, team: str) -> tuple[float, float]:
    """'left_kitchen' + 'my'|'opp' → (x_ft, y_ft)."""
    side, zone = pos_str.split("_", 1)
    y_map = _ZONE_Y_MY if team == "my" else _ZONE_Y_OPP
    return _SIDE_X[side], y_map[zone]


def eval_state_to_game_state(state: dict):
    """Translate eval schema state dict → GameState for recommend()."""
    from app.schemas.game_state import Ball, GameState, Players, Position

    me_str = state["me_position"]
    partner_str = state["partner_position"]
    me_side = me_str.split("_")[0]

    me_x, me_y = _pos_xy(me_str, "my")
    p_x, p_y = _pos_xy(partner_str, "my")

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
        spin=state.get("ball_spin"),
    )
    return GameState(
        my_side=me_side,
        players=players,
        ball=ball,
        skill_level=str(state["skill_level"]),
    )


# ── scoring ────────────────────────────────────────────────────────────────

def score_scenario(scenario: dict, recs: list) -> dict:
    """Score recs against a golden scenario.

    Deterministic checks emitted (one per failure mode that has a det. layer):
      shot_match         — M1: predicted family ∈ expected family set.
      m2_advanced_shot_violation
                         — M2: True if scenario.skill_level < 4.0 AND the
                           predicted shot is on the advanced-shot list.
      m5_tactical_mode_match
                         — M5: predicted shot's posture ∈ expected_postures
                           (postures of all acceptable shots for this state).
      reasoning_coverage — diagnostic only (must_mention keyword hit rate).

    M3 / M4 require the LLM judge and are added by the judge stage downstream.
    """
    expert = scenario["expert_answer"]
    primary = expert["primary_shot"]
    alternatives = expert.get("acceptable_alternatives", [])
    must_mention = expert.get("reasoning_must_mention", [])
    state = scenario.get("state", {})
    skill_level = float(state.get("skill_level", 0.0)) if state.get("skill_level") is not None else 0.0

    expected_fams, unmapped_expected = expected_families(primary, alternatives)
    exp_postures = expected_postures(primary, alternatives)
    exp_mode = expected_tactical_mode(state)

    predicted_shot: str | None = None
    predicted_family: str | None = None
    predicted_posture: str | None = None
    if recs:
        first_name = recs[0].name if hasattr(recs[0], "name") else recs[0].get("name", "")
        predicted_shot = first_name
        predicted_family = classify(first_name)
        predicted_posture = shot_posture(first_name)

    shot_match = (
        predicted_family is not None
        and predicted_family in expected_fams
    )

    # M2 — advanced shot recommended to a sub-4.0 player
    m2_violation = (
        predicted_shot is not None
        and skill_level < _ADVANCED_SHOT_THRESHOLD
        and is_advanced_shot(predicted_shot)
    )

    # M5 — tactical mode (posture) must match one of the acceptable postures
    m5_mode_match = (
        predicted_posture is not None
        and predicted_posture in exp_postures
    ) if exp_postures else None

    all_why = " ".join(
        (r.why if hasattr(r, "why") else r.get("why", "")) for r in recs
    ).lower()
    mentions = {kw: kw.lower() in all_why for kw in must_mention}
    reasoning_coverage = sum(mentions.values()) / len(mentions) if mentions else 0.0

    return {
        "scenario_id": scenario["id"],
        "difficulty": scenario.get("difficulty", "unknown"),
        "failure_modes": scenario.get("failure_modes", []),
        "shot_match": shot_match,
        "predicted_shot": predicted_shot,
        "predicted_family": predicted_family,
        "predicted_posture": predicted_posture,
        "expected_primary": primary,
        "expected_families": sorted(expected_fams),
        "expected_postures": sorted(exp_postures),
        "expected_tactical_mode": exp_mode,
        "unmapped_expected_labels": unmapped_expected,
        "m2_advanced_shot_violation": m2_violation,
        "m5_tactical_mode_match": m5_mode_match,
        "reasoning_coverage": round(reasoning_coverage, 3),
        "mentions": mentions,
    }


def _quadrant(shot_match: bool, judge_pass: bool) -> str:
    """Label the 4 failure quadrants (shot × reasoning)."""
    if shot_match and judge_pass:
        return "right_shot_good_reasoning"
    if shot_match and not judge_pass:
        return "right_shot_bad_reasoning"
    if not shot_match and judge_pass:
        return "wrong_shot_good_reasoning"  # dangerous — judge rationalizing
    return "wrong_shot_bad_reasoning"


# ── runner ─────────────────────────────────────────────────────────────────

def run(
    scenarios_path: str,
    output_path: str,
    sample: int | None = None,
    use_judge: bool = False,
    judge_model: str = "sonnet",
) -> dict:
    from app.observability import flush as flush_traces
    from app.observability import init_observability, trace_scenario
    from app.services.strategy import recommend

    init_observability(service="evals")

    scenarios: list[dict] = []
    with open(scenarios_path) as f:
        for line in f:
            line = line.strip()
            if line:
                scenarios.append(json.loads(line))

    if sample is not None:
        import random
        scenarios = random.sample(scenarios, min(sample, len(scenarios)))

    # Resolve judge model alias → pinned model id.
    judge_model_id: str | None = None
    if use_judge:
        from llm_judge import MODEL_OPUS, MODEL_SONNET  # noqa: PLC0415
        alias_map = {"sonnet": MODEL_SONNET, "opus": MODEL_OPUS}
        if judge_model not in alias_map:
            raise ValueError(
                f"--judge-model must be one of {sorted(alias_map)}, got {judge_model!r}"
            )
        judge_model_id = alias_map[judge_model]

    results: list[dict] = []
    errors: list[dict] = []

    for scenario in tqdm(scenarios, desc="Evaluating"):
        scenario_id = scenario.get("id", "?")
        failure_modes = ",".join(scenario.get("failure_modes", [])) or None
        difficulty = scenario.get("difficulty")
        with trace_scenario(
            scenario_id,
            service="evals",
            difficulty=difficulty,
            failure_modes=failure_modes,
            judge_model=judge_model_id if use_judge else None,
        ):
            try:
                game_state = eval_state_to_game_state(scenario["state"])
                recs, warning = recommend(game_state)
                result = score_scenario(scenario, recs)
                if warning:
                    result["warning"] = warning

                if use_judge and judge_model_id is not None:
                    from llm_judge import score_response  # noqa: PLC0415
                    recs_dicts = [
                        r.model_dump() if hasattr(r, "model_dump") else dict(r) for r in recs
                    ]
                    skill_level = scenario["state"].get("skill_level", "unknown")
                    jr = score_response(
                        recs_dicts,
                        scenario["state"],          # blind: state only
                        skill_level,
                        model=judge_model_id,
                    )
                    result["judge"] = {
                        "strategic_soundness": jr.strategic_soundness,
                        "reasoning_quality": jr.reasoning_quality,
                        "specificity": jr.specificity,
                        "skill_level_feasible": jr.skill_level_feasible,
                        "notes": jr.notes,
                        "passed": jr.passed,
                        "model": jr.model,
                    }
                    result["quadrant"] = _quadrant(result["shot_match"], jr.passed)
                    result["overall_pass"] = bool(result["shot_match"] and jr.passed)
                results.append(result)
            except Exception as exc:
                errors.append({"scenario_id": scenario_id, "error": str(exc)})

    # ── aggregate ──────────────────────────────────────────────────────────
    n = len(results)
    shot_matched = [r for r in results if r["shot_match"]]
    shot_match_rate = len(shot_matched) / n if n else 0.0
    avg_reasoning = sum(r["reasoning_coverage"] for r in results) / n if n else 0.0

    by_difficulty: dict[str, dict] = {}
    for r in results:
        d = r["difficulty"]
        bucket = by_difficulty.setdefault(
            d, {"total": 0, "shot_matched": 0, "overall_passed": 0}
        )
        bucket["total"] += 1
        if r["shot_match"]:
            bucket["shot_matched"] += 1
        if r.get("overall_pass"):
            bucket["overall_passed"] += 1
    for d, bucket in by_difficulty.items():
        t = bucket["total"]
        bucket["shot_match_rate"] = round(bucket["shot_matched"] / t, 3) if t else 0.0
        if use_judge:
            bucket["overall_pass_rate"] = round(bucket["overall_passed"] / t, 3) if t else 0.0

    summary: dict = {
        "total": n,
        "errors": len(errors),
        "shot_match_rate": round(shot_match_rate, 3),
        "avg_reasoning_coverage": round(avg_reasoning, 3),
        "by_difficulty": by_difficulty,
    }

    if use_judge:
        judge_rows = [r["judge"] for r in results if "judge" in r]
        judge_passed = [r for r in results if r.get("judge", {}).get("passed")]
        overall_passed = [r for r in results if r.get("overall_pass")]

        failure_breakdown: dict[str, int] = {
            "right_shot_good_reasoning": 0,
            "right_shot_bad_reasoning": 0,
            "wrong_shot_good_reasoning": 0,
            "wrong_shot_bad_reasoning": 0,
        }
        for r in results:
            q = r.get("quadrant")
            if q is not None:
                failure_breakdown[q] += 1

        summary["judge_model"] = judge_model_id
        summary["judge_pass_rate"] = round(len(judge_passed) / n, 3) if n else 0.0
        summary["overall_pass_rate"] = round(len(overall_passed) / n, 3) if n else 0.0
        summary["failure_breakdown"] = failure_breakdown
        if judge_rows:
            summary["avg_judge_scores"] = {
                k: round(sum(j[k] for j in judge_rows) / len(judge_rows), 2)
                for k in ("strategic_soundness", "reasoning_quality", "specificity")
            }
            summary["skill_level_feasible_rate"] = round(
                sum(1 for j in judge_rows if j["skill_level_feasible"]) / len(judge_rows), 2
            )

    output = {"summary": summary, "results": results, "errors": errors}
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(json.dumps(output, indent=2))
    print(json.dumps(summary, indent=2))

    flush_traces()
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
        help="Enable blind LLM-as-judge scoring (~$0.50/full run on sonnet)",
    )
    parser.add_argument(
        "--judge-model", choices=("sonnet", "opus"), default="sonnet",
        help="Which Claude model to use as judge (default: sonnet)",
    )
    args = parser.parse_args()
    run(
        args.scenarios_path,
        args.output_path,
        sample=args.sample,
        use_judge=args.judge,
        judge_model=args.judge_model,
    )


if __name__ == "__main__":
    main()
