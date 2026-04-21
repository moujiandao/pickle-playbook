from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.schemas.game_state import GameState, ShotRecommendation
from app.services.strategy import recommend

router = APIRouter()


@router.post("/analyze", response_model=list[ShotRecommendation])
def analyze(state: GameState):
    """Return 2-3 shot recommendations with 3-step rallies for the given game state."""
    recs, warning = recommend(state)
    resp = JSONResponse(content=[r.model_dump() for r in recs])
    if warning:
        resp.headers["X-Pickle-Warning"] = warning
    return resp
