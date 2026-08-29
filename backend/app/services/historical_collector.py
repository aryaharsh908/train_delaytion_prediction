import os
import json
import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from app.config import settings
from app.db.models import CollectionJob, HistoricalTrainRun
from app.adapters.historical_data_adapter import get_historical_adapter
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
            running_jobs = db.query(CollectionJob).filter(CollectionJob.status == "RUNNING").all()
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

        while curr_dt <= end_dt:
            self.db.refresh(job)
            if job.status == "PAUSED":
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
                else:
                    job.failed_requests += 1

            except Exception as e:
                logger.error(f"Failed to process date {date_str} for job {job_id}: {e}")
                job.failed_requests += 1

            curr_dt += timedelta(days=1)
            job.current_date = curr_dt.strftime("%Y-%m-%d") if curr_dt <= end_dt else job.end_date
            job.updated_at = datetime.now().isoformat()
            self.db.commit()

            days_processed += 1
            if max_days and days_processed >= max_days:
                break

        if curr_dt > end_dt:
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
