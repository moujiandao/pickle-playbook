from typing import Literal, Optional

from pydantic import BaseModel, Field


class Position(BaseModel):
    x: float = Field(..., ge=0, le=20)
    y: float = Field(..., ge=0, le=44)


class Players(BaseModel):
    my_left: Position
    my_right: Position
    opp_left: Position
    opp_right: Position


class Ball(BaseModel):
    x: float = Field(..., ge=0, le=20)
    y: float = Field(..., ge=0, le=44)
    height: Literal["low", "mid", "high"]
    speed: Literal["slow", "fast"]
    spin: Optional[Literal["topspin", "flat", "slice"]] = None


class GameState(BaseModel):
    my_side: Literal["left", "right"]
    players: Players
    ball: Ball


class RallyShot(BaseModel):
    shot: int
    who: str
    action: str
    result: str


class Recommendation(BaseModel):
    name: str
    why: str
    rally: list[RallyShot]


class CorrectionRequest(BaseModel):
    game_state: GameState
    original_recommendation: Recommendation
    corrected_recommendation: Optional[str] = None
    feedback_type: Literal["thumbs_up", "thumbs_down", "rewrite"]
