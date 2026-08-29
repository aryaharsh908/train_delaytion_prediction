import sys
import os

sys.path.insert(0, r"c:\Users\aryah\train_schedule\backend")

import random
from datetime import datetime, timedelta

from app.db.database import SessionLocal, engine
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
    season_factor = 1.25 if dt_obj.month in [11, 12, 1] else 1.0
    
    for train_num in corridors:
        catalog = route_catalogs[train_num]
        
        # 35% of runs start with 0 delay (On Time), but accumulate cascading delays downstream!
        # 65% of runs start with initial origin delay
        scenario = random.choice(["ON_TIME_START", "SLIGHT_DELAY_START", "HEAVY_DELAY_START"])
        if scenario == "ON_TIME_START":
            accum_delay = 0.0
        elif scenario == "SLIGHT_DELAY_START":
            accum_delay = random.uniform(5.0, 15.0) * season_factor
        else:
            accum_delay = random.uniform(25.0, 60.0) * season_factor
        
        total_route_dist = catalog[-1]["dist"] if catalog else 1000.0

        for idx, st in enumerate(catalog):
            st_code = st["code"]
            st_name = st["name"].upper()
            sec_dist = st["dist"] - (catalog[idx - 1]["dist"] if idx > 0 else 0.0)

            # Check bottleneck junction keywords (CNB, PRYJ, DDU, GAYA, RTM, BRC, BPL, NGP, BZA, TVC)
            is_junction = any(jk in st_name or jk in st_code for jk in ["JN", "JUNCTION", "CENTRAL", "TERMINUS", "CANTT", "DDU", "CNB", "PRYJ", "RTM", "BRC", "BPL", "NGP", "BPQ", "BZA", "KPD", "TVC"])

            # Cascading non-linear delay compounding vs speed recovery logic
            if is_junction and accum_delay > 0:
                # Precedence hold / platform queuing penalty at major junction
                accum_delay += random.uniform(8.0, 22.0)
            elif idx > 0 and sec_dist > 75.0 and accum_delay > 15.0:
                # High speed recovery on long section
                recovery_mins = min(accum_delay * 0.2, (sec_dist / 100.0) * 5.0)
                accum_delay = max(0.0, accum_delay - recovery_mins)
            else:
                # Standard section variance
                accum_delay += random.uniform(0.5, 4.0)

            arr_delay = round(accum_delay, 1)
            dep_delay = round(accum_delay + random.uniform(1.0, 4.0), 1)
            
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
                distance_to_destination=float(total_route_dist - st["dist"])
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
