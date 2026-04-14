from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from db.repository import CorrectionRepo
from db.supabase_client import get_client

router = APIRouter()

VALID_FEEDBACK_TYPES = {"thumbs_up", "thumbs_down", "rewrite"}


class CorrectionCreate(BaseModel):
    game_state: dict
    original_recommendation: dict
    corrected_recommendation: dict | None = None
    feedback_type: str


@router.post("/correct", status_code=201)
def submit_correction(body: CorrectionCreate):
    if body.feedback_type not in VALID_FEEDBACK_TYPES:
        raise HTTPException(
            status_code=422,
            detail=f"feedback_type must be one of: {', '.join(sorted(VALID_FEEDBACK_TYPES))}",
        )
    repo = CorrectionRepo(get_client())
    return repo.save(
        game_state=body.game_state,
        original=body.original_recommendation,
        corrected=body.corrected_recommendation,
        feedback_type=body.feedback_type,
    )
