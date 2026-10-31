"""
Agent and Gemma 4 Reasoning API Endpoints.
Provides health check, dispatch recommendation, chat, explainability, advisories, vision, and run audit logs.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Path, UploadFile, File, Form
from typing import Dict, List, Any, Optional
from datetime import datetime

from app.agent.harness import get_gemma_harness
from app.agent.dispatcher_agent import get_dispatcher_agent
from app.db.database import get_db
from app.db.models import AgentRun
from sqlalchemy.orm import Session
from pydantic import BaseModel

router = APIRouter(prefix="/agent", tags=["Gemma 4 Agent"])

_orchestrator_instance = None

def set_orchestrator(orchestrator):
    global _orchestrator_instance
    _orchestrator_instance = orchestrator

def _get_orchestrator():
    if _orchestrator_instance is not None:
        return _orchestrator_instance
    from app.main import orchestrator
    return orchestrator


@router.get("/health")
def get_agent_health():
    """
    Checks Gemma model reachability and backend status.
    Tests live generation. If the API key is missing or offline, gracefully returns fallback without crashing.
    """
    harness = get_gemma_harness()
    try:
        res = harness.generate(
            prompt="Ping test. Reply with 'Gemma online' in two words.",
            model="gemma-4-26b-a4b-it",
            use_cache=False
        )
        status_str = "healthy" if res.get("source") == "gemma" else "fallback_operational"
        return {
            "status": status_str,
            "backend": harness.backend_type,
            "model": res.get("model"),
            "source": res.get("source"),
            "reply": res.get("text", "").strip(),
            "latency_ms": res.get("latency_ms", 0.0),
            "tokens": res.get("tokens", 0)
        }
    except Exception as e:
        return {
            "status": "error",
            "backend": harness.backend_type,
            "source": "fallback",
            "error": str(e)
        }


class DispatchRequest(BaseModel):
    alert_id: Optional[str] = None
    train_id: Optional[str] = None
    context: Optional[str] = None
    model: Optional[str] = "gemma-4-31b-it"


@router.post("/dispatch")
def run_dispatch_reasoning(req: DispatchRequest):
    """
    Runs Gemma 4 Dispatch Planner on an alert ID or train ID.
    Performs multi-step tool calls, tests at least two counterfactual interventions,
    and returns mathematically grounded operating recommendation with full audit trace.
    """
    agent = get_dispatcher_agent()
    result = agent.run_dispatch(
        alert_id=req.alert_id,
        train_id=req.train_id,
        context=req.context,
        model=req.model or "gemma-4-31b-it"
    )
    return result


class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str
    model: Optional[str] = "gemma-4-26b-a4b-it"


@router.post("/chat")
def control_room_chat(req: ChatRequest):
    """
    Multi-turn conversational control-room assistant.
    Maintains session history and executes read-only + counterfactual railway tools.
    """
    from app.agent.chat import get_control_room_chat
    chat = get_control_room_chat()
    return chat.process_message(
        session_id=req.session_id,
        message=req.message,
        model=req.model or "gemma-4-26b-a4b-it"
    )


class ExplainRequest(BaseModel):
    train_id: str
    context: Optional[str] = None
    model: Optional[str] = "gemma-4-26b-a4b-it"


@router.post("/explain")
def get_prediction_explanation(req: ExplainRequest):
    """
    Generates Gemma 4 operational explanation for a train ETA forecast or alert,
    grounded in empirical feature importances and P10/P50/P90 quantile bounds.
    """
    from app.explainability.explainer import ETAExplainer
    return ETAExplainer.explain_prediction(
        train_id=req.train_id,
        context=req.context,
        model=req.model or "gemma-4-26b-a4b-it"
    )


@router.post("/vision")
async def analyze_control_image(
    file: UploadFile = File(..., description="Control room screenshot or track diagram"),
    prompt: Optional[str] = Form(None)
):
    """
    Multimodal visual analyst endpoint.
    Extracts structured facts (trains, delays, signals) from control room screenshots.
    Requires human controller confirmation before applying.
    """
    from app.agent.vision import get_visual_analyst
    analyst = get_visual_analyst()
    content = await file.read()
    try:
        return analyst.analyze_image(
            image_bytes=content,
            mime_type=file.content_type or "image/png",
            user_prompt=prompt
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image analysis error: {e}")


class AdvisoryRequest(BaseModel):
    train_id: str
    languages: Optional[List[str]] = ["en", "hi"]
    model: Optional[str] = "gemma-4-26b-a4b-it"


@router.post("/advisory")
def create_passenger_advisory(req: AdvisoryRequest):
    """
    Generates multi-lingual passenger announcements in English and Hindi (Devanagari),
    validated against the NumberValidator.
    """
    from app.agent.advisories import get_advisory_writer
    writer = get_advisory_writer()
    return writer.generate_advisory(
        train_id=req.train_id,
        languages=req.languages,
        model=req.model or "gemma-4-26b-a4b-it"
    )


class ReportRequest(BaseModel):
    type: str = "handover"  # "handover" or "incident"
    incident_id: Optional[str] = None
    train_id: Optional[str] = None
    time_range: Optional[str] = None
    model: Optional[str] = "gemma-4-26b-a4b-it"


@router.post("/report")
def generate_operations_report(req: ReportRequest):
    """
    Generates formal shift handover reports or post-incident disruption analysis.
    """
    from app.agent.reports import get_report_generator
    gen = get_report_generator()
    rep_type = req.type.lower()
    if rep_type in ("handover", "shift_handover"):
        return gen.generate_shift_handover(
            time_range=req.time_range,
            model=req.model or "gemma-4-26b-a4b-it"
        )
    elif rep_type in ("incident", "post_incident"):
        return gen.generate_post_incident(
            incident_id=req.incident_id,
            train_id=req.train_id,
            model=req.model or "gemma-4-26b-a4b-it"
        )
    else:
        raise HTTPException(status_code=400, detail=f"Invalid report type '{req.type}'. Allowed: 'handover', 'incident'.")


class ScenarioRequest(BaseModel):
    category: Optional[str] = None
    junction_code: Optional[str] = None
    primary_train: Optional[str] = None
    model: Optional[str] = "gemma-4-26b-a4b-it"


@router.post("/scenario")
def generate_synthetic_scenario(req: Optional[ScenarioRequest] = None):
    """
    Generates a synthetic railway disruption scenario for evaluation or drills.
    """
    from app.agent.scenarios import get_scenario_generator
    gen = get_scenario_generator()
    cat = req.category if req else None
    junc = req.junction_code if req else None
    train = req.primary_train if req else None
    model = req.model if req else "gemma-4-26b-a4b-it"
    return gen.generate_scenario(category=cat, junction_code=junc, primary_train=train, model=model)


@router.get("/runs/{run_id}")
def get_agent_run(run_id: str = Path(..., description="Agent run UUID"), db: Session = Depends(get_db)):
    """Fetches full audit trace for an agent reasoning run."""
    run = db.query(AgentRun).filter(AgentRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Agent run not found")
    return {
        "id": run.id,
        "model": run.model,
        "prompt": run.prompt,
        "system_prompt": run.system_prompt,
        "tool_calls": run.tool_calls,
        "tool_results": run.tool_results,
        "output": run.output,
        "latency_ms": run.latency_ms,
        "tokens_used": run.tokens_used,
        "source": run.source,
        "status": run.status,
        "created_at": run.created_at
    }


class DecisionActionRequest(BaseModel):
    controller_id: str = "CHIEF_CONTROLLER_1"
    edited_order: Optional[str] = None
    notes: Optional[str] = None


@router.post("/decisions/{decision_id}/approve")
def approve_decision(decision_id: str, req: Optional[DecisionActionRequest] = None, db: Session = Depends(get_db)):
    """Approves a pending dispatch operating order with controller sign-off."""
    from app.db.models import AgentDecision
    dec = db.query(AgentDecision).filter(AgentDecision.id == decision_id).first()
    if not dec:
        raise HTTPException(status_code=404, detail="Decision record not found")
    dec.status = "APPROVED"
    dec.controller_id = req.controller_id if req else "CHIEF_CONTROLLER"
    if req and req.edited_order:
        dec.edited_order = req.edited_order
    if req and req.notes:
        dec.notes = req.notes
    dec.decided_at = datetime.now().isoformat()
    db.commit()
    return {"status": "success", "decision_id": dec.id, "state": dec.status, "controller_id": dec.controller_id}


@router.post("/decisions/{decision_id}/reject")
def reject_decision(decision_id: str, req: Optional[DecisionActionRequest] = None, db: Session = Depends(get_db)):
    """Rejects a pending dispatch operating order."""
    from app.db.models import AgentDecision
    dec = db.query(AgentDecision).filter(AgentDecision.id == decision_id).first()
    if not dec:
        raise HTTPException(status_code=404, detail="Decision record not found")
    dec.status = "REJECTED"
    dec.controller_id = req.controller_id if req else "CHIEF_CONTROLLER"
    if req and req.notes:
        dec.notes = req.notes
    dec.decided_at = datetime.now().isoformat()
    db.commit()
    return {"status": "success", "decision_id": dec.id, "state": dec.status, "controller_id": dec.controller_id}


@router.get("/decisions")
def list_decisions(status: Optional[str] = None, db: Session = Depends(get_db)):
    """Lists dispatch decisions filtered by status (PENDING, APPROVED, REJECTED)."""
    from app.db.models import AgentDecision
    q = db.query(AgentDecision)
    if status:
        q = q.filter(AgentDecision.status == status.upper())
    recs = q.order_by(AgentDecision.created_at.desc()).limit(50).all()
    return [
        {
            "id": r.id,
            "run_id": r.run_id,
            "status": r.status,
            "controller_id": r.controller_id,
            "edited_order": r.edited_order,
            "notes": r.notes,
            "decided_at": r.decided_at,
            "created_at": r.created_at
        }
        for r in recs
    ]
