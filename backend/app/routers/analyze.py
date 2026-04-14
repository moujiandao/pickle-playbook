from fastapi import APIRouter

from app.schemas.game_state import GameState, ShotRecommendation
from app.services.strategy import recommend

router = APIRouter()


@router.post("/analyze", response_model=list[ShotRecommendation])
def analyze(state: GameState) -> list[ShotRecommendation]:
    """Return 2-3 shot recommendations with 3-step rallies for the given game state."""
    return recommend(state)
