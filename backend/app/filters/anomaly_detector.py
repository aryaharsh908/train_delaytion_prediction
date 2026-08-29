import numpy as np
from typing import Dict, Any

class AnomalyDetector:
    """
    Statistical Z-Score & Outlier Anomaly Detector.
    Identifies abnormal section travel delays or station dwell delays.
    """
    def __init__(self, z_threshold: float = 2.5):
        self.z_threshold = z_threshold
        # Baseline section stats (mean_min, std_min)
        self.baseline_stats = {
            "NDLS-MTJ": (70.0, 8.0),
            "MTJ-AGC": (30.0, 4.0),
            "AGC-GWL": (70.0, 9.0),
            "GWL-VGLJ": (55.0, 7.0),
            "VGLJ-BINA": (90.0, 10.0),
            "BINA-BPL": (80.0, 9.0)
        }

    def check_section_anomaly(self, section_id: str, actual_travel_time_min: float) -> Dict[str, Any]:
        mean_t, std_t = self.baseline_stats.get(section_id, (45.0, 6.0))
        z_score = (actual_travel_time_min - mean_t) / std_t if std_t > 0 else 0.0
        
        is_anomalous = z_score >= self.z_threshold
        
        return {
            "section_id": section_id,
            "actual_time_min": actual_travel_time_min,
            "historical_mean_min": mean_t,
            "z_score": round(float(z_score), 2),
            "is_anomaly": is_anomalous,
            "anomaly_level": "CRITICAL" if z_score > 4.0 else ("HIGH" if z_score > 2.5 else "NORMAL")
        }
