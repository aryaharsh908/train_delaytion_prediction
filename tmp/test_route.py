import sys
import os

sys.path.insert(0, r"c:\Users\aryah\train_schedule\backend")

from app.simulation.orchestrator import SimulationOrchestrator

orchestrator = SimulationOrchestrator()
res = orchestrator.get_train_route_timeline("12626")
print("SUCCESS! Response keys:", list(res.keys()))
print("Total station route items:", len(res["route_items"]))
print("Live Total Delay Minutes:", res["total_delay_minutes"])
print("\nFirst 5 authentic stations:")
for item in res["route_items"][:5]:
    print(f"- {item['station_code']} ({item['station_name']}) | Live Delay: {item['live_telemetry_delay_minutes']}m | ML Est Delay: {item['ml_predicted_delay_minutes']}m ({item['ml_forecasted_arrival']})")
