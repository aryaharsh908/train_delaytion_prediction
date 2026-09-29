import csv
import json
import io
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session

from app.config import settings, reload_settings, save_api_key
from app.db.database import get_db
from app.db.models import CollectionJob, HistoricalTrainRun
from app.adapters.historical_data_adapter import WhereIsMyTrainHistoricalAdapter, get_historical_adapter
from app.services.historical_collector import ResumableHistoricalCollector
from app.services.historical_normalizer import HistoricalNormalizer
from app.services.quality_checker import DataQualityChecker

router = APIRouter(prefix="/data", tags=["Historical Data & Ingestion"])
logger = logging.getLogger("historical_api")

class UpdateApiKeyRequest(BaseModel):
    api_key: str

@router.get("/source/status")
def get_source_status():
    """Returns provider credentials status, rate limiting rules, and authentication state."""
    cfg = reload_settings()
    adapter = get_historical_adapter()
    if isinstance(adapter, WhereIsMyTrainHistoricalAdapter):
        st = adapter.test_connection()
        # Add masked key info for frontend display
        raw_key = cfg.WHERE_IS_MY_TRAIN_API_KEY
        masked_key = f"{raw_key[:7]}...{raw_key[-4:]}" if len(raw_key) > 12 else (raw_key[:4] + "..." if raw_key else "Not Configured")
        st["active_api_key_masked"] = masked_key
        st["has_api_key"] = bool(raw_key)
        return st
    return {
        "provider": "Where Is My Train (Mock Historical Adapter)",
        "configured": False,
        "authenticated": True,
        "last_successful_request": None,
        "rate_limit_status": "60 req/min (Mock Mode)",
        "historical_access": "available_synthetic_fallback",
        "has_api_key": False
    }

@router.post("/source/test")
def test_source_connection():
    """Performs ONE safe test request to verify official endpoint connection without bulk downloading."""
    reload_settings()
    adapter = get_historical_adapter()
    if isinstance(adapter, WhereIsMyTrainHistoricalAdapter):
        return adapter.test_connection()
    return {
        "provider": "Where Is My Train (Mock Mode)",
        "status": "success",
        "message": "Mock adapter active. Provide WHERE_IS_MY_TRAIN_API_KEY in .env to connect to live RailRadar endpoints."
    }

@router.post("/source/update-key")
def update_api_key(req: UpdateApiKeyRequest):
    """Updates the RailRadar API key dynamically, saves to .env, and retests connection."""
    clean_key = req.api_key.strip()
    if not clean_key:
        raise HTTPException(status_code=400, detail="API key cannot be empty")
    
    # Save to disk and reload in memory
    save_api_key(clean_key)
    adapter = get_historical_adapter()
    test_res = adapter.test_connection()
    
    return {
        "message": "API key successfully updated and saved.",
        "connection_test": test_res
    }

@router.post("/collect/start")
def start_collection(
    train_number: str,
    start_date: str = "2024-01-01",
    end_date: str = "2026-01-01",
    use_synthetic: bool = False,
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """Initiates a resumable historical data collection job. Requires explicit user action."""
    collector = ResumableHistoricalCollector(db)
    job = collector.create_job(train_number, start_date, end_date)
    
    if use_synthetic:
        # Run synthetic multi-year generation
        res = collector.generate_synthetic_dataset(job.job_id)
        return {
            "message": f"Synthetic historical dataset generation completed for Train {train_number}.",
            "job": res
        }
    
    # Run initial batch synchronously and queue remaining background downloading
    res = collector.run_job(job.job_id, max_days=5)
    if background_tasks and res.get("status") == "RUNNING":
        background_tasks.add_task(collector.run_job, job.job_id)
    return {
        "message": f"Historical data collection job {job.job_id} started for train {train_number}.",
        "job": res
    }

@router.post("/collect/synthetic")
def generate_synthetic_historical(
    train_number: str,
    start_date: str = "2024-01-01",
    end_date: str = "2026-01-01",
    db: Session = Depends(get_db)
):
    """Generates multi-year authentic historical runs when API quota is exhausted or for local training."""
    collector = ResumableHistoricalCollector(db)
    job = collector.create_job(train_number, start_date, end_date)
    res = collector.generate_synthetic_dataset(job.job_id)
    return {
        "message": f"Successfully generated synthetic multi-year dataset for train {train_number}.",
        "job": res
    }

@router.post("/collect/pause/{job_id}")
def pause_collection(job_id: str, db: Session = Depends(get_db)):
    collector = ResumableHistoricalCollector(db)
    return collector.pause_job(job_id)

@router.post("/collect/resume/{job_id}")
def resume_collection(job_id: str, db: Session = Depends(get_db)):
    collector = ResumableHistoricalCollector(db)
    return collector.resume_job(job_id)

@router.get("/jobs")
def list_jobs(db: Session = Depends(get_db)):
    jobs = db.query(CollectionJob).order_by(CollectionJob.created_at.desc()).all()
    return jobs

@router.get("/stats")
def get_dataset_stats(db: Session = Depends(get_db)):
    total_records = db.query(HistoricalTrainRun).count()
    trains_count = db.query(HistoricalTrainRun.train_number).distinct().count()
    stations_count = db.query(HistoricalTrainRun.station_code).distinct().count()
    
    earliest = db.query(HistoricalTrainRun.journey_date).order_by(HistoricalTrainRun.journey_date.asc()).first()
    latest = db.query(HistoricalTrainRun.journey_date).order_by(HistoricalTrainRun.journey_date.desc()).first()
    
    job_count = db.query(CollectionJob).count()

    return {
        "total_historical_records": total_records,
        "total_trains": trains_count,
        "total_stations": stations_count,
        "total_collection_jobs": job_count,
        "date_range": {
            "start_date": earliest[0] if earliest else "N/A",
            "end_date": latest[0] if latest else "N/A"
        },
        "last_sync": latest[0] if latest else None
    }

@router.post("/import/json")
async def import_json_dump(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Imports offline JSON historical data dump through normalization and quality validation pipeline."""
    content = await file.read()
    try:
        data = json.loads(content.decode("utf-8"))
        if isinstance(data, list):
            all_records = []
            for item in data:
                all_records.extend(HistoricalNormalizer.normalize_journey(item))
        else:
            all_records = HistoricalNormalizer.normalize_journey(data)

        val_res = DataQualityChecker.validate_records(all_records)
        valid = val_res["valid_records"]

        for rec in valid:
            db.add(rec)
        db.commit()

        return {
            "message": f"Successfully imported JSON dump.",
            "total_records_parsed": len(all_records),
            "valid_records_stored": len(valid),
            "invalid_count": val_res["invalid_count"],
            "reasons_breakdown": val_res["reasons_breakdown"]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process JSON dump: {e}")

@router.post("/import/csv")
async def import_csv_dump(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Imports offline CSV historical data dump through normalization and quality validation pipeline."""
    content = await file.read()
    try:
        decoded = content.decode("utf-8")
        reader = csv.DictReader(io.StringIO(decoded))
        records = []
        for row in reader:
            train_num = row.get("train_number") or row.get("train_no") or ""
            journey_date = row.get("journey_date", "2024-01-01")
            rec = HistoricalNormalizer.normalize_station_record(train_num, journey_date, row, source="csv_import")
            records.append(rec)

        val_res = DataQualityChecker.validate_records(records)
        valid = val_res["valid_records"]

        for rec in valid:
            db.add(rec)
        db.commit()

        return {
            "message": f"Successfully imported CSV dump.",
            "total_records_parsed": len(records),
            "valid_records_stored": len(valid),
            "invalid_count": val_res["invalid_count"],
            "reasons_breakdown": val_res["reasons_breakdown"]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process CSV dump: {e}")
