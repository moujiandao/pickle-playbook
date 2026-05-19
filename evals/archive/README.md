# evals/archive — v1 artifacts (frozen)

This directory holds the eval state from before the 2026-04-28 rebuild.
Nothing in here is run against the current code; it's preserved as evidence
and reference.

## Contents

| Path | What it is |
|---|---|
| `golden_v1.jsonl` | The 48-scenario golden set as of Apr 22 (post-cleanup, pre-rebuild). Co-evolved with the model, hence "contaminated" — that's why we restarted. |
| `golden_v1_pre_apr22_cleanup.jsonl` | The 50-scenario set from before the Apr 22 shot-classification cleanup. Older snapshot, kept for diff if we ever need to trace a labeling decision. |
| `llm_judge_v1.py` | The blind-judge prompt before the rubric was redesigned around explicit failure modes. Useful as a starting reference for v2. |
| `results_v1/baseline.json` | Apr 21 baseline run **before** the LLM judge was wired in. Deterministic checks only. 50 scenarios, 26% pass rate. |
| `results_v1/baseline_v4_sonnet.json` | Apr 22 full baseline with Sonnet blind judge. 48 scenarios. The "real" v1 baseline. |
| `results_v1/judge_smoke*.json` | Smoke runs from judge prompt iteration sessions. |
| `results_v1/baseline.notes.json` | Triage annotations from the Streamlit UI on `baseline.json`. 3 entries. |
| `results_v1/baseline.csv` | Flattened spreadsheet view of `baseline.json`. |
| `results_v1/*.log` | Stdout/stderr captures from each run. |

## Why preserved instead of deleted

The Apr 24 audit conclusion was "preserve infrastructure, rebuild content
and rubric." Even the contaminated content has value as a reference point —
when designing v2 scenarios we'll want to be able to ask "did v1 cover this
failure mode?" and answer it without git archaeology.

## Recoverability

The pre-rebuild commit is also tagged: `git checkout evals-pre-rebuild` to
see the v1 layout in its original location.

Last updated: 2026-04-28
