"""
check_regression.py — CI gate script for eval pass-rate regression.

Usage (CI):
    python evals/check_regression.py \
        --baseline evals/results/baseline.json \
        --current  evals/results/current.json \
        --threshold 0.05

Exits 0 if the current pass rate has not dropped more than `threshold`
below the baseline. Exits 1 (and prints a diff) if regression is detected.

Baseline contract:
    The baseline.json must exist before CI runs this script.
    Generate it once on a known-good commit:
        python evals/run_eval.py evals/golden_scenarios.jsonl evals/results/baseline.json

TODO: implement argument parsing (argparse)
TODO: implement load_results(path) -> dict
TODO: implement check_regression(baseline, current, threshold) -> bool
TODO: implement diff report (show which scenarios flipped passed→failed)
TODO: set sys.exit code appropriately
"""

import sys


def main():
    # TODO: parse --baseline, --current, --threshold
    # TODO: load both result files
    # TODO: call check_regression(), print report, exit with correct code
    raise NotImplementedError


def load_results(path: str) -> dict:
    """Load a run_eval.py output JSON file."""
    # TODO: read and parse JSON
    raise NotImplementedError


def check_regression(baseline: dict, current: dict, threshold: float) -> tuple[bool, list[str]]:
    """
    Returns (passed, flipped_ids).
    passed=True means no regression beyond threshold.
    flipped_ids is the list of scenario IDs that went from pass to fail.
    """
    # TODO: compare summary.pass_rate values
    # TODO: collect scenario IDs where baseline passed and current failed
    raise NotImplementedError


if __name__ == "__main__":
    main()
