import logging
from sqlalchemy.orm import Session
from app.ml.historical_pipeline import HistoricalMLPipeline

logger = logging.getLogger("trainer")

class ETAModelTrainer:
    """
    Unified ETAModelTrainer wrapper around HistoricalMLPipeline.
    Ensures legacy routes delegate to the single canonical training pipeline.
    """
    def __init__(self, db: Session = None):
        self.pipeline = HistoricalMLPipeline(db)

    def train_and_save(self):
        logger.info("ETAModelTrainer delegating to HistoricalMLPipeline...")
        return self.pipeline.train_and_version_model()
