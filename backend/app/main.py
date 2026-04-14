from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import analyze, scenarios, corrections

app = FastAPI(title="Pickle Playbook API", version="0.0.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analyze.router, prefix="/api", tags=["analyze"])
app.include_router(scenarios.router, prefix="/api", tags=["scenarios"])
app.include_router(corrections.router, prefix="/api", tags=["corrections"])


@app.get("/api/health")
def health():
    return {"status": "ok"}
