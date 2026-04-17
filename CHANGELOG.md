# Changelog

## [2026-04-13]

### Added
- Add CorrectionControls component: thumbs up/down, inline rewrite editor, POST to /api/correct, inline toast, locks after submission
- Implement ResultsPanel: recommendation cards with 3-shot rally sequences, loading/empty states, CorrectionControls per card
- Add CorrectionRequest Pydantic schema (game_state + original_recommendation + corrected_recommendation + feedback_type)
- Implement POST /api/correct with full request validation; logs corrections until CorrectionRepo/Supabase lands
- Wire App.jsx with recommendations/gameState/analyzing state passed down to ResultsPanel

### Added
- Scaffold full project skeleton: frontend (Vite + React + Tailwind v4), backend (FastAPI + Uvicorn), RAG pipeline placeholders
- Create component, hook, lib, constants placeholders for frontend
- Create routers, services, models, schemas placeholders for backend
- Add Pydantic GameState schema matching API contract in CLAUDE.md
- Add requirements.txt, .env.example, docker-compose.yml, root .gitignore
- Add health check endpoint and smoke test
