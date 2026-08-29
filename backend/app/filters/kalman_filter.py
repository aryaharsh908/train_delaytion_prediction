import numpy as np

class Kalman1DFilter:
    """
    1D Kalman Filter for smoothing noisy simulated live telemetry streams (GPS lat, lng, speed).
    State equation:
    x_k = x_{k-1} + K * (z_k - x_{k-1})
    """
    def __init__(self, process_variance: float = 1e-4, measurement_variance: float = 1e-2):
        self.q = process_variance  # Process noise variance
        self.r = measurement_variance  # Measurement noise variance
        self.x = None  # Estimated state
        self.p = 1.0   # Estimation error covariance

    def update(self, measurement: float) -> float:
        if self.x is None:
            self.x = measurement
            return measurement
            
        # Time update (Predict)
        self.p = self.p + self.q
        
        # Measurement update (Correct)
        k = self.p / (self.p + self.r)
        self.x = self.x + k * (measurement - self.x)
        self.p = (1 - k) * self.p
        
        return float(self.x)


class TrainTelemetryFilter:
    """
    Combines 1D Kalman Filters for Latitude, Longitude, and Speed telemetry streams per train.
    Supports adaptive process variance scaling to prevent tracking lag at high simulation speeds.
    """
    def __init__(self):
        self.lat_filters = {}
        self.lng_filters = {}
        self.speed_filters = {}
        self.speed_multiplier = 1

    def set_speed_multiplier(self, speed_multiplier: int):
        self.speed_multiplier = max(1, speed_multiplier)
        q_scale = float(self.speed_multiplier)
        for fid in self.lat_filters:
            self.lat_filters[fid].q = 1e-5 * q_scale
            self.lng_filters[fid].q = 1e-5 * q_scale
            self.speed_filters[fid].q = 1e-1 * q_scale

    def filter_telemetry(self, train_id: str, lat: float, lng: float, speed: float) -> tuple:
        if train_id not in self.lat_filters:
            q_scale = float(max(1, self.speed_multiplier))
            self.lat_filters[train_id] = Kalman1DFilter(process_variance=1e-5 * q_scale, measurement_variance=1e-3)
            self.lng_filters[train_id] = Kalman1DFilter(process_variance=1e-5 * q_scale, measurement_variance=1e-3)
            self.speed_filters[train_id] = Kalman1DFilter(process_variance=1e-1 * q_scale, measurement_variance=2.0)
            
        filt_lat = self.lat_filters[train_id].update(lat)
        filt_lng = self.lng_filters[train_id].update(lng)
        filt_speed = self.speed_filters[train_id].update(speed)
        
        return round(filt_lat, 6), round(filt_lng, 6), round(filt_speed, 1)
