"""
run_eval.py — Batch eval runner for Pickle Playbook strategy recommendations.

Usage:
    python evals/run_eval.py <scenarios.jsonl> <output.json> [--api-url URL]

What it does:
    1. Reads each golden scenario from the JSONL file.
    2. Posts the game_state to /api/analyze (local or remote).
    3. Passes the response + expected fields to llm_judge.py for scoring.
    4. Writes a results JSON with per-scenario verdicts and aggregate stats.

Output schema:
    {
      "summary": {
        "total": int,
        "passed": int,
        "pass_rate": float,          // 0.0 – 1.0
        "by_difficulty": {
          "beginner": { "total": int, "passed": int },
          "intermediate": { ... },
          "advanced": { ... }
        }
      },
      "scenarios": [
        {
          "id": str,
          "difficulty": str,
          "passed": bool,
          "score": float,            // 0.0 – 1.0 from LLM judge
          "reasoning_coverage": bool,
          "judge_notes": str
        },
        ...
      ]
    }

TODO: implement argument parsing (argparse)
TODO: implement JSONL loader
TODO: implement HTTP client (httpx or requests) to hit /api/analyze
TODO: implement per-scenario result collection loop
TODO: implement aggregate stats calculation
TODO: write results to output JSON file
"""


def main():
    # TODO: parse CLI arguments: scenarios_path, output_path, --api-url
    # TODO: load golden scenarios from JSONL
    # TODO: for each scenario, call analyze_scenario()
    # TODO: collect results, compute summary, write output
    raise NotImplementedError


def analyze_scenario(game_state: dict, api_url: str) -> dict:
    """POST game_state to /api/analyze and return the parsed response."""
    # TODO: implement HTTP POST with timeout handling
    raise NotImplementedError


if __name__ == "__main__":
    main()
