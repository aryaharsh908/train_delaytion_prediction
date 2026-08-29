from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/simulation", tags=["Simulation Control"])

orchestrator = None

def set_orchestrator(orch):
    global orchestrator
    orchestrator = orch

class SpeedRequest(BaseModel):
    speed_multiplier: int

@router.post("/start")
def start_simulation():
    if orchestrator:
        orchestrator.is_running = True
        return {"status": "started", "is_running": True}
    raise HTTPException(status_code=500, detail="Orchestrator not initialized")

@router.post("/pause")
def pause_simulation():
    if orchestrator:
        orchestrator.is_running = False
        return {"status": "paused", "is_running": False}
    raise HTTPException(status_code=500, detail="Orchestrator not initialized")

@router.post("/reset")
def reset_simulation():
    if orchestrator:
        orchestrator.reset_simulation()
        return {"status": "reset", "is_running": True}
    raise HTTPException(status_code=500, detail="Orchestrator not initialized")

@router.post("/speed")
def set_speed(req: SpeedRequest):
    if orchestrator:
        orchestrator.speed_multiplier = max(1, min(100, req.speed_multiplier))
        return {"status": "speed_updated", "speed_multiplier": orchestrator.speed_multiplier}
    raise HTTPException(status_code=500, detail="Orchestrator not initialized")

@router.post("/demo_step")
def trigger_sih_demo_step():
    if orchestrator:
        res = orchestrator.trigger_sih_demo_step()
        return res
    raise HTTPException(status_code=500, detail="Orchestrator not initialized")
