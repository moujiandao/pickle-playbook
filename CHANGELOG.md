# Changelog

## [2026-04-14] (more green space + court recolor + player labels + thicker border)

### Changed
- Triple the out-of-bounds strip below the near baseline from 40px to 120px; `SVG_H` raised from 537 to 617 with `NEAR_Y = SVG_H - 120` so the court geometry above the near baseline is untouched
- Widen the left/right out-of-bounds margins from 60px to 100px on each side by raising `SVG_W` from 800 to 880 and recentering `NEAR_LEFT_X`/`FAR_LEFT_X` (near baseline stays 680px wide, far baseline stays 340px wide — trapezoid proportions unchanged)
- Recolor the entire playing surface to `#1E93D6` (was `#2563EB`); white lines retained
- Rename near-side player labels from `YOU L` / `YOU R` to `Leftside Player` / `Rightside Player`
- Thicken the court perimeter (baselines + sidelines) from `strokeWidth=2.6` to `5.2` while keeping interior kitchen + center service lines at 2.6; split `COURT_LINES` into `COURT_PERIMETER` + `COURT_INTERIOR` in `Court3D.jsx`

## [2026-04-14] (near half 10% taller than far half)

### Changed
- Lower `DEPTH_EXP` from 1.27 to 0.93 so the near half (net → near baseline) is 10% taller on screen than the far half (net → far baseline), reversing the previous opponent-favored perspective; derived from `near/far = 0.5^E / (1 - 0.5^E) = 1.10`

## [2026-04-14] (top margin + deeper opponent service boxes)

### Changed
- Extend the out-of-bounds strip above the far baseline from 60px to 120px so far-side player heads no longer clip against the top edge of the SVG
- Raise `DEPTH_EXP` from 1.12 to 1.27 so the far half (opponent service boxes, net → far baseline) is 20% taller on screen while the near half stays at its previous 156px; `SVG_H` raised from 440 to 537 to accommodate the combined top-margin + far-half changes

## [2026-04-14] (court geometry + net bottom band)

### Changed
- Narrow the far baseline to exactly half the near baseline (`FAR_LEFT_X=230`, `FAR_RIGHT_X=570`); all projected geometry, drag constraints, and player/ball positioning update via `constants.js` without touching `courtProjection.js`
- Recolor the net bottom band from black to white in `Court3D.jsx`

## [2026-04-14] (rally flow layout)

### Changed
- Move `ResultsPanel` from the right-side column to directly below `Court3D` in the left column so the shot sequence reads left-to-right under the court
- Rewrite `ResultsPanel` success state to show only the top recommendation as a single horizontal strip: `#1` badge + shot name + `why` header, followed by 3 bubbles (action + result) connected by right-pointing arrows
- Bubble strip uses `overflow-x: auto` with `flex-wrap: nowrap` so it stays on one line and scrolls horizontally only when the container is narrower than three bubbles plus arrows
- Tighten rally text scale (action 11.5px, result 10.5px) to fit the default case inside the ~800px court column without triggering scroll
- Drop recommendations 2+ from the UI (backend still returns them; they're intentionally ignored for now)

## [2026-04-14] (fix: analyze button silent failure in production)

### Fixed
- Correct `frontend/.env.production` to point at the real Render URL `https://pickle-playbook.onrender.com` (was a never-provisioned `pickle-api.brianmar.com` custom domain)
- Surface API failures in `ResultsPanel`: `App.jsx` now passes the `useAnalyze` `error` state through, and `ResultsPanel` renders a red banner when `error` is set so network/API failures are visible instead of making the analyze button look dead
- Update `docs/render-temporary-deployment.md` to reflect the actual Render service hostname (`pickle-playbook.onrender.com`, not `pickle-playbook-api.onrender.com`)

## [2026-04-14] (ball height visualization)

### Added
- Elevate the ball visually based on `ball.height`: `low` sits on the court, `mid` raises it by `NET_PIXEL_HEIGHT` (≈ one net-tape height), `high` raises it by 2x, all scaled by depth
- Dashed vertical tether line from ground contact point to the elevated ball, so the lift is legible at any depth
- `NET_PIXEL_HEIGHT = 40` constant in `constants.js`

### Changed
- `BallIcon` now takes an `elevation` prop; ground shadow stays pinned to `cy` while the ball body, holes, and selection ring render at `cy - elevation`

## [2026-04-14] (reference-image court)

### Added
- Ship `frontend/public/court.jpg` (copy of `reference/reference-court.jpg`) as the court backdrop

### Changed
- Replace the hand-drawn SVG court/net in `Court3D.jsx` with a single `<image href="/court.jpg">` element; viewBox resized to 1000x556 to match the image
- Rewrite `courtProjection.js` with a piecewise mapping anchored to pixel-measured net position (`NET_SCREEN_Y=245`): far half is a rectangle, near half is a trapezoid, so player/ball movement restrictions at `NET_Y=22` line up with the painted net in the image
- Corner constants in `constants.js` now hold pixel coordinates lifted from the reference image (far `[253, 750] @ y=175`, near `[141, 858] @ y=430`); remove unused `DEPTH_EXP`
- `useDrag.js` imports `SVG_W`/`SVG_H` from constants instead of hardcoding 800x440

## [2026-04-14] (court rendering per skill spec)

### Changed
- Rewrite `Court3D`, `StickFigure`, `BallIcon`, `constants.js`, and `courtProjection.js` to comply with `.claude/skills/pickleball-court-rendering.md`
- Trapezoid geometry: near baseline = 85% of container, far baseline = 59% of near, court height = 77% of container
- Depth scaling reformulated to `0.55 + depth_ratio * 0.45` (was a custom 0.65-1.15 range)
- `PLAYER_HEIGHT = 75` and `BALL_RADIUS = 12` so far-side players stay above the 40px minimum and balls above the 8px minimum
- Player stick figure rebuilt with spec proportions (head 18%, body 40%, legs 35%, arm span 40%) and label rendered below the figure
- Team colors updated to skill palette: `#F5A623` (you), `#E74C3C` (opponents); ball `#C8E636` with dark stroke; court `#2563EB`, out-of-bounds `#991B1B`, net `#2C3E50` with white mesh
- Net height capped at 12 units with black posts and a white top-tape

## [2026-04-14] (court visual refresh)

### Changed
- Restyle `Court3D.jsx` to match a real pickleball court: solid royal blue playing surface, red out-of-bounds border, thicker white lines, black net posts, and a darker mesh net
- Collapse `kitchenFar`/`kitchenNear` palette entries in `constants.js` to a single blue and add an `outOfBounds` brick-red color
- Remove NVZ watermark text from the kitchen

## [2026-04-14] (merge sprint-2.5 into main)

### Changed
- Merge `sprint-2.5-integration-tests` into `main`; resolved 14 conflicts by taking the sprint branch's real product code (routers, services, frontend components, rag modules) and keeping the deploy-infra branch's CORS allowlist and API version in `backend/app/main.py`
- Persistence layer temporarily on SQLAlchemy+SQLite (sprint branch) rather than Supabase (deploy-infra branch); `backend/db/` Supabase wrappers remain on disk as dead code until a later migration task
- Re-add `sqlalchemy>=2.0.36` to `backend/requirements.txt` (auto-merge had dropped it in favour of the Supabase-only deploy-infra list)

## [2026-04-14] (Render deploy fixes)

### Changed
- Bind uvicorn to `${PORT:-8001}` in Dockerfile so Render's injected `$PORT` works (local dev still falls back to 8001)
- Add `https://pickle-playbook-delta.vercel.app` to CORS allowlist in `backend/app/main.py`

### Added
- Add `docs/render-temporary-deployment.md` documenting temporary Render deployment and clean migration path back to EC2

## [2026-04-13] (Tasks 3.2 & 3.3)

### Added
- Add Supabase client singleton (backend/db/supabase_client.py) with python-dotenv loading
- Add repository layer (backend/db/repository.py): ScenarioRepo, CorrectionRepo, CorpusRepo wrapping Supabase tables and match_corpus RPC
- Implement rag/embeddings.py with OpenAI text-embedding-3-small (1536 dims)
- Implement rag/retrieval.py using CorpusRepo.search_similar() via pgvector
- Implement rag/prompt_builder.py: tactical court-position language + strategy context prompt for Claude
- Implement backend/app/services/position_describer.py: x/y coordinate to English converter
- Implement backend/app/services/strategy.py: RAG -> Claude claude-opus-4-6 -> JSON recommendations
- Wire analyze router to strategy.recommend()
- Implement scenarios router with ScenarioRepo CRUD (list, create, delete)
- Implement corrections router with CorrectionRepo and feedback_type validation
- Add corpus migration script at backend/scripts/migrate_corpus.py
- Add Dockerfile with PYTHONPATH=/app:/app/backend for rag + backend co-location
- Add docker-compose.pickle.yml for EC2 deployment
- Add scripts/deploy.sh (executable) for SSH-based EC2 deploy
- Add caddy/pickle.caddyfile Caddy snippet for HTTPS reverse proxy

### Changed
- Replace chromadb and sqlalchemy dependencies with supabase>=2.9.0 in requirements.txt
- Update CORS origins to include https://pickle-playbook.vercel.app
- Bump API version to 0.3.0

## [2026-04-13] (integration tests)

### Added
- Add `backend/tests/integration/` suite that spawns a real uvicorn subprocess against an isolated SQLite file and exercises every public endpoint over real HTTP (47 tests covering health, analyze contract + zone coverage + validation + CORS, scenarios CRUD + round-trip, and corrections)
- Session-scoped `live_server` fixture in `tests/integration/conftest.py` waits on `/api/health`, forces the heuristic strategy path (clears `ANTHROPIC_API_KEY`), and per-test `_isolate_scenarios` fixture wipes the scenarios table between tests

### Notes (resume context for next session)
- Branch layout: `sprint-2.5-integration-tests` (4810c66) = `feature/scaffold-skeleton` (696377c, integration wiring) fast-forward-merged + the integration test commit on top. `main` is unchanged. Do work on `sprint-2.5-integration-tests`.
- Test counts as of this commit: backend 70/70 passing (47 integration + 23 unit), rag 44/44 passing.
- `tiktoken` is installed in `backend/.venv` but is **not** listed in `backend/requirements.txt` — it lives in `rag/requirements.txt`. If you rebuild the backend venv from requirements alone the rag unit tests will fail with `ModuleNotFoundError: tiktoken`. Either install both requirements files or add `tiktoken` to `backend/requirements.txt`.
- `rag/chroma_db/` is **not built yet**. The analyze endpoint runs through the heuristic fallback in `services/strategy.py` until you run `python rag/ingest.py` with `OPENAI_API_KEY` set, then start the backend with `ANTHROPIC_API_KEY` set. Integration tests intentionally clear `ANTHROPIC_API_KEY` so they keep exercising the heuristic path regardless.
- Run integration tests from `backend/` with `.venv` active: `python -m pytest tests/integration -v`. They take ~6s because each session boots a real uvicorn subprocess on a free port against a tmp SQLite file (`PICKLE_DATABASE_URL`).

## [2026-04-13] (integration wiring)

### Changed
- Wire frontend `useAnalyze` hook to call POST `/api/analyze` directly; remove inline mock generator
- Replace heuristic-only `services/strategy.py` with a RAG + Claude orchestrator that imports `rag/retrieval.py` and `rag/prompt_builder.py` via `sys.path`; falls back to the deterministic heuristic when `ANTHROPIC_API_KEY`, the rag modules, or the Claude call are unavailable
- Refactor `useScenarios` hook to call backend `/api/scenarios` instead of `localStorage`
- Reshape backend `Scenario` schema to match the frontend payload (`{name, state: {players, ball, mySide, result}, timestamp}`); rename `ScenarioRow.game_state_json` -> `state_json`
- Broaden CORS allowlist to include `http://127.0.0.1:5173`
- Add `frontend/.env.example` documenting `VITE_API_URL`

## [2026-04-13] (RAG pipeline)

### Added
- Implement token-aware chunker (300-500 tokens, 50-token overlap, tiktoken cl100k_base) with .md/.txt/.srt support
- Implement OpenAI text-embedding-3-small wrapper with batching
- Implement corpus ingestion pipeline with deterministic chunk IDs, upserts to local ChromaDB
- Implement position_describer: GameState coordinates -> natural language (zone labels, lateral positions, tactical context)
- Implement retrieval service: GameState -> NL query -> top-5 ChromaDB chunks with source attribution
- Implement prompt builder: assembles system prompt + situation description + retrieved context + 3-shot output spec
- Add 3 seed corpus files with real pickleball strategy content (kitchen play, third shot drops, positioning/stacking)
- Add 43 tests covering chunking, position description, and prompt assembly
- Add requirements.txt and .env.example for RAG pipeline

## [2026-04-13] (scaffold)

### Added
- Add Supabase migration 001: pgvector extension, scenarios/corrections/corpus_chunks tables, IVFFlat index, match_corpus similarity search function
- Scaffold full project skeleton: frontend (Vite + React + Tailwind v4), backend (FastAPI + Uvicorn), RAG pipeline placeholders
- Create component, hook, lib, constants placeholders for frontend
- Create routers, services, models, schemas placeholders for backend
- Add Pydantic GameState schema matching API contract in CLAUDE.md
- Add requirements.txt, .env.example, docker-compose.yml, root .gitignore
- Add health check endpoint and smoke test
