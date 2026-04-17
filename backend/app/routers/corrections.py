from fastapi import APIRouter

from app.schemas.game_state import CorrectionRequest

router = APIRouter()


@router.post("/correct")
async def submit_correction(body: CorrectionRequest):
    """
    Human-in-the-loop correction submission.

    Validates the full payload via CorrectionRequest.
    Storage: TODO — wire to CorrectionRepo (Supabase) once Sprint 2 repo lands.
    For now, logs and returns success so the frontend flow is unblocked.
    """
    # Structured log so corrections are at least captured in server output
    # until the repo layer exists.
    print(
        f"[correction] type={body.feedback_type!r} "
        f"rec={body.original_recommendation.name!r} "
        f"rewrite={'yes' if body.corrected_recommendation else 'no'}"
    )
    return {"status": "received"}
