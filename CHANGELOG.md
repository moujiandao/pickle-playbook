# Changelog

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
- Scaffold full project skeleton: frontend (Vite + React + Tailwind v4), backend (FastAPI + Uvicorn), RAG pipeline placeholders
- Create component, hook, lib, constants placeholders for frontend
- Create routers, services, models, schemas placeholders for backend
- Add Pydantic GameState schema matching API contract in CLAUDE.md
- Add requirements.txt, .env.example, docker-compose.yml, root .gitignore
- Add health check endpoint and smoke test
