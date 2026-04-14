from fastapi import APIRouter

from app.schemas.game_state import GameState
from app.services import strategy

router = APIRouter()


@router.post("/analyze")
async def analyze(state: GameState):
    """Return a list of 3-shot rally recommendations."""
    return await strategy.recommend(state.model_dump())
