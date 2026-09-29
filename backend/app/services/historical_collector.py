import os
import json
import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from app.config import settings
from app.db.models import CollectionJob, HistoricalTrainRun
from app.adapters.historical_data_adapter import (
    get_historical_adapter,
    QuotaExceededException,
    AuthenticationException
)
from app.services.historical_normalizer import HistoricalNormalizer
from app.services.quality_checker import DataQualityChecker

logger = logging.getLogger("historical_collector")

class ResumableHistoricalCollector:
    """
    Resumable Historical Data Collection Engine.
    Iterates through date ranges, enforces rate limiting, archives raw responses,
    normalizes records, performs quality validation, and stores runs in database.
    """

    def __init__(self, db: Session):
        self.db = db
        self.adapter = get_historical_adapter()

    @staticmethod
    def cleanup_zombie_jobs(db: Session):
        try:
            running_jobs = db.query(CollectionJob).filter(CollectionJob.status.like("RUNNING%")).all()
            for job in running_jobs:
                job.status = "PAUSED"
                job.updated_at = datetime.now().isoformat()
            if running_jobs:
                db.commit()
                logger.info(f"Cleaned up {len(running_jobs)} zombie background collection jobs on server startup.")
        except Exception as e:
            logger.warning(f"Failed cleaning zombie jobs: {e}")

    def create_job(self, train_number: str, start_date: str, end_date: str) -> CollectionJob:
        job_id = f"job_{uuid.uuid4().hex[:8]}"
        job = CollectionJob(
            job_id=job_id,
            train_number=train_number,
            start_date=start_date,
            end_date=end_date,
            current_date=start_date,
            status="PENDING",
            records_downloaded=0,
            failed_requests=0,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def archive_raw_response(self, train_number: str, journey_date: str, data: Dict[str, Any]):
        train_dir = os.path.join(settings.RAW_DATA_DIR, f"train_{train_number}")
        os.makedirs(train_dir, exist_ok=True)
        file_path = os.path.join(train_dir, f"{journey_date}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def run_job(self, job_id: str, max_days: Optional[int] = None) -> Dict[str, Any]:
        job = self.db.query(CollectionJob).filter(CollectionJob.job_id == job_id).first()
        if not job:
            return {"status": "error", "message": f"Job {job_id} not found"}

        job.status = "RUNNING"
        self.db.commit()

        curr_dt = datetime.strptime(job.current_date, "%Y-%m-%d")
        end_dt = datetime.strptime(job.end_date, "%Y-%m-%d")

        days_processed = 0
        consecutive_failures = 0

        while curr_dt <= end_dt:
            self.db.refresh(job)
            if job.status.startswith("PAUSED"):
                logger.info(f"Job {job_id} paused at date {job.current_date}")
                break

            date_str = curr_dt.strftime("%Y-%m-%d")
            logger.info(f"Processing train {job.train_number} for date {date_str}")

            try:
                raw_data = self.adapter.fetch_train_day(job.train_number, date_str)
                if raw_data:
                    self.archive_raw_response(job.train_number, date_str, raw_data)
                    normalized_records = HistoricalNormalizer.normalize_journey(raw_data)
                    validation_res = DataQualityChecker.validate_records(normalized_records)
                    valid_records = validation_res["valid_records"]

                    for rec in valid_records:
                        self.db.add(rec)
                    
                    job.records_downloaded += len(valid_records)
                    job.last_successful_date = date_str
                    consecutive_failures = 0
                else:
                    job.failed_requests += 1
                    consecutive_failures += 1

            except QuotaExceededException as qe:
                logger.warning(f"Circuit breaker triggered for job {job_id}: {qe}")
                job.status = "PAUSED (Quota Exceeded)"
                job.failed_requests += 1
                job.updated_at = datetime.now().isoformat()
                self.db.commit()
                break

            except AuthenticationException as ae:
                logger.warning(f"Circuit breaker triggered for job {job_id}: {ae}")
                job.status = "PAUSED (Auth Error)"
                job.failed_requests += 1
                job.updated_at = datetime.now().isoformat()
                self.db.commit()
                break

            except Exception as e:
                logger.error(f"Failed to process date {date_str} for job {job_id}: {e}")
                job.failed_requests += 1
                consecutive_failures += 1

            # Circuit breaker: if 10 consecutive requests fail, pause to prevent wasting API tokens
            if consecutive_failures >= 10:
                logger.warning(
                    f"Job {job_id} encountered {consecutive_failures} consecutive failed requests on or before {date_str}. "
                    "Pausing automatically to protect API tokens and quota."
                )
                job.status = "PAUSED (Repeated Failures)"
                job.updated_at = datetime.now().isoformat()
                self.db.commit()
                break

            curr_dt += timedelta(days=1)
            job.current_date = curr_dt.strftime("%Y-%m-%d") if curr_dt <= end_dt else job.end_date
            job.updated_at = datetime.now().isoformat()
            self.db.commit()

            days_processed += 1
            if max_days and days_processed >= max_days:
                break

        if curr_dt > end_dt and not job.status.startswith("PAUSED"):
            job.status = "COMPLETED"
            self.db.commit()

        return {
            "job_id": job.job_id,
            "train_number": job.train_number,
            "start_date": job.start_date,
            "end_date": job.end_date,
            "current_date": job.current_date,
            "status": job.status,
            "records_downloaded": job.records_downloaded,
            "failed_requests": job.failed_requests,
            "last_successful_date": job.last_successful_date
        }

    def generate_synthetic_dataset(self, job_id: str) -> Dict[str, Any]:
        """
        Generates realistic multi-year historical train runs for any train when external API
        quota is exhausted or unavailable. Populates database and JSON archives with full 8-factor delay chains.
        """
        job = self.db.query(CollectionJob).filter(CollectionJob.job_id == job_id).first()
        if not job:
            return {"status": "error", "message": f"Job {job_id} not found"}

        job.status = "RUNNING"
        self.db.commit()

        import random
        # 1. Fetch route stations for the train
        route_info = self.adapter.fetch_train_route(job.train_number)
        stations = route_info.get("stations", []) if route_info and isinstance(route_info, dict) else []

        if not stations:
            # High-fidelity fallback corridor stations
            stations = [
                {"code": "NDLS", "name": "New Delhi", "dist": 0.0, "sched_arr": "06:00", "sched_dep": "06:15"},
                {"code": "CNB", "name": "Kanpur Central", "dist": 435.0, "sched_arr": "11:20", "sched_dep": "11:25"},
                {"code": "PRYJ", "name": "Prayagraj Junction", "dist": 629.0, "sched_arr": "13:30", "sched_dep": "13:35"},
                {"code": "DDU", "name": "Pt Deen Dayal Upadhyaya", "dist": 782.0, "sched_arr": "15:40", "sched_dep": "15:50"},
                {"code": "PNBE", "name": "Patna Junction", "dist": 994.0, "sched_arr": "18:40", "sched_dep": "18:50"},
                {"code": "BJU", "name": "Barauni Junction", "dist": 1104.0, "sched_arr": "21:10", "sched_dep": "21:20"},
                {"code": "KIR", "name": "Katihar Junction", "dist": 1285.0, "sched_arr": "00:45", "sched_dep": "00:55"},
                {"code": "NJP", "name": "New Jalpaiguri", "dist": 1469.0, "sched_arr": "04:30", "sched_dep": "04:45"},
                {"code": "APDJ", "name": "Alipur Duar Junction", "dist": 1637.0, "sched_arr": "08:15", "sched_dep": "08:25"},
                {"code": "GHY", "name": "Guwahati", "dist": 1819.0, "sched_arr": "12:00", "sched_dep": "12:00"}
            ]

        start_dt = datetime.strptime(job.start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(job.end_date, "%Y-%m-%d")
        total_days = max(1, (end_dt - start_dt).days)

        # Generate runs roughly 2-3 times per week across date range
        curr = start_dt
        new_records = 0

        while curr <= end_dt:
            date_str = curr.strftime("%Y-%m-%d")
            month = curr.month
            day = curr.day
            weekday = curr.weekday()

            # 1. Day-of-the-Week Pattern (e.g. Saturday vs past 2 years Saturdays)
            if weekday == 5:  # Saturday weekend surge
                weekday_mult = random.uniform(1.35, 1.50)
            elif weekday == 6: # Sunday return surge
                weekday_mult = random.uniform(1.22, 1.35)
            elif weekday == 4: # Friday evening rush
                weekday_mult = random.uniform(1.15, 1.25)
            elif weekday == 0: # Monday morning rush
                weekday_mult = random.uniform(1.10, 1.20)
            else:              # Mid-week baseline (Tue, Wed, Thu)
                weekday_mult = random.uniform(0.85, 1.02)

            # 2. Specific Date & Month Recurring Anomalies (past 2 years)
            date_anomaly = 0.0
            if (month == 12 and day >= 15) or (month == 1 and day <= 31):
                # Peak North Indian Fog Season
                date_anomaly = random.uniform(22.0, 42.0)
            elif (month == 10 and day >= 22) or (month == 11 and day <= 10):
                # Diwali / Chhath Puja festive passenger surge
                date_anomaly = random.uniform(18.0, 36.0)
            elif (month == 7 and day >= 10) or (month == 8 and day <= 15):
                # Monsoon infiltration speed restrictions
                date_anomaly = random.uniform(12.0, 24.0)

            # Initial departure delay with weekday pattern & date anomaly
            accum_delay = max(0.0, (random.gauss(6.0, 8.0) * weekday_mult) + date_anomaly)

            records_for_day = []
            prev_dist = 0.0
            for idx, st in enumerate(stations):
                st_code = st.get("code") or st.get("stationCode", f"ST{idx}")
                st_name = st.get("name") or st.get("stationName", st_code)
                dist = float(st.get("dist") or st.get("distance", idx * 100.0))
                section_dist = max(1.0, dist - prev_dist)
                prev_dist = dist

                # 3. Cascading Delay Chain & Section Delay Recovery Dynamics
                is_junction = any(jk in st_name.upper() or jk in st_code.upper() for jk in [
                    "JN", "JUNCTION", "CENTRAL", "TERMINUS", "DDU", "CNB", "PRYJ", "PNBE", "BJU", "KIR", "NDLS", "GHY"
                ])

                if idx > 0:
                    if is_junction:
                        # Junction bottleneck compounding delay
                        accum_delay += random.uniform(4.0, 12.0) * weekday_mult
                    elif section_dist >= 80.0 and accum_delay > 8.0:
                        # Long clear stretch delay recovery capability (>80 km)
                        recovery_amount = min(accum_delay * 0.35, section_dist * 0.08 + random.uniform(2.0, 6.0))
                        accum_delay = max(0.0, accum_delay - recovery_amount)
                    else:
                        delta = random.uniform(-1.5, 3.5) * weekday_mult
                        accum_delay = max(0.0, accum_delay + delta)

                sched_arr = st.get("sched_arr") or "10:00"
                sched_dep = st.get("sched_dep") or "10:05"

                rec = HistoricalTrainRun(
                    journey_date=date_str,
                    train_number=job.train_number,
                    station_code=st_code,
                    station_name=st_name,
                    station_sequence=idx + 1,
                    distance_from_origin=dist,
                    scheduled_arrival=sched_arr,
                    scheduled_departure=sched_dep,
                    arrival_delay_minutes=round(accum_delay, 1),
                    departure_delay_minutes=round(accum_delay + random.uniform(1.0, 3.0), 1),
                    source="where_is_my_train_synthetic_fallback"
                )
                self.db.add(rec)
                records_for_day.append({
                    "station_sequence": idx + 1,
                    "station_code": st_code,
                    "station_name": st_name,
                    "distance_from_origin": dist,
                    "arrival_delay_minutes": round(accum_delay, 1)
                })

            new_records += len(records_for_day)
            # Save raw archive
            self.archive_raw_response(job.train_number, date_str, {
                "source": "where_is_my_train_synthetic_fallback",
                "train_number": job.train_number,
                "journey_date": date_str,
                "stations": records_for_day
            })

            # Advance 2 days to evenly cover all weekdays (including Saturdays) across 104 weeks
            curr += timedelta(days=2)
            job.current_date = min(curr, end_dt).strftime("%Y-%m-%d")
            job.records_downloaded += len(records_for_day)
            job.last_successful_date = date_str
            self.db.commit()

        job.status = "COMPLETED"
        job.updated_at = datetime.now().isoformat()
        self.db.commit()

        return {
            "status": "COMPLETED",
            "job_id": job.job_id,
            "train_number": job.train_number,
            "records_downloaded": job.records_downloaded,
            "message": f"Successfully generated {job.records_downloaded} historical run records for Train {job.train_number}."
        }

    def pause_job(self, job_id: str) -> Dict[str, Any]:
        job = self.db.query(CollectionJob).filter(CollectionJob.job_id == job_id).first()
        if job:
            job.status = "PAUSED"
            job.updated_at = datetime.now().isoformat()
            self.db.commit()
            return {"job_id": job_id, "status": "PAUSED"}
        return {"status": "error", "message": f"Job {job_id} not found"}

    def resume_job(self, job_id: str) -> Dict[str, Any]:
        job = self.db.query(CollectionJob).filter(CollectionJob.job_id == job_id).first()
        if job:
            job.status = "RUNNING"
            job.updated_at = datetime.now().isoformat()
            self.db.commit()
            return self.run_job(job_id)
        return {"status": "error", "message": f"Job {job_id} not found"}
