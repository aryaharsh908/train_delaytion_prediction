import pandas as pd
import numpy as np
from datetime import datetime

class FeatureEngineer:
    """
    Transforms historical and real-time train running data into feature arrays for ML training/prediction.
    """
    TYPE_MAP = {"RAJDHANI": 1, "SHATABDI": 2, "SUPERFAST": 3, "EXPRESS": 4, "LOCAL": 5}
    
    @classmethod
    def extract_features(cls, df: pd.DataFrame) -> pd.DataFrame:
        X = pd.DataFrame()
        X["train_priority"] = df["train_priority"].fillna(3)
        X["train_type_code"] = df["train_type"].map(cls.TYPE_MAP).fillna(3)
        X["day_of_week"] = df["day_of_week"].fillna(0)
        X["is_fog_season"] = df["is_fog_season"].fillna(0)
        X["distance_from_origin"] = df["distance_from_origin"].fillna(0)
        X["route_sequence"] = df["route_sequence"].fillna(0)
        X["arrival_delay"] = df["arrival_delay"].fillna(0)
        X["sched_section_travel_min"] = df["sched_section_travel_min"].fillna(15.0)
        X["station_seq"] = df["route_sequence"].fillna(0)
        return X

    @classmethod
    def extract_single_feature_vector(cls, train_priority: int, train_type: str, day_of_week: int,
                                     is_fog_season: int, distance_from_origin: float,
                                     route_sequence: int, arrival_delay: float,
                                     sched_section_travel_min: float,
                                     delay_delta_vs_previous: float = 0.0,
                                     weekday_median: float = None,
                                     weather_penalty: float = 0.0,
                                     current_time: datetime = None) -> np.ndarray:
        if current_time is None:
            current_time = datetime.now()
            
        type_code = cls.TYPE_MAP.get(train_type, 3)
        vec = np.array([[
            float(route_sequence),                       # station_sequence
            float(distance_from_origin),                  # distance_from_origin
            max(0.0, 1385.0 - float(distance_from_origin)), # distance_to_destination
            float(arrival_delay),                         # arrival_delay_minutes
            float(arrival_delay + 2.0),                   # departure_delay_minutes
            float(current_time.weekday()),                           # day_of_week
            float(current_time.month),                                          # month
            float(current_time.hour),                                         # time_of_day_hour
            float(sched_section_travel_min),              # section_historical_median_time
            1.5,                                          # section_historical_std_dev
            float(delay_delta_vs_previous),               # delay_delta_vs_previous
            float(weekday_median if weekday_median is not None else sched_section_travel_min), # weekday_historical_median
            float(weather_penalty)                        # weather_penalty
        ]])
        return vec

