"""Flatten an eval results JSON into a wide CSV for spreadsheet review.

Usage:
    python evals/flatten_results.py results/baseline.json
    python evals/flatten_results.py results/baseline.json -o my_review.csv

Joins each result row against golden_scenarios.jsonl so the sheet has the
scenario context (positions, ball state, source) next to the model's
predicted vs expected shot. A blank `notes` column is appended for review.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_SCENARIOS_PATH = _HERE / "golden_scenarios.jsonl"


def _load_scenarios() -> dict[str, dict]:
    rows = {}
    with _SCENARIOS_PATH.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            rows[row["id"]] = row
    return rows


def _format_mentions(mentions: dict) -> tuple[str, str]:
    hit = [k for k, v in mentions.items() if v]
    miss = [k for k, v in mentions.items() if not v]
    return ", ".join(hit), ", ".join(miss)


def flatten(results_path: Path, out_path: Path) -> int:
    data = json.loads(results_path.read_text())
    scenarios = _load_scenarios()

    columns = [
        "id",
        "difficulty",
        "pass",                       # ✓ / ✗ for quick visual scan
        "predicted_shot",
        "expected_shot",
        "acceptable_alternatives",
        "reasoning_coverage",
        "mentions_hit",
        "mentions_miss",
        "skill_level",
        "zone",
        "ball_height",
        "ball_speed",
        "ball_x",
        "ball_y",
        "me_position",
        "partner_position",
        "opp_left_position",
        "opp_right_position",
        "expected_sequence",
        "source",
        "warning",
        "notes",                      # left blank for review
    ]

    with out_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        for r in data["results"]:
            sid = r["scenario_id"]
            scen = scenarios.get(sid, {})
            state = scen.get("state", {})
            expert = scen.get("expert_answer", {})
            ball = state.get("ball_position", {}) or {}
            hit, miss = _format_mentions(r.get("mentions", {}))

            writer.writerow({
                "id": sid,
                "difficulty": r.get("difficulty", ""),
                "pass": "✓" if r.get("shot_match") else "✗",
                "predicted_shot": r.get("predicted_shot", ""),
                "expected_shot": r.get("expected_shot", ""),
                "acceptable_alternatives": ", ".join(expert.get("acceptable_alternatives", [])),
                "reasoning_coverage": r.get("reasoning_coverage", ""),
                "mentions_hit": hit,
                "mentions_miss": miss,
                "skill_level": state.get("skill_level", ""),
                "zone": state.get("zone", ""),
                "ball_height": state.get("ball_height", ""),
                "ball_speed": state.get("ball_speed", ""),
                "ball_x": ball.get("x", ""),
                "ball_y": ball.get("y", ""),
                "me_position": state.get("me_position", ""),
                "partner_position": state.get("partner_position", ""),
                "opp_left_position": state.get("opp_left_position", ""),
                "opp_right_position": state.get("opp_right_position", ""),
                "expected_sequence": " | ".join(expert.get("expected_sequence", [])),
                "source": scen.get("source", ""),
                "warning": r.get("warning", ""),
                "notes": "",
            })

    return len(data["results"])


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("results", type=Path, help="path to results JSON (e.g. results/baseline.json)")
    ap.add_argument("-o", "--out", type=Path, default=None, help="output CSV path (defaults to <results>.csv)")
    args = ap.parse_args()

    results_path = args.results if args.results.is_absolute() else (_HERE / args.results)
    out_path = args.out or results_path.with_suffix(".csv")

    n = flatten(results_path, out_path)
    print(f"wrote {n} rows → {out_path}")


if __name__ == "__main__":
    main()
