from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from db.repository import ScenarioRepo
from db.supabase_client import get_client

router = APIRouter()


class ScenarioCreate(BaseModel):
    name: str
    game_state: dict


@router.get("/scenarios")
def list_scenarios():
    repo = ScenarioRepo(get_client())
    return repo.list_all()


@router.post("/scenarios", status_code=201)
def create_scenario(body: ScenarioCreate):
    repo = ScenarioRepo(get_client())
    return repo.save(body.name, body.game_state)


@router.delete("/scenarios/{scenario_id}", status_code=204)
def delete_scenario(scenario_id: str):
    repo = ScenarioRepo(get_client())
    deleted = repo.delete(scenario_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Scenario not found")
