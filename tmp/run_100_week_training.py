import sys
import os

sys.path.insert(0, r"c:\Users\aryah\train_schedule\backend")

import random
from datetime import datetime, timedelta

from app.db.session import SessionLocal, engine
from app.db.models import Base, HistoricalTrainRun
from app.ml.historical_pipeline import HistoricalMLPipeline
from app.simulation.orchestrator import route_catalogs


# Ensure tables exist
Base.metadata.create_all(bind=engine)

db = SessionLocal()

print("--- Generating 100-Week Historical Station Running Status Data ---")

# Delete old historical runs for a clean 100-week dataset
db.query(HistoricalTrainRun).delete()
db.commit()

base_date = datetime.now() - timedelta(weeks=100)
sample_runs = []

corridors = list(route_catalogs.keys())

for week in range(100):
    run_date = (base_date + timedelta(weeks=week)).strftime("%Y-%m-%d")
    dt_obj = datetime.strptime(run_date, "%Y-%m-%d")
    dow = dt_obj.weekday()
    
    # Weekly seasonality & random traffic variance factor
    season_factor = 1.2 if dt_obj.month in [11, 12, 1] else 0.95
    
    for train_num in corridors:
        catalog = route_catalogs[train_num]
        accum_delay = float(random.choice([0, 5, 12, 25, 40, 60])) * season_factor
        
        for idx, st in enumerate(catalog):
            # Speedup recovery or delay accumulation simulation
            if accum_delay > 10.0 and idx % 3 == 0:
                accum_delay = max(0.0, accum_delay - random.uniform(2.0, 6.0))
            else:
                accum_delay += random.uniform(0.5, 3.5)
                
            arr_delay = round(accum_delay, 1)
            dep_delay = round(accum_delay + random.uniform(1.0, 3.0), 1)
            
            run_rec = HistoricalTrainRun(
                journey_date=run_date,
                train_number=train_num,
                station_code=st["code"],
                station_name=st["name"],
                station_sequence=idx + 1,
                scheduled_arrival=st["sched_arr"],
                actual_arrival=st["sched_arr"],
                arrival_delay_minutes=arr_delay,
                scheduled_departure=st["sched_dep"],
                actual_departure=st["sched_dep"],
                departure_delay_minutes=dep_delay,
                distance_from_origin=float(st["dist"]),
                distance_to_destination=float(catalog[-1]["dist"] - st["dist"]),
                weather_condition="CLEAR" if season_factor < 1.1 else "FOG"
            )
            sample_runs.append(run_rec)

print(f"Generated {len(sample_runs)} historical station records across 100 weeks and 10 train corridors.")
db.bulk_save_objects(sample_runs)
db.commit()

print("\n--- Training ML Pipeline on 100-Week Historical Dataset ---")
pipeline = HistoricalMLPipeline(db)
meta = pipeline.train_and_version_model()

print("\n100-Week Training Metadata Summary:")
print("Model Version:", meta["model_version"])
print("Dataset Size:", meta["dataset_size"])
print("Training Date Range:", meta["training_start_date"], "to", meta["training_end_date"])
print("Comparison Metrics:")
print("  - GBR Model MAE:", meta["comparison"]["gbr_model"]["mae"], "| RMSE:", meta["comparison"]["gbr_model"]["rmse"])
print("  - Linear Reg MAE:", meta["comparison"]["linear_regression"]["mae"], "| RMSE:", meta["comparison"]["linear_regression"]["rmse"])
print("  - Naive Base MAE:", meta["comparison"]["naive_timetable_baseline"]["mae"], "| RMSE:", meta["comparison"]["naive_timetable_baseline"]["rmse"])

print("\nFeature Importances:")
for k, v in meta["feature_importance"].items():
    print(f"  - {k}: {v}")

db.close()
