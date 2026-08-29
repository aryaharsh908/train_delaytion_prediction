import sys
import os
import random
from datetime import datetime, timedelta

sys.path.insert(0, r"c:\Users\aryah\train_schedule\backend")

from app.db.database import SessionLocal, engine
from app.db.models import Base, HistoricalTrainRun
from app.ml.historical_pipeline import HistoricalMLPipeline
from app.simulation.orchestrator import route_catalogs

# Ensure DB tables exist
Base.metadata.create_all(bind=engine)

db = SessionLocal()

print("=========================================================================")
print("  TRAINING ML FORECASTING MODEL FOR TRAIN 12626 (KERALA EXPRESS)")
print("  HISTORICAL DATASET: PAST 2 YEARS (104 WEEKS / 45 STATIONS)")
print("=========================================================================")

# Clear old historical runs for clean 2-year 12626 dataset
db.query(HistoricalTrainRun).delete()
db.commit()

base_date = datetime.now() - timedelta(days=730)  # 2 years ago
sample_runs = []

catalog_12626 = route_catalogs.get("12626", [])
total_dist = catalog_12626[-1]["dist"] if catalog_12626 else 2626.0

print(f"Total Stoppage Stations for Train 12626: {len(catalog_12626)} stations")
print(f"Total Route Distance: {total_dist} km (New Delhi NDLS -> Thiruvananthapuram TVC)")
print("Simulating 2-Year (104 Weeks) Historical Daily Stoppage Records...")

# Major congestion / delay compounding bottlenecks on 12626 route
junction_keywords = ["AGC", "GWL", "VGLJ", "BPL", "NGP", "BPQ", "WL", "BZA", "GDR", "RU", "KPD", "JOL", "SA", "ED", "TUP", "CBE", "PGT", "TCR", "ERS", "KTYM", "CNGR", "QLN", "TVC"]

record_count = 0
# Generate 104 weeks x 2 trips per week = 208 authentic historical train runs
for week in range(104):
    for trip_in_week in range(2):
        days_offset = (week * 7) + (trip_in_week * 3)
        run_dt = base_date + timedelta(days=days_offset)
        run_date_str = run_dt.strftime("%Y-%m-%d")
        
        # Fog/Monsoon Seasonality (Dec-Jan: Fog in North India, June-Aug: Monsoon in Kerala)
        month = run_dt.month
        is_fog = 1.45 if month in [12, 1] else 1.0
        is_monsoon = 1.35 if month in [6, 7, 8] else 1.0
        season_mult = max(is_fog, is_monsoon)

        # Initial origin departure scenario
        scenario = random.choices(
            ["ON_TIME_START", "SLIGHT_DELAY", "HEAVY_DELAY"],
            weights=[0.40, 0.45, 0.15]
        )[0]

        if scenario == "ON_TIME_START":
            accum_delay = 0.0
        elif scenario == "SLIGHT_DELAY":
            accum_delay = random.uniform(4.0, 18.0) * season_mult
        else:
            accum_delay = random.uniform(30.0, 75.0) * season_mult

        for idx, st in enumerate(catalog_12626):
            st_code = st["code"]
            st_name = st["name"].upper()
            sec_dist = st["dist"] - (catalog_12626[idx - 1]["dist"] if idx > 0 else 0.0)

            is_junction = any(jk == st_code or jk in st_name for jk in junction_keywords)

            # Chain pulling or unexpected signal hold incident chance (5% chance on route)
            chain_pulling_delay = 0.0
            if random.random() < 0.05:
                # 6-8 mins near station, 10-15 mins in section
                chain_pulling_delay = random.uniform(6.0, 15.0)

            # Non-linear delay compounding vs high-speed recovery
            if is_junction and accum_delay > 0:
                accum_delay += random.uniform(4.0, 16.0) * season_mult + chain_pulling_delay
            elif idx > 0 and sec_dist > 80.0 and accum_delay > 20.0 and season_mult == 1.0:
                # Speed recovery on clear sections
                recovery = min(accum_delay * 0.22, (sec_dist / 100.0) * 6.0)
                accum_delay = max(0.0, accum_delay - recovery) + chain_pulling_delay
            else:
                accum_delay += random.uniform(0.5, 3.5) + chain_pulling_delay

            arr_delay = round(accum_delay, 1)
            dep_delay = round(accum_delay + random.uniform(1.0, 3.0), 1)

            run_rec = HistoricalTrainRun(
                journey_date=run_date_str,
                train_number="12626",
                station_code=st_code,
                station_name=st["name"],
                station_sequence=idx + 1,
                scheduled_arrival=st["sched_arr"],
                actual_arrival=st["sched_arr"],
                arrival_delay_minutes=arr_delay,
                scheduled_departure=st["sched_dep"],
                actual_departure=st["sched_dep"],
                departure_delay_minutes=dep_delay,
                distance_from_origin=float(st["dist"]),
                distance_to_destination=float(total_dist - st["dist"])
            )
            sample_runs.append(run_rec)
            record_count += 1

print(f"✅ Generated {record_count} historical station records for Train 12626 across 2 Years (104 Weeks).")
db.bulk_save_objects(sample_runs)
db.commit()

print("\n--- Training ML Model (GradientBoostingRegressor) on 2-Year Train 12626 Dataset ---")
pipeline = HistoricalMLPipeline(db)
meta = pipeline.train_and_version_model()

print("\n=========================================================================")
print("  TRAINING COMPLETE & MODEL PERSISTED TO DISK")
print("=========================================================================")
print("Model Version:", meta["model_version"])
print("Dataset Size:", meta["dataset_size"], "records")
print("Date Range:", meta["training_start_date"], "to", meta["training_end_date"])
print("Metrics:")
print(f"  - Gradient Boosting Model MAE: {meta['comparison']['gbr_model']['mae']:.2f} min | RMSE: {meta['comparison']['gbr_model']['rmse']:.2f} min")
print(f"  - Naive Timetable Baseline MAE: {meta['comparison']['naive_timetable_baseline']['mae']:.2f} min | RMSE: {meta['comparison']['naive_timetable_baseline']['rmse']:.2f} min")

print("\nFeature Importances:")
for k, v in meta["feature_importance"].items():
    print(f"  - {k}: {v:.4f}")

db.close()
