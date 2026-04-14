# Changelog

## [2026-04-13] (backend implementation)

### Added
- Implement heuristic strategy engine: branches on ball zone (kitchen/transition/baseline), height, speed to return 2-3 ShotRecommendations with 3-step rallies
- Implement position_describer service: converts feet coordinates to natural-language tactical phrases
- Define full Pydantic schema set: ShotRecommendation, RallyStep, ScenarioCreate/Scenario, CorrectionCreate/Correction with field validation
- Wire POST /api/analyze to heuristic strategy engine
- Implement scenarios CRUD: POST/GET /api/scenarios and DELETE /api/scenarios/{id} backed by SQLite via SQLAlchemy
- Implement POST /api/correct for human-in-the-loop corrections
- Add SQLAlchemy models (ScenarioRow, CorrectionRow) with SQLite engine and session factory
- Add 23 pytest tests covering analyze heuristics, input validation, and scenarios CRUD lifecycle
- Replace deprecated on_event startup with lifespan context manager

## [2026-04-13]

### Added
- Scaffold full project skeleton: frontend (Vite + React + Tailwind v4), backend (FastAPI + Uvicorn), RAG pipeline placeholders
- Create component, hook, lib, constants placeholders for frontend
- Create routers, services, models, schemas placeholders for backend
- Add Pydantic GameState schema matching API contract in CLAUDE.md
- Add requirements.txt, .env.example, docker-compose.yml, root .gitignore
- Add health check endpoint and smoke test
