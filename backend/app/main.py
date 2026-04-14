from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.models.database import init_db
from app.routers import analyze, corrections, scenarios

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Pickle Playbook API", version="0.3.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://pickle-playbook.vercel.app",
        "https://pickle-playbook-delta.vercel.app",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analyze.router, prefix="/api", tags=["analyze"])
app.include_router(scenarios.router, prefix="/api", tags=["scenarios"])
app.include_router(corrections.router, prefix="/api", tags=["corrections"])


@app.get("/api/health")
def health():
    return {"status": "ok", "version": "0.3.0"}
