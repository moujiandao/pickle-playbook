# Pickle Playbook — Evals

Eval-driven quality gate for strategy recommendations. Every prompt or RAG change must pass the golden set before merging.

---

## Files

| File | Purpose |
|------|---------|
| `golden_scenarios.jsonl` | Ground-truth test cases. One JSON object per line. Each scenario has a `game_state` (exact API input), `expected` fields (shot type, must-mention keywords), and a `difficulty` label. |
| `run_eval.py` | Batch runner. Hits `/api/analyze` for every scenario, invokes the LLM judge on each response, writes a structured results JSON. |
| `llm_judge.py` | LLM-as-judge scorer. Asks Claude to evaluate a response on shot-type match, keyword coverage, and reasoning quality. Returns a `JudgeResult` with a 0–1 score. |
| `check_regression.py` | CI gate. Compares a current results file against a saved baseline. Exits non-zero if pass rate dropped more than the allowed threshold (default 5%). |
| `results/` | Local run output. `*.json` files are gitignored — only `.gitkeep` is tracked. |

---

## Running Evals Locally

**Prerequisites:** backend running on `http://localhost:8000`, virtual env active.

```bash
# 1. Start the backend
cd backend && uvicorn app.main:app --reload

# 2. Run the full golden set
python evals/run_eval.py evals/golden_scenarios.jsonl evals/results/run_$(date +%Y%m%d).json

# 3. (Optional) Check against saved baseline
python evals/check_regression.py \
  --baseline evals/results/baseline.json \
  --current  evals/results/run_$(date +%Y%m%d).json \
  --threshold 0.05
```

To save a new baseline after a deliberate improvement:

```bash
cp evals/results/run_$(date +%Y%m%d).json evals/results/baseline.json
git add evals/results/baseline.json
git commit -m "chore: update eval baseline"
```

---

## Interpreting Output

`run_eval.py` writes a JSON file with this shape:

```json
{
  "summary": {
    "total": 20,
    "passed": 17,
    "pass_rate": 0.85,
    "by_difficulty": {
      "beginner":     { "total": 8,  "passed": 8  },
      "intermediate": { "total": 8,  "passed": 7  },
      "advanced":     { "total": 4,  "passed": 2  }
    }
  },
  "scenarios": [ ... ]
}
```

- **pass_rate** — primary health metric. Target: >= 0.80 overall.
- **by_difficulty** — use this to diagnose whether regressions are concentrated in complex scenarios.
- **reasoning_coverage** — True if a scenario's `reasoning_quality` score >= 0.6. Low reasoning coverage means Claude is recommending correctly but not explaining why — a sign the RAG context is thin.
- **judge_notes** — per-scenario free-text from the LLM judge. Check these when a scenario flips from pass to fail.

`check_regression.py` exits 0 (pass) or 1 (fail) and prints a diff of flipped scenario IDs on failure.
