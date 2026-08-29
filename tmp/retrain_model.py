import sys
import os

sys.path.insert(0, r"c:\Users\aryah\train_schedule\backend")

from app.db.database import SessionLocal
from app.ml.historical_pipeline import HistoricalMLPipeline

db = SessionLocal()
pipeline = HistoricalMLPipeline(db)
metrics = pipeline.train_and_version_model()
db.close()

print("RETRAIN COMPLETE!")
print("Model MAE:", metrics.get("ml_mae"))
print("Model RMSE:", metrics.get("ml_rmse"))
print("Comparison metrics:", metrics.get("comparison"))
print("Feature importances:", metrics.get("feature_importances"))
