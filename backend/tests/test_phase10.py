"""
Acceptance Test for Phase 10: Operations Reports (Handover & Post-Incident).
Tests shift handover briefing synthesis, incident timeline reconstruction,
root-cause analysis, and regulatory rule citations.
"""

import sys
from pathlib import Path

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.agent.reports import get_report_generator
from app.api.agent import generate_operations_report, ReportRequest


def test_phase10_reports_acceptance():
    print("=== Testing Phase 10: Operational Reports ===")

    generator = get_report_generator()

    # 1. Test Shift Handover Report
    handover = generator.generate_shift_handover()
    assert "summary" in handover
    assert "report_type" in handover and handover["report_type"] == "shift_handover"
    assert "disclaimer" in handover
    assert "active_bottlenecks" in handover or "open_action_items" in handover
    print("Shift handover report verified.")
    print(f"Handover summary: {handover['summary'][:100]}...")

    # 2. Test Post-Incident Report for a seeded incident
    incident_res = generator.generate_post_incident(incident_id="INC_2026_TEST_01", train_id="12951")
    assert "incident_id" in incident_res
    assert incident_res["incident_id"] == "INC_2026_TEST_01"
    assert "root_cause" in incident_res and len(incident_res["root_cause"]) > 5
    assert "timeline" in incident_res and isinstance(incident_res["timeline"], list)
    assert len(incident_res["timeline"]) > 0, "Expected non-empty incident timeline"
    assert "cascading_trains_count" in incident_res
    assert "rule_citations" in incident_res
    print("Post-incident report verified.")
    print(f"Root cause: {incident_res['root_cause']}")
    print(f"Timeline steps: {len(incident_res['timeline'])}")
    print(f"Rule citations: {incident_res.get('rule_citations')}")

    # 3. Test API endpoint handler with handover request
    api_handover = generate_operations_report(ReportRequest(type="handover"))
    assert api_handover["report_type"] == "shift_handover"
    assert "summary" in api_handover
    print("FastAPI /report (type=handover) verified.")

    # 4. Test API endpoint handler with incident request
    api_incident = generate_operations_report(ReportRequest(type="incident", incident_id="INC_TEST_99", train_id="12951"))
    assert api_incident["report_type"] == "post_incident"
    assert api_incident["incident_id"] == "INC_TEST_99"
    assert len(api_incident["timeline"]) > 0
    print("FastAPI /report (type=incident) verified.")

    print("=== Phase 10 Acceptance Criteria PASSED successfully! ===")


if __name__ == "__main__":
    test_phase10_reports_acceptance()
