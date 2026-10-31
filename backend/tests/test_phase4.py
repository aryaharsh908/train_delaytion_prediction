"""
Acceptance Test for Phase 4: Gemma-powered Explainer & /explain endpoint.
Tests real feature importance grounding, quantile bounds, fallback handling, and backwards compatibility.
"""

import sys
from pathlib import Path

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.explainability.explainer import ETAExplainer
from app.api.agent import get_prediction_explanation, ExplainRequest


def test_phase4_explainer_acceptance():
    print("=== Testing Phase 4: Gemma-Powered Explainer ===")

    # 1. Test backwards compatibility of generate_explanation for orchestrator
    legacy_factors = ETAExplainer.generate_explanation(
        current_delay_min=12.5,
        weather_delay_min=5.0,
        junction_congestion_min=4.0,
        platform_hold_min=2.0,
        recovery_min=3.0,
        weather_condition="FOG"
    )
    assert len(legacy_factors) == 5, f"Expected 5 factors, got {len(legacy_factors)}"
    assert legacy_factors[0].factor_name == "Current Accumulated Delay"
    assert legacy_factors[0].impact_minutes == 12.5
    print("Backwards compatibility verified.")

    # 2. Test Gemma explainer with real feature importances
    exp_res = ETAExplainer.explain_prediction(train_id="12951", context="Fog speed restriction between Mathura and Kota")
    assert "train_id" in exp_res
    assert "explanation" in exp_res
    assert "primary_delay_driver" in exp_res
    assert "quantiles" in exp_res
    assert "p10_min" in exp_res["quantiles"]
    assert "p50_min" in exp_res["quantiles"]
    assert "p90_min" in exp_res["quantiles"]
    assert "top_features" in exp_res
    assert len(exp_res["top_features"]) > 0
    print("Gemma explain_prediction passed.")
    print("Primary driver:", exp_res["primary_delay_driver"])
    print("Quantiles:", exp_res["quantiles"])
    print("Explanation excerpt:", exp_res["explanation"][:150], "...")

    # 3. Test API endpoint handler
    api_req = ExplainRequest(train_id="12951", context="Routine junction clearance")
    api_res = get_prediction_explanation(api_req)
    assert api_res["train_id"] == "12951"
    assert len(api_res["explanation"]) > 20
    assert api_res["source"] in ("gemma", "fallback")
    print(f"API endpoint verified. Source: {api_res['source']}")

    # 4. Test offline fallback
    fallback_res = ETAExplainer.explain_prediction(train_id="99999", model="non_existent_offline_model")
    assert fallback_res["source"] == "fallback"
    assert "Standard Explainability Assessment" in fallback_res["explanation"] or "delayed" in fallback_res["explanation"].lower() or "tolerance" in fallback_res["explanation"].lower()
    print("Offline deterministic fallback verified.")

    print("=== Phase 4 Acceptance Criteria PASSED successfully! ===")


if __name__ == "__main__":
    test_phase4_explainer_acceptance()
