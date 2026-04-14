# Changelog

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

## [2026-04-13]

### Added
- Add Supabase migration 001: pgvector extension, scenarios/corrections/corpus_chunks tables, IVFFlat index, match_corpus similarity search function
- Scaffold full project skeleton: frontend (Vite + React + Tailwind v4), backend (FastAPI + Uvicorn), RAG pipeline placeholders
- Create component, hook, lib, constants placeholders for frontend
- Create routers, services, models, schemas placeholders for backend
- Add Pydantic GameState schema matching API contract in CLAUDE.md
- Add requirements.txt, .env.example, docker-compose.yml, root .gitignore
- Add health check endpoint and smoke test
