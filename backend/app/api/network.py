from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/network", tags=["Railway Network"])

orchestrator = None

def set_orchestrator(orch):
    global orchestrator
    orchestrator = orch

@router.get("/state")
def get_network_state():
    if not orchestrator:
        raise HTTPException(status_code=500, detail="Orchestrator not initialized")
    return {
        "stations": list(orchestrator.graph.stations_dict.values()),
        "sections": list(orchestrator.graph.sections_dict.values())
    }
