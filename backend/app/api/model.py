import os
import json
from fastapi import APIRouter, HTTPException
from app.config import settings
from app.ml.trainer import ETAModelTrainer

router = APIRouter(prefix="/model", tags=["ML Model"])

@router.get("/metrics")
def get_model_metrics():
    if not os.path.exists(settings.METRICS_PATH):
        trainer = ETAModelTrainer()
        metrics = trainer.train_and_save()
        return metrics
        
    with open(settings.METRICS_PATH, "r") as f:
        metrics = json.load(f)
    return metrics

@router.post("/retrain")
def retrain_model():
    trainer = ETAModelTrainer()
    metrics = trainer.train_and_save()
    return {"status": "retrained", "metrics": metrics}
