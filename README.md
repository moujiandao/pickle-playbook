# Pickle Playbook

Pickle Playbook is an interactive pickleball strategy tool. A user places four players and the ball on a perspective court, describes the incoming ball, and receives a shot recommendation grounded in curated strategy material.

[Open the hosted frontend](https://pickle-playbook-delta.vercel.app)

The project is an active prototype. The current recommendation contract returns one shot with its tactical reasoning. Longer rally sequences are intentionally deferred until single-shot recommendations are reliable.

## How it works

1. The browser stores player and ball positions in court coordinates measured in feet.
2. The API converts those coordinates and ball attributes into a tactical description.
3. The retrieval layer selects relevant scenario cards from a local Chroma collection.
4. Claude receives the game state and retrieved context and returns a structured recommendation.
5. Users can save scenarios and submit corrections for later analysis.
6. An evaluation harness checks the recommendation against explicitly documented failure modes.

```text
React court editor
      |
      v
FastAPI game-state contract
      |
      +-- position and situation description
      +-- Chroma retrieval over strategy cards
      +-- Claude recommendation
      +-- recommendation logging and corrections
      |
      v
Structured shot recommendation
      |
      +-- deterministic checks
      +-- focused LLM judge
      +-- Langfuse and OpenTelemetry traces
```

## Product behavior

- Drag four players and a ball within legal court boundaries.
- Choose the controlled player and set skill level, ball height, speed, and spin.
- Generate a structured shot recommendation with an immediate expected result.
- Save and reload game scenarios.
- Submit a human correction when the recommendation is tactically wrong.
- Keep court geometry independent of screen pixels through reversible court-to-screen projection.

## Evaluation

The evaluation suite is organized around concrete failures rather than a generic quality score:

- **M1:** wrong shot family, checked deterministically.
- **M4:** incorrect reading of ball height or speed, graded by a focused LLM judge.
- **M5:** wrong offensive, defensive, or neutral posture, checked deterministically.

The current golden set is intentionally small and does not yet cover every failure mode. See [`evals/failure_modes.md`](evals/failure_modes.md) for the coverage gaps and [`evals/README.md`](evals/README.md) for the runner.

With the API running locally:

```bash
python evals/run_eval.py \
  evals/golden_scenarios.jsonl \
  evals/results/run.json
```

Generated evaluation results are ignored by default. A baseline should be committed only after its scenarios and scoring changes have been reviewed.

## Local development

Requirements:

- Python 3.11+
- Node.js 20+
- Anthropic and OpenAI API keys

```bash
# Backend
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
cp backend/.env.example backend/.env
cd backend && uvicorn app.main:app --reload
```

In another terminal:

```bash
cd frontend
npm ci
npm run dev
```

The frontend runs at [http://localhost:5173](http://localhost:5173), and the API health endpoint is [http://localhost:8000/api/health](http://localhost:8000/api/health).

The backend uses SQLite by default. Chroma stores the local retrieval index, and both directories are excluded from Git.

## Verification

```bash
pytest backend/tests rag/tests evals/tests
cd frontend && npm run lint
cd frontend && npm run build
```

## Technology

- React, Vite, Tailwind CSS, and SVG
- FastAPI, Pydantic, and SQLAlchemy
- ChromaDB and OpenAI embeddings
- Anthropic API
- Langfuse and OpenTelemetry
- SQLite for local persistence

## Current limitations

- The golden evaluation set is too small to support broad quality claims.
- M5 does not yet have a golden scenario.
- Recommendation confidence is not yet informed by enough real outcome data.
- The current response intentionally stops after one recommended shot.
- Ten existing backend contract assertions still encode the earlier three-shot response and need to be updated to the current one-shot contract.
- The frontend builds successfully, but ESLint currently reports three cleanup items in `App.jsx` and `StickFigure.jsx`.
- The hosted frontend depends on separately configured backend services.
- The strategy corpus and evaluation set require continued human review.
