# Changelog

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
