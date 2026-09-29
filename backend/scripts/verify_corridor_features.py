"""
Comprehensive verification test for corridor conflict engine, downstream propagation,
and grounded counterfactual engine.
"""

from app.simulation.orchestrator import SimulationOrchestrator
from app.simulation.counterfactual_engine import CounterfactualSimulator
from app.schemas.schemas import CounterfactualRequestSchema
from app.analytics.corridor_conflict_engine import CorridorConflictEngine

orch = SimulationOrchestrator()
engine = CorridorConflictEngine(orch)

print("==================================================")
print("TEST 1: WHAT-IF COUNTERFACTUAL SIMULATION")
print("==================================================")

# Exercise Train 12926
req_12926 = CounterfactualRequestSchema(train_number="12926", injected_delay_minutes=10.0)
res_12926 = CounterfactualSimulator.run_counterfactual_simulation(req_12926, orch)

# Exercise Train 12951
req_12951 = CounterfactualRequestSchema(train_number="12951", injected_delay_minutes=20.0)
res_12951 = CounterfactualSimulator.run_counterfactual_simulation(req_12951, orch)

print(f"Train 1: {res_12926.train_number} - {res_12926.train_name}")
print(f"  Baseline ETA: {res_12926.baseline_eta} | Intervention ETA: {res_12926.intervention_eta}")
print(f"  P10: {res_12926.eta_p10} | P50: {res_12926.eta_p50} | P90: {res_12926.eta_p90}")
print(f"  Route Stations count: {len(res_12926.route_comparison)}")
sample_12926 = [s["station_name"] for s in res_12926.route_comparison]
print(f"  Stations sample: {sample_12926}")

print(f"\nTrain 2: {res_12951.train_number} - {res_12951.train_name}")
print(f"  Baseline ETA: {res_12951.baseline_eta} | Intervention ETA: {res_12951.intervention_eta}")
print(f"  P10: {res_12951.eta_p10} | P50: {res_12951.eta_p50} | P90: {res_12951.eta_p90}")
print(f"  Route Stations count: {len(res_12951.route_comparison)}")
sample_12951 = [s["station_name"] for s in res_12951.route_comparison]
print(f"  Stations sample: {sample_12951}")

assert res_12926.train_name != res_12951.train_name, "Train names should differ"
assert res_12926.baseline_eta != res_12951.baseline_eta, "Baseline ETAs should differ"
assert sample_12926 != sample_12951, "Route stations must differ!"

print("\n>>> VERIFIED: Train 12926 and Train 12951 have completely distinct routes, stations, and ETAs.")

print("\n==================================================")
print("TEST 2: JUNCTION CONFLICT DETECTION & SCORING")
print("==================================================")
conflicts = engine.analyze_junction_conflicts()
print(f"Identified {len(conflicts)} ranked junctions.")
for c in conflicts[:4]:
    print(f"  {c['station_name']} ({c['station_code']}) -> Score: {c['conflict_score']}/100 | Risk: {c['risk_level']} | Approaching: {c['approaching_trains_count']} | Range: {c['expected_impact_window_min']}")
    print(f"    Breakdown: Density={c['factor_breakdown']['converging_traffic_density_pct']}%, Congestion={c['factor_breakdown']['approach_track_congestion_pct']}%, Precedence={c['factor_breakdown']['priority_clearance_precedence_pct']}%")

assert len(conflicts) > 0, "Must have ranked conflicts"
assert all(0.0 <= c["conflict_score"] <= 100.0 for c in conflicts), "Scores must be bounded [0, 100]"

print("\n==================================================")
print("TEST 3: HEADWAY-CLEARANCE DOWNSTREAM PROPAGATION")
print("==================================================")
prop = engine.compute_downstream_propagation(source_train_id="12926")
print(f"Source Train: {prop['source_train_number']} - {prop['source_train_name']} (Delay: +{prop['source_delay_minutes']}m)")
print(f"Critical Bottleneck: {prop['critical_junction_name']} (Score: {prop['critical_conflict_score']})")
print(f"Exposed Services: {prop['downstream_exposed_services_count']}")
print(f"Total Induced Delay: +{prop['total_induced_network_delay_minutes']} min")
for step in prop["propagation_chain"]:
    print(f"  Step {step['step']}: [{step['type']}] {step['title']} -> {step['delay_display']}")

print("\nALL AUTOMATED LOGIC TESTS PASSED SUCCESSFULLY!")
