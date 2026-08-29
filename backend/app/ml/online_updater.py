import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from collections import deque
import logging

logger = logging.getLogger("online_updater")

class HardExampleReplayBuffer:
    """
    Replay Buffer for Hard Machine Learning Examples.
    Stores historical observations where prediction error |y - y_hat| exceeds error_threshold (10.0 min).
    Re-injects hard samples into training batches during 1-click UI model retraining.
    """
    def __init__(self, max_capacity: int = 500, error_threshold: float = 10.0):
        self.max_capacity = max_capacity
        self.error_threshold = error_threshold
        self.buffer: deque = deque(maxlen=max_capacity)

    def add_example(self, feature_vec: List[float], y_true: float, y_pred: float, meta: Dict[str, Any]):
        abs_err = abs(y_true - y_pred)
        if abs_err >= self.error_threshold:
            self.buffer.append({
                "feature_vec": feature_vec,
                "y_true": float(y_true),
                "y_pred": float(y_pred),
                "error": float(abs_err),
                "meta": meta
            })
            logger.info(f"Hard example added to Replay Buffer! Error: {abs_err:.1f} min | Section/Station: {meta.get('station_code')}")

    def get_all_samples(self) -> Tuple[List[List[float]], List[float]]:
        X_hard = [item["feature_vec"] for item in self.buffer]
        y_hard = [item["y_true"] for item in self.buffer]
        return X_hard, y_hard

    def __len__(self) -> int:
        return len(self.buffer)


class OnlineSectionUpdater:
    """
    Lightweight Online Section Parameter Updater.
    Maintains a sliding window (N=50) of real-time section running observations per railway section.
    Adapts section median travel time & standard deviation within minutes of sudden speed drops or TSRs.
    """
    def __init__(self, window_size: int = 50):
        self.window_size = window_size
        self.section_buffers: Dict[str, deque] = {}
        self.replay_buffer = HardExampleReplayBuffer()

    def record_section_run(
        self,
        section_id: str,
        actual_running_time_min: float,
        feature_vec: Optional[List[float]] = None,
        predicted_time_min: Optional[float] = None,
        meta: Optional[Dict[str, Any]] = None
    ):
        """Records a new section run observation and updates rolling section distribution."""
        if section_id not in self.section_buffers:
            self.section_buffers[section_id] = deque(maxlen=self.window_size)

        self.section_buffers[section_id].append(float(actual_running_time_min))

        if feature_vec is not None and predicted_time_min is not None:
            self.replay_buffer.add_example(
                feature_vec=feature_vec,
                y_true=actual_running_time_min,
                y_pred=predicted_time_min,
                meta=meta or {"section_id": section_id}
            )

    def get_online_section_stats(self, section_id: str, default_median: float = 15.0, default_std: float = 2.0) -> Tuple[float, float]:
        """
        Calculates online median running time and standard deviation for a given section.
        Returns: (online_median_min, online_std_dev_min)
        """
        buf = self.section_buffers.get(section_id)
        if not buf or len(buf) < 3:
            return float(default_median), float(default_std)

        obs = np.array(list(buf), dtype=np.float32)
        med = float(np.median(obs))
        std = float(np.std(obs))
        return max(1.0, med), max(0.5, std)

    def get_all_section_stats(self) -> Dict[str, Dict[str, float]]:
        """Returns online section stats for all active sections."""
        stats = {}
        for sec_id, buf in self.section_buffers.items():
            if buf:
                obs = np.array(list(buf), dtype=np.float32)
                stats[sec_id] = {
                    "count": len(buf),
                    "median": round(float(np.median(obs)), 2),
                    "std": round(float(np.std(obs)), 2)
                }
        return stats
