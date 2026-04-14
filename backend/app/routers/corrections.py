from fastapi import APIRouter

router = APIRouter()


@router.post("/correct")
async def submit_correction():
    """Human-in-the-loop correction submission. Placeholder."""
    return {"status": "received"}
