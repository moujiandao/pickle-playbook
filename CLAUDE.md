# Pickle Playbook

## What This Is
Interactive pickleball strategy visualizer. Users drag 4 players and a ball
on a 3D-perspective court, set ball parameters (height, speed, spin), and
get AI-powered shot recommendations with 3-shot rally sequences. Strategy
is powered by RAG over curated pickleball content with human-in-the-loop
corrections.

## Architecture
pickle-playbook/
├── CLAUDE.md
├── reference/
│   └── prototype.jsx          # Working artifact from Claude.ai (DO NOT EDIT)
├── frontend/                  # React + Vite + Tailwind
│   ├── src/
│   │   ├── App.jsx
│   │   ├── components/
│   │   │   ├── Court3D.jsx          # SVG court renderer + perspective projection
│   │   │   ├── StickFigure.jsx      # Player stick figure component
│   │   │   ├── BallIcon.jsx         # Ball component
│   │   │   ├── ControlPanel.jsx     # Side selector, ball params, analyze button
│   │   │   ├── ResultsPanel.jsx     # 3-shot rally display
│   │   │   └── ScenarioList.jsx     # Save/load scenarios
│   │   ├── hooks/
│   │   │   ├── useDrag.js           # Pointer/touch drag with court projection
│   │   │   ├── useAnalyze.js        # API call to /api/analyze
│   │   │   └── useScenarios.js      # Scenario CRUD
│   │   ├── lib/
│   │   │   └── courtProjection.js   # courtToScreen/screenToCourt math
│   │   └── constants.js             # Court dimensions, colors
│   ├── package.json
│   ├── vite.config.js
│   └── tailwind.config.js
├── backend/                   # FastAPI + Python
│   ├── app/
│   │   ├── main.py                  # FastAPI app, CORS, mount routers
│   │   ├── routers/
│   │   │   ├── analyze.py           # POST /api/analyze
│   │   │   ├── scenarios.py         # CRUD /api/scenarios
│   │   │   └── corrections.py       # POST /api/correct
│   │   ├── services/
│   │   │   ├── strategy.py          # Orchestrates RAG → Claude → response
│   │   │   └── position_describer.py # Converts coordinates to natural language
│   │   ├── models/
│   │   │   └── database.py          # SQLAlchemy models
│   │   └── schemas/
│   │       └── game_state.py        # Pydantic models
│   ├── tests/
│   ├── requirements.txt
│   └── .env.example
├── rag/                       # RAG pipeline
│   ├── ingest.py                    # Chunk + embed corpus files
│   ├── embeddings.py                # OpenAI embedding wrapper
│   ├── retrieval.py                 # Query ChromaDB for relevant chunks
│   ├── prompt_builder.py            # Build Claude API prompt from game state
│   ├── corpus/                      # Raw strategy text files
│   │   ├── kitchen_play.md
│   │   ├── third_shot_drops.md
│   │   └── positioning.md
│   ├── chroma_db/                   # Local ChromaDB storage (gitignored)
│   └── tests/
└── docker-compose.yml         # Optional: backend + db for deployment

## Key Design Decisions

### Coordinate System
- Court positions stored in FEET (0-20 x, 0-44 y), not pixels
- y=0 is the far baseline (opponents), y=44 is near baseline (ours)
- NET_Y = 22 (center), KITCHEN = 7ft from net on each side
- Frontend projection: courtToScreen()/screenToCourt() handles 3D perspective
- Backend receives feet coordinates — translates to tactical descriptions
  ("3ft behind kitchen line, left sideline") for the Claude prompt

### Ball Rules
- Ball can only be dragged on YOUR side (y >= 22)
- Spin selector ONLY appears when ball is in kitchen zone (22 <= y <= 29)
- Height: low/mid/high — Speed: slow/fast — Spin: topspin/flat/slice

### Player Constraints
- Left player.x must always be < right player.x (minimum 1ft gap)
- Opponents locked to y <= 22, your team locked to y >= 22
- "ME" badge follows the mySide selection (left or right)

### 3-Shot Rally Format
Every recommendation includes exactly 3 shots:
1. YOUR shot (what to hit)
2. OPPONENT likely response (based on their actual positions)
3. YOUR follow-up (or partner's follow-up)

Each step has: shot number, who acts, action description, result description.

### Game State JSON (API Contract)
```json
{
  "my_side": "left",
  "players": {
    "my_left":   { "x": 5.0,  "y": 37.0 },
    "my_right":  { "x": 15.0, "y": 37.0 },
    "opp_left":  { "x": 5.0,  "y": 7.0 },
    "opp_right": { "x": 15.0, "y": 7.0 }
  },
  "ball": {
    "x": 10.0, "y": 33.0,
    "height": "mid",
    "speed": "slow",
    "spin": null
  }
}
```

### Response JSON (API Contract)
```json
[
  {
    "name": "Cross-Court Dink",
    "why": "Ball is low in kitchen. Both opponents at kitchen.",
    "rally": [
      { "shot": 1, "who": "You", "action": "Soft cross-court dink...", "result": "Lands in opponent kitchen..." },
      { "shot": 2, "who": "Opponent", "action": "OPP L dinks back...", "result": "Returns to your side..." },
      { "shot": 3, "who": "You", "action": "Attack middle gap...", "result": "Splits defenders..." }
    ]
  }
]
```

## Tech Stack
- Frontend: React 18 + Vite + Tailwind CSS
- Backend: FastAPI + Uvicorn + Pydantic
- RAG: ChromaDB (local, swap to pgvector for prod) + OpenAI embeddings
- AI: Claude Sonnet via Anthropic API
- DB: SQLite (local, swap to Supabase PostgreSQL for prod)
- Deploy: Vercel (frontend) + Railway/EC2 (backend)

## Conventions
- Snake_case for Python, camelCase for JS/React
- All API routes prefixed with /api/
- Pydantic models in schemas/, SQLAlchemy in models/
- Tests mirror the source structure (backend/tests/test_analyze.py)
- .env for secrets, .env.example committed with placeholders

## Do Not
- Do NOT modify reference/prototype.jsx — it's the design reference
- Do NOT hardcode API URLs — use env vars (VITE_API_URL for frontend)
- Do NOT put Claude API key in frontend code — backend only
- Do NOT merge coordinate systems — always store in feet, project in the component
- Do NOT skip the natural language translation step — Claude needs
  "3ft behind kitchen, left side" not "x:5, y:37"