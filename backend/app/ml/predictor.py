import os
import json
import joblib
import numpy as np
import logging
from typing import Optional, Tuple, Any

from app.config import settings
from app.ml.feature_engineering import FeatureEngineer
from app.ml.temporal_graph_model import TemporalGraphNN

logger = logging.getLogger("eta_predictor")


class ETAPredictor:
    """
    Production ETA Model Predictor.
    Loads the trained GBDT model, quantile models (P10/P90), and TGNN weights from disk.
    Provides single-section travel time prediction, multi-quantile delay prediction,
    and in-memory hot-reload after retraining.
    """
    def __init__(self):
        self.model = None
        self.model_p10 = None
        self.model_p90 = None
        self.tgnn = TemporalGraphNN()
        self.metadata: dict = {}
        self.crps_score: float = 0.0
        self.cascade_consistency_score: Optional[float] = None

    def load_or_train(self):
        """Load model from disk, or trigger training if no model exists."""
        model_loaded = False

        # Load metadata first to get active model filename (A5 fix)
        if os.path.exists(settings.METRICS_PATH):
            try:
                with open(settings.METRICS_PATH, "r", encoding="utf-8") as f:
                    self.metadata = json.load(f)
                    self.crps_score = float(self.metadata.get("metrics", {}).get("crps_score", 0.0))
                    self.cascade_consistency_score = self.metadata.get("metrics", {}).get("cascade_consistency_score")
            except Exception as e:
                logger.warning(f"Could not read metadata: {e}")

        active_filename = self.metadata.get("active_model_filename")
        if active_filename:
            active_path = os.path.join(settings.MODEL_DIR, active_filename)
            if os.path.exists(active_path):
                try:
                    self.model = joblib.load(active_path)
                    model_loaded = True
                    logger.info(f"Loaded active model: {active_filename}")
                except Exception as e:
                    logger.warning(f"Failed to load active versioned model: {e}")

        # Fallback to default MODEL_PATH
        if not model_loaded and os.path.exists(settings.MODEL_PATH):
            try:
                self.model = joblib.load(settings.MODEL_PATH)
                model_loaded = True
                logger.info(f"Loaded fallback model from {settings.MODEL_PATH}")
            except Exception as e:
                logger.warning(f"Failed to load fallback model: {e}")

        # Load quantile models (A4 fix — these were trained but never loaded before)
        p10_path = os.path.join(settings.MODEL_DIR, "active_model_p10.pkl")
        p90_path = os.path.join(settings.MODEL_DIR, "active_model_p90.pkl")
        if os.path.exists(p10_path):
            try:
                self.model_p10 = joblib.load(p10_path)
                logger.info("Loaded quantile P10 model")
            except Exception as e:
                logger.warning(f"Failed to load P10 model: {e}")
        if os.path.exists(p90_path):
            try:
                self.model_p90 = joblib.load(p90_path)
                logger.info("Loaded quantile P90 model")
            except Exception as e:
                logger.warning(f"Failed to load P90 model: {e}")

        # Load TGNN weights (A1 fix — these were trained but never loaded before)
        tgnn_path = os.path.join(settings.MODEL_DIR, "active_tgnn_weights.npz")
        if os.path.exists(tgnn_path):
            self.tgnn.load_weights(tgnn_path)
        else:
            logger.info("No persisted TGNN weights found — using initialized weights")

        if not model_loaded:
            logger.info("No trained model found. Training from historical dataset...")
            self._train_initial_model()

    def _train_initial_model(self):
        """Falls back to training pipeline when no model exists."""
        from app.db.database import SessionLocal
        from app.ml.historical_pipeline import HistoricalMLPipeline
        db = SessionLocal()
        try:
            pipeline = HistoricalMLPipeline(db)
            metadata = pipeline.train_and_version_model()
            self.metadata = metadata
            self.crps_score = float(metadata.get("metrics", {}).get("crps_score", 0.0))
            self.cascade_consistency_score = metadata.get("metrics", {}).get("cascade_consistency_score")
            self.load_or_train()
        finally:
            db.close()

    def reload(self):
        """
        Hot-reload: atomically swap in-memory model after retraining.
        Called by ml_retrain endpoint to avoid server restart.
        """
        logger.info("Hot-reloading predictor with newly trained model...")
        self.model = None
        self.model_p10 = None
        self.model_p90 = None
        self.load_or_train()
        logger.info("Predictor hot-reload complete.")

    def predict_section_travel_time(
        self,
        train_priority: int,
        train_type: str,
        day_of_week: int,
        is_fog_season: int,
        distance_from_origin: float,
        route_sequence: int,
        arrival_delay: float,
        sched_section_travel_min: float,
        online_section_stats: dict = None
    ) -> float:
        """
        Predict section travel time using loaded ML model.
        NEW (A3): Accepts optional online_section_stats to override static median.
        """
        effective_median = sched_section_travel_min
        if online_section_stats and "median" in online_section_stats:
            effective_median = online_section_stats["median"]

        
        # Dynamically fetch live weather (A5 fix)
        from app.adapters.weather_adapter import MockWeatherAdapter
        weather = MockWeatherAdapter().get_weather_for_section(f"SECTION_{route_sequence}")
        live_weather_penalty = weather.get("speed_penalty_pct", 0.0) * 15.0

        vec = FeatureEngineer.extract_single_feature_vector(
            train_priority=train_priority,
            train_type=train_type,
            day_of_week=day_of_week,
            is_fog_season=is_fog_season,
            distance_from_origin=distance_from_origin,
            route_sequence=route_sequence,
            arrival_delay=arrival_delay,
            sched_section_travel_min=effective_median,
            delay_delta_vs_previous=0.0,
            weekday_median=effective_median,
            weather_penalty=live_weather_penalty
        )

        if self.model is not None:
            try:
                return float(self.model.predict(vec)[0])
            except Exception as e:
                logger.warning(f"Model prediction error: {e}")

        return max(effective_median, effective_median + arrival_delay * 0.15)

    def predict_multi_quantile_delays(
        self,
        current_delay_min: float,
        station_sequence: int,
        distance_from_origin: float,
        total_distance: float,
        day_of_week: float,
        month: float,
        hour: float,
        section_median: float = 15.0,
        section_std: float = 1.5
    ) -> Tuple[float, float, float, float, float]:
        """
        Predict P10, P50, P90 quantile delays using trained quantile regression models.
        A4 FIX: Uses REAL trained quantile models instead of heuristic spread.
        Returns: (p10_delay, p50_delay, p90_delay, confidence_score, crps_score)
        """
        from app.adapters.weather_adapter import MockWeatherAdapter
        
        weather = MockWeatherAdapter().get_weather_for_section(f"SECTION_{station_sequence}")
        live_weather_penalty = weather.get("speed_penalty_pct", 0.0) * 15.0
        
        # Build a feature vector for the quantile models
        vec = np.array([[
            float(station_sequence),
            distance_from_origin,
            max(0.0, total_distance - distance_from_origin),
            current_delay_min,
            current_delay_min + 2.0,
            float(day_of_week),
            float(month),
            float(hour),
            float(section_median),
            float(section_std),
            0.0,  # delay_delta_vs_previous fallback
            15.0, # weekday_historical_median fallback
            float(live_weather_penalty)   # weather_penalty fallback
        ]])

        p50_del = current_delay_min

        # P50: main model prediction
        if self.model is not None:
            try:
                p50_del = max(0.0, float(self.model.predict(vec)[0]))
            except Exception:
                pass

        # P10: real quantile model prediction (A4 fix)
        if self.model_p10 is not None:
            try:
                p10_del = max(0.0, float(self.model_p10.predict(vec)[0]))
            except Exception:
                p10_del = max(0.0, p50_del * 0.7)
        else:
            # Fallback when quantile model hasn't been trained yet
            p10_del = max(0.0, p50_del * 0.7)

        # P90: real quantile model prediction (A4 fix)
        if self.model_p90 is not None:
            try:
                p90_del = max(0.0, float(self.model_p90.predict(vec)[0]))
            except Exception:
                p90_del = p50_del * 1.4
        else:
            p90_del = p50_del * 1.4

        # Ensure proper ordering: p10 <= p50 <= p90
        p10_del = min(p10_del, p50_del)
        p90_del = max(p90_del, p50_del)

        spread = max(0.1, p90_del - p10_del)
        conf = max(60.0, min(98.0, 100.0 - spread * 1.2))

        return (
            round(p10_del, 1),
            round(p50_del, 1),
            round(p90_del, 1),
            round(conf, 1),
            round(self.crps_score, 3)
        )
