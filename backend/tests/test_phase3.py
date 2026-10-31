"""
Acceptance Test for Phase 3: Dispatcher Agent & /dispatch endpoint.
Tests multi-step reasoning, counterfactual evaluations, schema conformity, and audit logging.
"""

import sys
from pathlib import Path

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.api.agent import run_dispatch_reasoning, DispatchRequest, get_agent_run
from app.db.database import SessionLocal

def test_phase3_dispatcher_acceptance():
    print("=== Testing Phase 3: Dispatcher Agent & /dispatch ===")
    
    # 1. Execute dispatch run through the API endpoint handler
    api_req = DispatchRequest(train_id="12951", context="Converging conflict at Mathura Junction with 12002")
    res = run_dispatch_reasoning(api_req)
    
    # 2. Verify mandatory schema keys
    required_keys = [
        "summary", "recommendation", "alternatives_considered", 
        "rule_citations", "confidence", "operating_order_draft", "tool_trace"
    ]
    for k in required_keys:
        assert k in res, f"Missing required key: {k}"
        
    rec = res["recommendation"]
    assert "action" in rec, "Recommendation missing action"
    assert "train_id" in rec, "Recommendation missing train_id"
    assert "expected_passenger_minutes_saved" in rec, "Recommendation missing expected_passenger_minutes_saved"
    print("Schema verification passed.")
    print("Summary:", res.get("summary"))
    print("Recommendation:", rec)

    # 3. Verify at least two counterfactual simulations are present in trace
    cf_trace = [t for t in res["tool_trace"] if t.get("tool") == "run_counterfactual"]
    print(f"Counterfactual tool calls count in trace: {len(cf_trace)}")
    assert len(cf_trace) >= 2, f"Expected at least 2 counterfactual calls, found {len(cf_trace)}"
    
    # 4. Verify database audit record exists and is retrievable
    run_id = res.get("run_id")
    assert run_id, "Response missing run_id"
    db = SessionLocal()
    try:
        run_record = get_agent_run(run_id=run_id, db=db)
        assert run_record["id"] == run_id
        assert run_record["output"] is not None
        print(f"Audit log verified: Run ID={run_id}, Source={run_record['source']}, Status={run_record['status']}")
    finally:
        db.close()
        
    print("=== Phase 3 Acceptance Criteria PASSED successfully! ===")

if __name__ == "__main__":
    test_phase3_dispatcher_acceptance()
