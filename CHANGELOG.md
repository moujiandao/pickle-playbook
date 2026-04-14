# Changelog

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
