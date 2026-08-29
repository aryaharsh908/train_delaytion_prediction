import sys
import os

sys.path.insert(0, r"c:\Users\aryah\train_schedule\backend")

from app.simulation.orchestrator import SimulationOrchestrator

orch = SimulationOrchestrator()

for t in ["12302", "12626", "12424", "12951"]:
    res = orch.get_train_route_timeline(t)
    print(f"================ TRAIN {t} ({res.get('train_name')}) ================")
    print("  Live Current Delay:", res.get("total_delay_minutes"), "mins")
    print("  Status Msg:", res.get("status_message"))
    print("  Station Timeline Delays (Live vs ML Dynamic Progression):")
    for item in res["route_items"]:
        print(f"    - {item['station_code']} ({item['station_name']}) [{item['status']}]: Live = +{item['live_telemetry_delay_minutes']}m | ML Est = +{item['ml_predicted_delay_minutes']}m ({item['ml_forecasted_arrival']})")
    print("\n")
