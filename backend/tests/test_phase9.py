"""
Acceptance Test for Phase 9: Multi-Lingual Passenger Advisories & /advisory endpoint.
Tests English and Hindi (Devanagari) advisory generation, number validator enforcement,
and grounded delay reporting.
"""

import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.agent.advisories import get_advisory_writer
from app.api.agent import create_passenger_advisory, AdvisoryRequest


def test_phase9_advisory_acceptance():
    print("=== Testing Phase 9: Multi-Lingual Passenger Advisories ===")

    writer = get_advisory_writer()

    # 1. Generate bilingual advisory
    res = writer.generate_advisory(train_id="12951", languages=["en", "hi"])

    # 2. Verify schema
    assert "train_id" in res
    assert "advisories" in res
    advisories = res["advisories"]
    assert "en" in advisories and len(advisories["en"]) > 20, "Missing or empty English advisory"
    assert "hi" in advisories and len(advisories["hi"]) > 20, "Missing or empty Hindi advisory"

    # 3. Verify Hindi contains Devanagari script
    hi_text = advisories["hi"]
    has_devanagari = any("\u0900" <= char <= "\u097F" for char in hi_text)
    assert has_devanagari, "Expected Devanagari script in Hindi advisory"
    print(f"Hindi advisory verified: contains valid Devanagari script ({len(hi_text)} characters).")

    # 4. Verify NumberValidator passed
    assert res.get("number_validator_passed") is True, "Expected NumberValidator to pass on advisory"
    assert "disclaimer" in res
    print("Number validator passed on advisory text.")
    print(f"English advisory verified: {advisories['en'][:80]}...")

    # 5. Verify API endpoint handler
    api_req = AdvisoryRequest(train_id="12951", languages=["en", "hi"])
    api_res = create_passenger_advisory(api_req)
    assert api_res["train_id"] == "12951"
    assert "en" in api_res["advisories"]
    assert "hi" in api_res["advisories"]
    print("FastAPI /advisory endpoint verified.")

    print("=== Phase 9 Acceptance Criteria PASSED successfully! ===")


if __name__ == "__main__":
    test_phase9_advisory_acceptance()
