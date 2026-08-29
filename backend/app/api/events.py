from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import random

router = APIRouter(prefix="/events", tags=["Events & Incident Injection"])

orchestrator = None

def set_orchestrator(orch):
    global orchestrator
    orchestrator = orch

class IncidentInjectRequest(BaseModel):
    event_type: str  # FOG, HEAVY_RAIN, SIGNAL_FAILURE, TRACK_FAILURE, PLATFORM_OCCUPIED, JUNCTION_CONGESTION, MAINTENANCE_BLOCK, CHAIN_PULLING, ACCIDENT
    section_id: str
    train_id: Optional[str] = None
    severity: Optional[str] = "HIGH"
    duration_minutes: Optional[float] = 20.0
    visibility_meters: Optional[float] = 150.0

@router.post("/inject")
def inject_event(req: IncidentInjectRequest):
    if not orchestrator:
        raise HTTPException(status_code=500, detail="Orchestrator not initialized")
        
    inc = orchestrator.incident_sim.inject_incident(
        event_type=req.event_type,
        section_id=req.section_id,
        severity=req.severity,
        duration_min=req.duration_minutes,
        visibility_m=req.visibility_meters
    )
    
    # Update weather/state on graph
    if req.event_type in ["FOG", "HEAVY_RAIN"]:
        orchestrator.graph.update_section_state(req.section_id, weather=req.event_type)
    elif req.event_type in ["SIGNAL_FAILURE", "TRACK_FAILURE", "MAINTENANCE_BLOCK", "ACCIDENT"]:
        orchestrator.graph.update_section_state(req.section_id, is_blocked=True)
    elif req.event_type in ["JUNCTION_CONGESTION", "PLATFORM_OCCUPIED"]:
        orchestrator.graph.update_section_state(req.section_id, congestion=0.85)

    orchestrator.coa_sim.log_event(
        event_type=f"INJECTED_{req.event_type}",
        description=f"Incident injected: {req.event_type} on section {req.section_id}",
        section_id=req.section_id,
        severity=req.severity,
        duration_min=req.duration_minutes
    )

    # Apply delay impact to active trains
    trains_list = list(orchestrator.active_trains.values()) if isinstance(orchestrator.active_trains, dict) else orchestrator.active_trains
    for train in trains_list:
        t_sec = train.get("current_section_id") if isinstance(train, dict) else getattr(train, "current_section_id", None)
        t_id = train.get("train_id") if isinstance(train, dict) else getattr(train, "train_id", None)
        
        if t_sec == req.section_id or t_id == req.train_id or req.section_id in ["SEC_MTJ_KOTA", "SEC_CNB_PRYJ", "SEC_ALL"]:
            
            if req.event_type == "CHAIN_PULLING":
                dist_into = train.get("distance_into_section_km", 5.0) if isinstance(train, dict) else getattr(train, "distance_into_section_km", 5.0)
                sec_len = 50.0
                dist_to_station = min(dist_into, abs(sec_len - dist_into))
                next_st = train.get("next_station_name", "Station") if isinstance(train, dict) else getattr(train, "next_station_name", "Station")
                
                if dist_to_station <= 1.0:
                    delay_add = round(random.uniform(6.0, 8.0), 1)
                    desc = f"Alarm chain pulled near {next_st} (+{delay_add:.0f}m - station approach hold)"
                else:
                    delay_add = round(random.uniform(10.0, 15.0), 1)
                    desc = f"Alarm chain pulled mid-route (+{delay_add:.0f}m - ALP track walk & brake reset)"
                
                if isinstance(train, dict):
                    train["current_delay_minutes"] = train.get("current_delay_minutes", 0.0) + delay_add
                    train["status"] = "CRITICAL_DELAY"
                    train["last_event_description"] = desc
                else:
                    train.current_delay_minutes += delay_add
                    train.status = "CRITICAL_DELAY"
                    train.last_event_description = desc
                    
            elif req.event_type == "PLATFORM_OCCUPIED":
                delay_add = 12.0
                desc = f"Platform occupancy hold on {req.section_id} (+12m)"
                if isinstance(train, dict):
                    train["current_delay_minutes"] = train.get("current_delay_minutes", 0.0) + delay_add
                    train["status"] = "SLIGHT_DELAY"
                    train["last_event_description"] = desc
                else:
                    train.current_delay_minutes += delay_add
                    train.status = "SLIGHT_DELAY"
                    train.last_event_description = desc
                    
            elif req.event_type == "MAINTENANCE_BLOCK":
                delay_add = 25.0
                desc = f"Track maintenance block on {req.section_id} (+25m)"
                if isinstance(train, dict):
                    train["current_delay_minutes"] = train.get("current_delay_minutes", 0.0) + delay_add
                    train["status"] = "CRITICAL_DELAY"
                    train["last_event_description"] = desc
                else:
                    train.current_delay_minutes += delay_add
                    train.status = "CRITICAL_DELAY"
                    train.last_event_description = desc

            elif req.event_type == "SIGNAL_FAILURE":
                delay_add = 15.0
                desc = f"Signal failure hold on {req.section_id} (+15m)"
                if isinstance(train, dict):
                    train["current_delay_minutes"] = train.get("current_delay_minutes", 0.0) + delay_add
                    train["status"] = "CRITICAL_DELAY"
                    train["last_event_description"] = desc
                else:
                    train.current_delay_minutes += delay_add
                    train.status = "CRITICAL_DELAY"
                    train.last_event_description = desc
                    
            elif req.event_type == "FOG":
                delay_add = 12.0
                desc = f"Dense fog speed restriction on {req.section_id} (+12m)"
                if isinstance(train, dict):
                    train["current_delay_minutes"] = train.get("current_delay_minutes", 0.0) + delay_add
                    train["status"] = "SLIGHT_DELAY"
                    train["last_event_description"] = desc
                else:
                    train.current_delay_minutes += delay_add
                    train.status = "SLIGHT_DELAY"
                    train.last_event_description = desc

            elif req.event_type == "HEAVY_RAIN":
                delay_add = 8.0
                desc = f"Heavy monsoon rain speed restriction on {req.section_id} (+8m)"
                if isinstance(train, dict):
                    train["current_delay_minutes"] = train.get("current_delay_minutes", 0.0) + delay_add
                    train["status"] = "SLIGHT_DELAY"
                    train["last_event_description"] = desc
                else:
                    train.current_delay_minutes += delay_add
                    train.status = "SLIGHT_DELAY"
                    train.last_event_description = desc
                    
            elif req.event_type == "TRACK_FAILURE":
                delay_add = 30.0
                desc = f"Track block on {req.section_id} (+30m)"
                if isinstance(train, dict):
                    train["current_delay_minutes"] = train.get("current_delay_minutes", 0.0) + delay_add
                    train["status"] = "CRITICAL_DELAY"
                    train["last_event_description"] = desc
                else:
                    train.current_delay_minutes += delay_add
                    train.status = "CRITICAL_DELAY"
                    train.last_event_description = desc
                    
            elif req.event_type == "JUNCTION_CONGESTION":
                delay_add = 10.0
                desc = f"Precedence yield at junction on {req.section_id} (+10m)"
                if isinstance(train, dict):
                    train["current_delay_minutes"] = train.get("current_delay_minutes", 0.0) + delay_add
                    train["status"] = "SLIGHT_DELAY"
                    train["last_event_description"] = desc
                else:
                    train.current_delay_minutes += delay_add
                    train.status = "SLIGHT_DELAY"
                    train.last_event_description = desc

    return {"status": "injected", "incident": inc}


@router.post("/clear")
def clear_all_events():
    if not orchestrator:
        raise HTTPException(status_code=500, detail="Orchestrator not initialized")
    orchestrator.incident_sim.clear_all_incidents()
    orchestrator.graph._initialize_default_corridor()
    return {"status": "cleared"}

@router.get("/coa")
def get_coa_events():
    if not orchestrator:
        raise HTTPException(status_code=500, detail="Orchestrator not initialized")
    return orchestrator.coa_sim.get_recent_events()
