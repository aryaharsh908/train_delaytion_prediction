"""
Agent and Gemma 4 Reasoning API Endpoints.
Provides health check, dispatch recommendation, chat, explainability, advisories, vision, and run audit logs.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from app.agent.harness import get_gemma_harness
from app.db.database import get_db
from app.db.models import AgentRun
from sqlalchemy.orm import Session

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
