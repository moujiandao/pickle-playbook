import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.models.database import ScenarioRow, get_db
from app.schemas.game_state import Scenario, ScenarioCreate

router = APIRouter()


@router.get("/scenarios", response_model=list[Scenario])
def list_scenarios(db: Session = Depends(get_db)) -> list[Scenario]:
    rows = db.query(ScenarioRow).order_by(ScenarioRow.created_at.desc()).all()
    return [_row_to_schema(r) for r in rows]


@router.post("/scenarios", response_model=Scenario, status_code=201)
def create_scenario(body: ScenarioCreate, db: Session = Depends(get_db)) -> Scenario:
    row = ScenarioRow(
        name=body.name,
        game_state_json=body.game_state.model_dump_json(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _row_to_schema(row)


@router.delete("/scenarios/{scenario_id}", status_code=204)
def delete_scenario(scenario_id: int, db: Session = Depends(get_db)) -> None:
    row = db.get(ScenarioRow, scenario_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Scenario not found")
    db.delete(row)
    db.commit()


def _row_to_schema(row: ScenarioRow) -> Scenario:
    from app.schemas.game_state import GameState
    return Scenario(
        id=row.id,
        name=row.name,
        game_state=GameState.model_validate(json.loads(row.game_state_json)),
        created_at=row.created_at,
    )
