from fastapi import APIRouter

from app.schemas.game_state import GameState

router = APIRouter()


@router.post("/analyze")
async def analyze(state: GameState):
    """Return a list of 3-shot rally recommendations. Placeholder."""
    return []
