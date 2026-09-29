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
        from app.ml.temporal_graph_model import TemporalGraphNN
        from app.ml.temporal_pattern_engine import TemporalPatternEngine
        self.tgnn = TemporalGraphNN()
        self.temporal_engine = TemporalPatternEngine()
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
        online_section_stats: dict = None,
        station_code: str = "SEC",
        next_station_code: Optional[str] = None,
        journey_date: Optional[str] = None
    ) -> float:
        """
        Predict section travel time using loaded ML model with 2-year same-weekday pattern,
        specific date anomaly, and chain recovery tracking.
        """
        effective_median = sched_section_travel_min
        if online_section_stats and "median" in online_section_stats:
            effective_median = online_section_stats["median"]

        # Dynamically fetch live weather (A5 fix)
        from app.adapters.weather_adapter import MockWeatherAdapter
        weather = MockWeatherAdapter().get_weather_for_section(f"SECTION_{route_sequence}")
        live_weather_penalty = weather.get("speed_penalty_pct", 0.0) * 15.0

        # 1. Same-weekday historical baseline (e.g. Saturday vs past 2 years Saturdays)
        same_wd_delay, _ = self.temporal_engine.get_same_weekday_delay(
            station_code, route_sequence, int(day_of_week), default_median=effective_median
        )

        # 2. Specific calendar date anomaly
        dt_val = None
        if journey_date:
            from datetime import datetime
            for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%d-%m-%Y"):
                try:
                    dt_val = datetime.strptime(str(journey_date)[:10], fmt)
                    break
                except Exception:
                    pass
        if dt_val is None:
            from datetime import datetime
            dt_val = datetime.now()
        calendar_anomaly = self.temporal_engine.get_calendar_date_anomaly(station_code, route_sequence, dt_val)

        # 3. Cascading delay chain recovery capability
        rec_capacity, _ = self.temporal_engine.get_section_delay_recovery_capability(
            station_code, next_station_code, distance_km=80.0
        )

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
            weekday_median=same_wd_delay,
            calendar_date_anomaly=calendar_anomaly,
            chain_delay_recovery_rate=rec_capacity,
            weather_penalty=live_weather_penalty
        )

        if self.model is not None:
            try:
                base_pred = float(self.model.predict(vec)[0])
                delta_delay = max(-5.0, base_pred - arrival_delay)
                section_travel = effective_median + delta_delay
                if calendar_anomaly > 0:
                    section_travel += min(15.0, calendar_anomaly * 0.25)
                if rec_capacity > 0 and arrival_delay > 5.0:
                    section_travel = max(effective_median * 0.85, section_travel - rec_capacity * 0.20)
                return max(effective_median * 0.85, section_travel)
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
        section_std: float = 1.5,
        delay_delta_vs_previous: float = 0.0,
        same_weekday_delay: Optional[float] = None,
        calendar_date_anomaly: Optional[float] = None,
        chain_recovery_rate: Optional[float] = None,
        station_code: Optional[str] = None,
        next_station_code: Optional[str] = None,
        journey_date: Optional[str] = None
    ) -> Tuple[float, float, float, float, float]:
        """
        Predict P10, P50, P90 quantile delays using trained quantile regression models
        with 2-year same-weekday pattern (e.g. Saturday vs past 2 years Saturdays),
        specific calendar date anomaly recognition, and cascading chain recovery dynamics.
        Returns: (p10_delay, p50_delay, p90_delay, confidence_score, crps_score)
        """
        from app.adapters.weather_adapter import MockWeatherAdapter
        from datetime import datetime
        
        weather = MockWeatherAdapter().get_weather_for_section(f"SECTION_{station_sequence}")
        live_weather_penalty = weather.get("speed_penalty_pct", 0.0) * 15.0

        st_code = station_code or "SEC"

        # 1. Extract same-weekday historical delay (e.g. Saturday vs past 2-year Saturdays)
        if same_weekday_delay is None:
            same_weekday_delay, _ = self.temporal_engine.get_same_weekday_delay(
                st_code, station_sequence, int(day_of_week), default_median=section_median
            )

        # 2. Extract calendar date anomaly (specific month & day)
        if calendar_date_anomaly is None:
            dt_val = None
            if journey_date:
                for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%d-%m-%Y"):
                    try:
                        dt_val = datetime.strptime(str(journey_date)[:10], fmt)
                        break
                    except Exception:
                        pass
            if dt_val is None:
                now_dt = datetime.now()
                try:
                    dt_val = now_dt.replace(month=int(month))
                except Exception:
                    dt_val = now_dt
            calendar_date_anomaly = self.temporal_engine.get_calendar_date_anomaly(st_code, station_sequence, dt_val)

        # 3. Extract section delay recovery capability
        if chain_recovery_rate is None:
            chain_recovery_rate, _ = self.temporal_engine.get_section_delay_recovery_capability(
                st_code, next_station_code, distance_km=80.0
            )
        
        # Build the complete 15-feature contract vector
        vec = np.array([[
            float(station_sequence),
            float(distance_from_origin),
            max(0.0, float(total_distance) - float(distance_from_origin)),
            float(current_delay_min),
            float(current_delay_min + 2.0),
            float(day_of_week),
            float(month),
            float(hour),
            float(section_median),
            float(section_std),
            float(delay_delta_vs_previous),
            float(same_weekday_delay),
            float(calendar_date_anomaly),
            float(chain_recovery_rate),
            float(live_weather_penalty)
        ]])

        p50_del = current_delay_min

        # P50: main model prediction
        if self.model is not None:
            try:
                p50_del = max(0.0, float(self.model.predict(vec)[0]))
            except Exception:
                pass

        # P10: real quantile model prediction
        if self.model_p10 is not None:
            try:
                p10_del = max(0.0, float(self.model_p10.predict(vec)[0]))
            except Exception:
                p10_del = max(0.0, p50_del * 0.7)
        else:
            p10_del = max(0.0, p50_del * 0.7)

        # P90: real quantile model prediction
        if self.model_p90 is not None:
            try:
                p90_del = max(0.0, float(self.model_p90.predict(vec)[0]))
            except Exception:
                p90_del = p50_del * 1.4
        else:
            p90_del = p50_del * 1.4

        # Incorporate learned 2-year calendar date anomaly into quantile forecasts
        if calendar_date_anomaly and abs(calendar_date_anomaly) > 0.0:
            p50_del = max(0.0, p50_del + calendar_date_anomaly * 0.35)
            p90_del = max(p50_del, p90_del + calendar_date_anomaly * 0.50)
            p10_del = max(0.0, p10_del + calendar_date_anomaly * 0.15)

        # Incorporate section delay recovery dynamics (train actively recovers time on clear stretch)
        if chain_recovery_rate and chain_recovery_rate > 0.0 and current_delay_min > 5.0:
            recovery_delta = min(chain_recovery_rate * 0.35, current_delay_min * 0.25)
            p10_del = max(0.0, p10_del - recovery_delta * 1.2)
            p50_del = max(0.0, p50_del - recovery_delta)
            p90_del = max(p50_del, p90_del - recovery_delta * 0.5)

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
