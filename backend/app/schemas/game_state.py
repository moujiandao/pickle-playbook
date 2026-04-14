from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, model_validator

Side = Literal["left", "right"]
Height = Literal["low", "mid", "high"]
Speed = Literal["slow", "fast"]
Spin = Literal["topspin", "flat", "slice"]


class Position(BaseModel):
    x: float = Field(..., ge=0, le=20)
    y: float = Field(..., ge=0, le=44)


class Players(BaseModel):
    my_left: Position
    my_right: Position
    opp_left: Position
    opp_right: Position

    @model_validator(mode="after")
    def _check_sides(self) -> "Players":
        if self.my_left.x >= self.my_right.x:
            raise ValueError("my_left.x must be < my_right.x")
        if self.opp_left.x >= self.opp_right.x:
            raise ValueError("opp_left.x must be < opp_right.x")
        if self.my_left.y < 22 or self.my_right.y < 22:
            raise ValueError("your team must be on near side (y >= 22)")
        if self.opp_left.y > 22 or self.opp_right.y > 22:
            raise ValueError("opponents must be on far side (y <= 22)")
        return self


class Ball(BaseModel):
    x: float = Field(..., ge=0, le=20)
    y: float = Field(..., ge=0, le=44)
    height: Height
    speed: Speed
    spin: Optional[Spin] = None

    @model_validator(mode="after")
    def _check_ball(self) -> "Ball":
        if self.y < 22:
            raise ValueError("ball must be on your side (y >= 22)")
        in_kitchen = 22 <= self.y <= 29
        if self.spin is not None and not in_kitchen:
            raise ValueError("spin only allowed when ball is in the kitchen zone")
        return self


class GameState(BaseModel):
    my_side: Side
    players: Players
    ball: Ball


class RallyStep(BaseModel):
    shot: int = Field(..., ge=1, le=3)
    who: str
    action: str
    result: str


class ShotRecommendation(BaseModel):
    name: str
    why: str
    rally: list[RallyStep]


class ScenarioCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    game_state: GameState


class Scenario(BaseModel):
    id: int
    name: str
    game_state: GameState
    created_at: datetime

    model_config = {"from_attributes": True}


class CorrectionCreate(BaseModel):
    game_state: GameState
    corrected_response: list[ShotRecommendation]
    note: Optional[str] = None


class Correction(BaseModel):
    id: int
    game_state: GameState
    corrected_response: list[ShotRecommendation]
    note: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
