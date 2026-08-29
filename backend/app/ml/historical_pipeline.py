import os
import json
import joblib
import numpy as np
import logging
from datetime import datetime
from typing import Dict, Any, List, Tuple
from sqlalchemy.orm import Session
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, root_mean_squared_error

from app.config import settings
from app.db.models import HistoricalTrainRun
from app.ml.temporal_graph_model import TemporalGraphNN

logger = logging.getLogger("historical_pipeline")

class HistoricalMLPipeline:
    """
    ML Feature Engineering, Chronological Split, Training, Evaluation, and Model Versioning Pipeline.
    Preserves complete running time distributions across historical observations to capture real-world variability.
    """

    def __init__(self, db: Session):
        self.db = db

    def extract_features(self, real_only: bool = True, horizon_stations: int = 1) -> Tuple[np.ndarray, np.ndarray, List[Dict[str, Any]], List[str], Dict[str, Any]]:
        query = self.db.query(HistoricalTrainRun) if self.db is not None else None
        if query is not None and real_only:
            query = query.filter(HistoricalTrainRun.source == "where_is_my_train_railradar")
        runs = []
        if query is not None:
            runs = query.order_by(
                HistoricalTrainRun.train_number, HistoricalTrainRun.journey_date,
                HistoricalTrainRun.station_sequence
            ).all()

        if not runs:
            logger.warning("No real historical rows available.")
            return np.array([]), np.array([]), [], [], {"total_training_rows": 0, "train_numbers": [], "mock_synthetic_historical_count": 0, "real_railradar_count": 0}

        feature_names = [
            "station_sequence", "distance_from_origin", "distance_to_destination",
            "arrival_delay_minutes", "departure_delay_minutes", "day_of_week", "month",
            "time_of_day_hour", "section_historical_median_time",
            "section_historical_std_dev", "delay_delta_vs_previous", "weekday_historical_median", "weather_penalty"
        ]

        from collections import defaultdict
        journeys = {}
        for rec in runs:
            journeys.setdefault((rec.train_number, rec.journey_date), []).append(rec)
        for key in journeys:
            journeys[key].sort(key=lambda r: r.station_sequence)

        section_history = defaultdict(list)
        section_wd_history = defaultdict(list)
        for rec in runs:
            sec_key = f"{rec.station_code}_{rec.station_sequence}"
            if rec.arrival_delay_minutes is not None and rec.journey_date:
                section_history[sec_key].append((rec.journey_date, rec.arrival_delay_minutes))
                try:
                    wd = datetime.strptime(rec.journey_date, "%Y-%m-%d").weekday()
                    section_wd_history[f"{sec_key}_{wd}"].append((rec.journey_date, rec.arrival_delay_minutes))
                except: pass
        for sec_key in section_history:
            section_history[sec_key].sort(key=lambda t: t[0])
        for wd_key in section_wd_history:
            section_wd_history[wd_key].sort(key=lambda t: t[0])

        def section_stats_before(sec_key: str, journey_date: str) -> Tuple[float, float]:
            obs = [d for (dt, d) in section_history.get(sec_key, []) if dt < journey_date]
            if not obs: return 10.0, 1.5
            return float(np.median(obs)), (float(np.std(obs)) if len(obs) > 1 else 1.5)
            
        def wd_stats_before(wd_key: str, journey_date: str, sec_median: float) -> float:
            obs = [d for (dt, d) in section_wd_history.get(wd_key, []) if dt < journey_date]
            return float(np.median(obs)) if obs else sec_median

        X_rows, y_rows, meta_list = [], [], []

        from app.adapters.weather_adapter import MockWeatherAdapter
        weather_adapter = MockWeatherAdapter()

        for (train_no, journey_date), records in journeys.items():
            dt_obj = datetime.strptime(journey_date, "%Y-%m-%d")
            day_of_week = float(dt_obj.weekday())
            month = float(dt_obj.month)

            for i in range(len(records) - horizon_stations):
                cur = records[i]
                target_rec = records[i + horizon_stations]

                if cur.arrival_delay_minutes is None or target_rec.arrival_delay_minutes is None:
                    continue

                sec_key = f"{cur.station_code}_{cur.station_sequence}"
                sec_median, sec_std = section_stats_before(sec_key, journey_date)
                wd_median = wd_stats_before(f"{sec_key}_{int(day_of_week)}", journey_date, sec_median)

                sched_hour = 12.0
                if cur.scheduled_arrival:
                    try:
                        sched_hour = float(cur.scheduled_arrival.split(":")[0])
                    except: pass

                arr_del = float(cur.arrival_delay_minutes)
                dep_del = float(cur.departure_delay_minutes) if cur.departure_delay_minutes is not None else arr_del
                dist_orig = float(cur.distance_from_origin or 0.0)
                dist_dest = float(cur.distance_to_destination or 1000.0)
                
                prev_arr_del = arr_del
                if i > 0 and records[i-1].arrival_delay_minutes is not None:
                     prev_arr_del = float(records[i-1].arrival_delay_minutes)
                delay_delta = arr_del - prev_arr_del

                # Simulate weather since we didn't query weather at ingest time, just map to month
                is_fog = 1.0 if month in [12.0, 1.0] else 0.0
                
                weather_info = weather_adapter.get_weather_for_section(sec_key)
                if weather_info.get("condition") != "CLEAR":
                    weather_penalty = weather_info.get("speed_penalty_pct", 0.0)
                else:
                    weather_penalty = is_fog * 0.4
                
                X_rows.append([
                    float(cur.station_sequence), dist_orig, dist_dest, arr_del, dep_del,
                    day_of_week, month, sched_hour, sec_median, sec_std,
                    delay_delta, wd_median, weather_penalty
                ])
                y_rows.append(float(target_rec.arrival_delay_minutes))
                meta_list.append({
                    "journey_date": journey_date, "train_number": train_no,
                    "station_code": cur.station_code,
                })

        from collections import Counter
        train_counts = Counter(r.train_number for r in runs)
        provenance_stats = {
            "total_training_rows": len(runs),
            "train_numbers": list(train_counts.keys()),
            "train_row_counts": dict(train_counts),
            "mock_synthetic_historical_count": 0,
            "real_railradar_count": len(runs)
        }
        return np.array(X_rows), np.array(y_rows), meta_list, feature_names, provenance_stats

    def time_based_split(
        self, X: np.ndarray, y: np.ndarray, meta: List[Dict[str, Any]]
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        dates = [m["journey_date"] for m in meta]
        sorted_indices = np.argsort(dates)

        X_sorted = X[sorted_indices]
        y_sorted = y[sorted_indices]

        n = len(X_sorted)
        train_end = int(n * 0.60)
        val_end = int(n * 0.85)

        X_train, y_train = X_sorted[:train_end], y_sorted[:train_end]
        X_val, y_val = X_sorted[train_end:val_end], y_sorted[train_end:val_end]
        X_test, y_test = X_sorted[val_end:], y_sorted[val_end:]

        if len(X_val) == 0:
            X_val, y_val = X_train, y_train
        if len(X_test) == 0:
            X_test, y_test = X_val, y_val

        return X_train, y_train, X_val, y_val, X_test, y_test

    def train_and_version_model(self, hard_examples: Tuple = None) -> Dict[str, Any]:
        logger.info("Starting unified historical ML model training pipeline...")
        X, y, meta, feature_names, provenance = self.extract_features()
        if len(X) == 0:
            logger.error("No training data available.")
            raise ValueError("no training data — run backfill_real_historical_data.py first")
            
        X_train, y_train, X_val, y_val, X_test, y_test = self.time_based_split(X, y, meta)

        # Inject hard examples from replay buffer if available (A3)
        if hard_examples and len(hard_examples) == 2:
            X_hard, y_hard = hard_examples
            if len(X_hard) > 0 and len(y_hard) > 0:
                X_hard_arr = np.array(X_hard, dtype=np.float64)
                y_hard_arr = np.array(y_hard, dtype=np.float64)
                X_train = np.vstack([X_train, X_hard_arr])
                y_train = np.concatenate([y_train, y_hard_arr])
                logger.info(f"Injected {len(X_hard)} hard examples from replay buffer into training set.")

        # 1. Self-Supervised Physics Pretraining & TGNN Fitting
        tgnn_model = TemporalGraphNN()
        from app.ml.pretrain import SelfSupervisedPhysicsPretrainer
        pretrainer = SelfSupervisedPhysicsPretrainer()
        pretrain_metrics = pretrainer.execute_pretraining_phase(X_train, y_train, tgnn_model=tgnn_model, epochs=10)

        # 2. Train GBDT residual baseline model
        model = GradientBoostingRegressor(n_estimators=100, learning_rate=0.08, max_depth=4, random_state=42)
        model.fit(X_train, y_train)

        # 3. Train Quantile Regressors (P10, P90)
        model_p10 = GradientBoostingRegressor(loss='quantile', alpha=0.10, n_estimators=60, max_depth=3, random_state=42)
        model_p10.fit(X_train, y_train)
        
        model_p90 = GradientBoostingRegressor(loss='quantile', alpha=0.90, n_estimators=60, max_depth=3, random_state=42)
        model_p90.fit(X_train, y_train)

        # Train Linear Regression comparison model
        from sklearn.linear_model import LinearRegression
        lin_model = LinearRegression()
        lin_model.fit(X_train, y_train)

        # Evaluate GBR & Quantiles
        val_preds = model.predict(X_val)
        val_p10_preds = model_p10.predict(X_val)
        val_p90_preds = model_p90.predict(X_val)

        val_mae = float(mean_absolute_error(y_val, val_preds))
        val_rmse = float(root_mean_squared_error(y_val, val_preds))
        val_median_ae = float(np.median(np.abs(y_val - val_preds)))

        # Evaluate Hybrid TGNN + GBDT Ensemble using REAL TGNN predictions (A1 fix)
        tgnn_preds = tgnn_model.batch_predict(X_val)
        hybrid_val_preds = 0.6 * tgnn_preds + 0.4 * val_preds
        hybrid_mae = float(mean_absolute_error(y_val, hybrid_val_preds))
        hybrid_rmse = float(root_mean_squared_error(y_val, hybrid_val_preds))

        # Evaluate CRPS & Pinball Loss
        pinball_10 = float(np.mean(np.maximum(0.1 * (y_val - val_p10_preds), (0.1 - 1.0) * (y_val - val_p10_preds))))
        pinball_50 = float(np.mean(np.maximum(0.5 * (y_val - val_preds), (0.5 - 1.0) * (y_val - val_preds))))
        pinball_90 = float(np.mean(np.maximum(0.9 * (y_val - val_p90_preds), (0.9 - 1.0) * (y_val - val_p90_preds))))
        crps_score = round(float((2.0 / 3.0) * (pinball_10 + pinball_50 + pinball_90)), 3)

        # Compute real cascade consistency score based on adjacent delay updates
        lead_delay_diffs = np.diff(y_val)
        cascade_consistency = float(np.mean(lead_delay_diffs >= -0.5)) if len(lead_delay_diffs) > 0 else None

        lin_preds = lin_model.predict(X_val)
        lin_mae = float(mean_absolute_error(y_val, lin_preds))
        lin_rmse = float(root_mean_squared_error(y_val, lin_preds))

        naive_preds = X_val[:, 3]
        naive_mae = float(mean_absolute_error(y_val, naive_preds))
        naive_rmse = float(root_mean_squared_error(y_val, naive_preds))

        # Compute within-5min and within-10min accuracy percentages (C2 fix)
        ml_abs_errors = np.abs(y_val - val_preds)
        naive_abs_errors = np.abs(y_val - naive_preds)

        ml_within_5min_pct = round(float(np.mean(ml_abs_errors <= 5.0) * 100), 1)
        ml_within_10min_pct = round(float(np.mean(ml_abs_errors <= 10.0) * 100), 1)
        naive_within_5min_pct = round(float(np.mean(naive_abs_errors <= 5.0) * 100), 1)
        naive_within_10min_pct = round(float(np.mean(naive_abs_errors <= 10.0) * 100), 1)

        raw_importances = model.feature_importances_
        feature_importance_dict = {
            name: round(float(imp), 4) for name, imp in zip(feature_names, raw_importances)
        }

        os.makedirs(settings.MODEL_DIR, exist_ok=True)
        existing_models = [f for f in os.listdir(settings.MODEL_DIR) if f.startswith("eta_model_v") and f.endswith(".pkl")]
        version_num = len(existing_models) + 1
        version_str = f"v{version_num:03d}"
        model_filename = f"eta_model_{version_str}.pkl"
        model_filepath = os.path.join(settings.MODEL_DIR, model_filename)

        # Persist main model
        joblib.dump(model, model_filepath)

        # Persist quantile models (A4 fix — these were trained but never saved before)
        p10_filepath = os.path.join(settings.MODEL_DIR, f"eta_model_{version_str}_p10.pkl")
        p90_filepath = os.path.join(settings.MODEL_DIR, f"eta_model_{version_str}_p90.pkl")
        joblib.dump(model_p10, p10_filepath)
        joblib.dump(model_p90, p90_filepath)

        # Persist TGNN weights (A1 fix — weights were trained but never saved before)
        tgnn_filepath = os.path.join(settings.MODEL_DIR, f"tgnn_weights_{version_str}.npz")
        tgnn_model.save_weights(tgnn_filepath)

        # Also save "active" copies for quick loading by predictor
        joblib.dump(model_p10, os.path.join(settings.MODEL_DIR, "active_model_p10.pkl"))
        joblib.dump(model_p90, os.path.join(settings.MODEL_DIR, "active_model_p90.pkl"))
        tgnn_model.save_weights(os.path.join(settings.MODEL_DIR, "active_tgnn_weights.npz"))

        history_filepath = os.path.join(settings.MODEL_DIR, "version_history.json")
        history = []
        if os.path.exists(history_filepath):
            try:
                with open(history_filepath, "r", encoding="utf-8") as hf:
                    history = json.load(hf)
            except Exception:
                history = []

        history_entry = {
            "version": version_str,
            "filename": model_filename,
            "validation_mae": round(val_mae, 2),
            "validation_rmse": round(val_rmse, 2),
            "crps_score": crps_score,
            "created_at": datetime.now().isoformat()
        }
        history.append(history_entry)

        with open(history_filepath, "w", encoding="utf-8") as hf:
            json.dump(history, hf, indent=2)

        metadata = {
            "model_version": version_str,
            "active_model_filename": model_filename,
            "filename": model_filename,
            "training_start_date": meta[0]["journey_date"] if meta else "2024-01-01",
            "training_end_date": meta[-1]["journey_date"] if meta else "2026-01-01",
            "dataset_size": len(X),
            "features": feature_names,
            "model_architecture": "HYBRID_TGNN_GBDT",
            "metrics": {
                "validation_mae": round(val_mae, 2),
                "validation_rmse": round(val_rmse, 2),
                "median_absolute_error": round(val_median_ae, 2),
                "crps_score": crps_score,
                "cascade_consistency_score": round(cascade_consistency, 2) if cascade_consistency is not None else None,
                "pinball_loss_p10": round(pinball_10, 3),
                "pinball_loss_p50": round(pinball_50, 3),
                "pinball_loss_p90": round(pinball_90, 3),
                "ml_mae": round(val_mae, 2),
                "ml_rmse": round(val_rmse, 2),
                "ml_within_5min_pct": ml_within_5min_pct,
                "ml_within_10min_pct": ml_within_10min_pct,
                "naive_mae": round(naive_mae, 2),
                "naive_rmse": round(naive_rmse, 2),
                "naive_within_5min_pct": naive_within_5min_pct,
                "naive_within_10min_pct": naive_within_10min_pct
            },
            "pretraining_metrics": pretrain_metrics,
            "comparison": {
                "hybrid_tgnn_gbdt": {"mae": round(hybrid_mae, 2), "rmse": round(hybrid_rmse, 2)},
                "gbr_model": {"mae": round(val_mae, 2), "rmse": round(val_rmse, 2)},
                "linear_regression": {"mae": round(lin_mae, 2), "rmse": round(lin_rmse, 2)},
                "naive_timetable_baseline": {"mae": round(naive_mae, 2), "rmse": round(naive_rmse, 2)}
            },
            "feature_importance": feature_importance_dict,
            "feature_importances": feature_importance_dict,
            "version_history": history,
            "data_provenance": provenance,
            "created_at": datetime.now().isoformat(),
            "deployed": True
        }

        metadata_filepath = os.path.join(settings.MODEL_DIR, "model_metadata.json")
        with open(metadata_filepath, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        # Deploy active production model (A5 fix — also store versioned name in metadata)
        joblib.dump(model, settings.MODEL_PATH)
        logger.info(f"Unified Model {version_str} successfully trained & deployed! MAE: {val_mae:.2f}")

        return metadata
