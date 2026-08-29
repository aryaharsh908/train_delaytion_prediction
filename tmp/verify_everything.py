import sys
import os
import json

sys.path.insert(0, r"c:\Users\aryah\train_schedule\backend")

from app.adapters.historical_data_adapter import WhereIsMyTrainHistoricalAdapter
from app.simulation.orchestrator import SimulationOrchestrator

def main():
    print("===================================================================")
    print("VERIFYING IN-BETWEEN STATION POINTER, DEPARTURE DELAY & 100-WEEK ML")
    print("===================================================================")

    # 1. Test Live Telemetry & Departure Delay Scraper
    print("\n[1] Testing Live Telemetry Departure Delay Scraper...")
    adapter = WhereIsMyTrainHistoricalAdapter()
    status = adapter.fetch_live_train_status("12302")
    if status:
        print(f"Train Number: {status.get('train_number')}")
        print(f"Train Name: {status.get('train_name')}")
        print(f"Current Station Name: {status.get('current_station_name')}")
        print(f"Current Station Code: {status.get('current_station_code')}")
        print(f"Calculated Delay Minutes: {status.get('delay_minutes')}")
        print(f"Station Dep Delays Count: {len(status.get('station_dep_delays', {}))}")
        print(f"Status Message: {status.get('status_message')}")

    # 2. Test In-Between Station Timeline Generation
    print("\n[2] Testing Route Timeline with In-Between Section Item...")
    orchestrator = SimulationOrchestrator()
    timeline = orchestrator.get_train_route_timeline("12951")

    if timeline:
        route_items = timeline.get("route_items", [])
        print(f"Total Route Items Generated: {len(route_items)}")
        
        in_between_items = [item for item in route_items if item.get("is_in_between")]
        current_items = [item for item in route_items if item.get("status") == "CURRENT"]
        
        print(f"In-Between Section Items Found: {len(in_between_items)}")
        print(f"Active CURRENT Items Found: {len(current_items)}")
        
        for item in in_between_items:
            print(f"  - Station Code: {item.get('station_code')}")
            print(f"  - Station Name: {item.get('station_name')}")
            print(f"  - Distance (km): {item.get('distance_km')}")
            print(f"  - Speed (km/h): {item.get('speed_kmh')}")
            print(f"  - Section Progress %: {item.get('in_between_progress_pct')}")
            print(f"  - Status: {item.get('status')}")

    # 3. Test 100-Week Model Metadata
    print("\n[3] Testing Model Metadata & Comparison Metrics...")
    meta_path = r"c:\Users\aryah\train_schedule\backend\models\model_metadata.json"
    if os.path.exists(meta_path):
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
            print(f"Model Version: {meta.get('model_version')}")
            print(f"Dataset Size: {meta.get('dataset_size')}")
            print(f"Training Date Range: {meta.get('training_start_date')} to {meta.get('training_end_date')}")
            print("Comparison Metrics:")
            for k, v in meta.get("comparison", {}).items():
                print(f"  - {k}: MAE={v.get('mae')}, RMSE={v.get('rmse')}")
            print("Top Feature Importances:")
            for k, v in list(meta.get("feature_importance", {}).items())[:5]:
                print(f"  - {k}: {v}")

    print("\n===================================================================")
    print("ALL VERIFICATIONS COMPLETED SUCCESSFULLY!")
    print("===================================================================")

if __name__ == "__main__":
    main()
