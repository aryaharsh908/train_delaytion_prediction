from fastapi import APIRouter, HTTPException
from typing import List, Optional
from app.schemas.schemas import TrainStateSchema, ETAPredictionSchema, TrainRouteResponse

router = APIRouter(prefix="/trains", tags=["Trains"])

# Global orchestrator reference set in main.py
orchestrator = None

def set_orchestrator(orch):
    global orchestrator
    orchestrator = orch

@router.get("", response_model=List[TrainStateSchema])
def get_all_trains():
    if not orchestrator:
        raise HTTPException(status_code=500, detail="Orchestrator not initialized")
    state = orchestrator.get_full_simulation_state()
    return state.trains

@router.get("/{train_id}", response_model=TrainStateSchema)
def get_train_details(train_id: str):
    if not orchestrator:
        raise HTTPException(status_code=500, detail="Orchestrator not initialized")
    clean_id = train_id.replace("TRAIN_", "").strip()
    trains_list = list(orchestrator.active_trains.values()) if isinstance(orchestrator.active_trains, dict) else orchestrator.active_trains
    found = any(
        getattr(t, "train_id", None) == train_id 
        or getattr(t, "train_number", None) == clean_id 
        or (isinstance(t, dict) and (t.get("train_id") == train_id or t.get("train_number") == clean_id)) 
        for t in trains_list
    )
    if not found:
        sync_res = orchestrator.sync_live_telemetry(clean_id)
        if sync_res is None:
            raise HTTPException(status_code=404, detail=f"Train {train_id} not found")

    state = orchestrator.get_full_simulation_state()
    for t in state.trains:
        if t.train_id == train_id or t.train_id == f"TRAIN_{clean_id}" or t.train_number == clean_id:
            return t
    raise HTTPException(status_code=404, detail=f"Train {train_id} not found")

@router.get("/{train_id}/eta", response_model=ETAPredictionSchema)
def get_train_eta(train_id: str):
    if not orchestrator:
        raise HTTPException(status_code=500, detail="Orchestrator not initialized")
    clean_id = train_id.replace("TRAIN_", "").strip()
    trains_list = list(orchestrator.active_trains.values()) if isinstance(orchestrator.active_trains, dict) else orchestrator.active_trains
    found = any(
        getattr(t, "train_id", None) == train_id 
        or getattr(t, "train_number", None) == clean_id 
        or (isinstance(t, dict) and (t.get("train_id") == train_id or t.get("train_number") == clean_id)) 
        for t in trains_list
    )
    if not found:
        sync_res = orchestrator.sync_live_telemetry(clean_id)
        if sync_res is None:
            raise HTTPException(status_code=404, detail=f"Train {train_id} not found")

    eta = orchestrator.compute_dynamic_eta(train_id)
    if not eta:
        raise HTTPException(status_code=404, detail=f"ETA unavailable for train {train_id}")
    return eta

@router.get("/{train_id}/route", response_model=TrainRouteResponse)
def get_train_route(train_id: str, journey_date: Optional[str] = None):
    if not orchestrator:
        raise HTTPException(status_code=500, detail="Orchestrator not initialized")
    route_data = orchestrator.get_train_route_timeline(train_id, journey_date=journey_date)
    if not route_data:
        raise HTTPException(status_code=404, detail=f"Train {train_id} route not found")
    return route_data


