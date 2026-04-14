from fastapi import APIRouter

router = APIRouter()


@router.get("/scenarios")
async def list_scenarios():
    return []


@router.post("/scenarios")
async def create_scenario():
    return {}


@router.delete("/scenarios/{scenario_id}")
async def delete_scenario(scenario_id: int):
    return {"deleted": scenario_id}
