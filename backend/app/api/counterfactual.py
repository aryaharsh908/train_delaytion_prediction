from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from app.schemas.schemas import CounterfactualRequestSchema, CounterfactualResponseSchema
from app.simulation.counterfactual_engine import CounterfactualSimulator

router = APIRouter(prefix="/counterfactual", tags=["Counterfactual What-If Engine"])

_orchestrator_instance = None

def set_orchestrator(orchestrator):
    global _orchestrator_instance
    _orchestrator_instance = orchestrator

@router.post("/simulate", response_model=CounterfactualResponseSchema)
def simulate_counterfactual_intervention(req: CounterfactualRequestSchema):
    """
    Executes a structural What-If operational intervention simulation.
    Interventions:
    - PRIORITY_BOOST: Express precedence upgrade (recovers delay, saves passenger-minutes).
    - TSR_IMPOSITION: Temporary speed restriction on section.
    - WEATHER_SPEED_DROP: Fog / rain corridor speed drop.
    """
    if _orchestrator_instance is None:
        from app.main import orchestrator
        orch = orchestrator
    else:
        orch = _orchestrator_instance

    try:
        res = CounterfactualSimulator.run_counterfactual_simulation(req, orch)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Counterfactual simulation error: {str(e)}")
