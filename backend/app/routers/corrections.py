import json

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.models.database import CorrectionRow, get_db
from app.schemas.game_state import Correction, CorrectionCreate

router = APIRouter()


@router.post("/correct", response_model=Correction, status_code=201)
def submit_correction(body: CorrectionCreate, db: Session = Depends(get_db)) -> Correction:
    """Store a human-in-the-loop correction for later RAG fine-tuning."""
    row = CorrectionRow(
        game_state_json=body.game_state.model_dump_json(),
        corrected_response_json=json.dumps([r.model_dump() for r in body.corrected_response]),
        note=body.note,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _row_to_schema(row)


def _row_to_schema(row: CorrectionRow) -> Correction:
    from app.schemas.game_state import GameState, ShotRecommendation
    return Correction(
        id=row.id,
        game_state=GameState.model_validate(json.loads(row.game_state_json)),
        corrected_response=[
            ShotRecommendation.model_validate(r)
            for r in json.loads(row.corrected_response_json)
        ],
        note=row.note,
        created_at=row.created_at,
    )
