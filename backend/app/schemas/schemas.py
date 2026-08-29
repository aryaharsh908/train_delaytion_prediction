from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class StationSchema(BaseModel):
    station_id: str
    station_code: str
    station_name: str
    latitude: float
    longitude: float
    platform_count: int = 4
    occupied_platforms: int = 0
    scheduled_dwell_minutes: float = 5.0
    sequence_order: int

class RailwaySectionSchema(BaseModel):
    section_id: str
    from_station_id: str
    to_station_id: str
    distance_km: float
    max_speed_kmh: float = 110.0
    current_speed_limit: float = 110.0
    track_type: str = "DOUBLE"  # SINGLE, DOUBLE, TRIPLE
    is_blocked: bool = False
    active_weather_condition: str = "CLEAR"  # CLEAR, FOG, HEAVY_RAIN, STORM
    active_visibility_meters: float = 10000.0
    congestion_level: float = 0.0  # 0.0 to 1.0
    occupied_by_train_id: Optional[str] = None
    coordinates: List[List[float]] = []  # Polyline [[lat, lng], ...]

class RTISTelemetrySchema(BaseModel):
    timestamp: str
    train_id: str
    latitude: float
    longitude: float
    filtered_latitude: Optional[float] = None
    filtered_longitude: Optional[float] = None
    speed_kmh: float
    filtered_speed_kmh: Optional[float] = None
    heading: float = 180.0
    current_section_id: str
    distance_into_section_km: float = 0.0
    current_delay_minutes: float = 0.0

class COAEventSchema(BaseModel):
    event_id: str
    timestamp: str
    event_type: str  # SIGNAL_HALT, SIGNAL_CLEARED, PRECEDENCE, ROUTE_CONFLICT, PLATFORM_OCCUPIED, MAINTENANCE_BLOCK, etc.
    train_id: Optional[str] = None
    station_id: Optional[str] = None
    section_id: Optional[str] = None
    severity: str = "MEDIUM"  # LOW, MEDIUM, HIGH, CRITICAL
    expected_duration_minutes: float = 10.0
    description: str

class UnexpectedEventSchema(BaseModel):
    event_id: str
    event_type: str  # FOG, HEAVY_RAIN, TRACK_FAILURE, OHE_FAILURE, UNSCHEDULED_STOP, ACCIDENT
    section_id: str
    from_km: float
    to_km: float
    start_time: str
    expected_end_time: Optional[str] = None
    severity: str = "HIGH"
    visibility_meters: float = 200.0
    speed_restriction_kmh: Optional[float] = 30.0
    active: bool = True

from typing import List, Optional, Dict, Any, Union

class ETABreakdownFactor(BaseModel):
    factor_name: str
    impact_minutes: Union[float, str]  # Can be numeric (+15.0) or descriptive range ("5-15 min")
    description: str


class ETAPredictionSchema(BaseModel):
    train_id: str
    train_number: str
    target_station_id: str
    target_station_name: str
    scheduled_arrival: str
    timetable_baseline_eta: str
    ml_base_eta: str
    dynamic_forecast_eta: str
    eta_p10: Optional[str] = None
    eta_p50: Optional[str] = None
    eta_p90: Optional[str] = None
    confidence_score: Optional[float] = None
    crps_score: Optional[float] = None
    model_architecture: Optional[str] = None
    formatted_confidence_eta: str = ""  # e.g., "17:43 ± 6 min"
    total_predicted_delay_minutes: float
    confidence_80_min: str
    confidence_80_max: str
    confidence_95_min: str
    confidence_95_max: str
    on_time_probability: float  # Probability of arriving within schedule + 5 mins
    explainability_factors: List[ETABreakdownFactor]
    monte_carlo_samples: List[float] = []
    last_updated: str

class TrainStateSchema(BaseModel):
    train_id: str
    train_number: str
    train_name: str
    train_type: str  # RAJDHANI, SHATABDI, SUPERFAST, EXPRESS, LOCAL
    priority: int  # 1 (Highest) to 5
    origin_station_name: str
    destination_station_name: str
    current_section_id: str
    next_station_id: str
    next_station_name: str
    latitude: float
    longitude: float
    speed_kmh: float
    current_delay_minutes: float
    status: str  # ON_TIME, SLIGHT_DELAY, CRITICAL_DELAY, SIGNAL_HALT, INCIDENT_AFFECTED
    last_event_description: str
    current_eta: Optional[ETAPredictionSchema] = None

class SimulationStateSchema(BaseModel):
    timestamp: str
    is_running: bool
    speed_multiplier: int
    active_events_count: int
    trains: List[TrainStateSchema]
    weather_zones: List[Dict[str, Any]]
    incidents: List[UnexpectedEventSchema]

class ModelMetricsSchema(BaseModel):
    model_name: str
    trained_at: str
    sample_count: int
    ml_mae: float
    ml_rmse: float
    ml_within_5min_pct: float
    ml_within_10min_pct: float
    naive_mae: float
    naive_rmse: float
    naive_within_5min_pct: float
    naive_within_10min_pct: float
    feature_importances: Dict[str, float]
    crps_score: Optional[float] = None
    cascade_consistency_score: Optional[float] = None
    model_architecture: Optional[str] = None

class StationRouteItem(BaseModel):
    station_id: str
    station_code: str
    station_name: str
    distance_km: float
    platform_number: str
    scheduled_arrival: str
    forecasted_arrival: str
    ml_forecasted_arrival: Optional[str] = None
    eta_p10: Optional[str] = None
    eta_p50: Optional[str] = None
    eta_p90: Optional[str] = None
    confidence_margin_minutes: Optional[float] = 4.0
    live_telemetry_delay_minutes: Optional[float] = 0.0
    ml_predicted_delay_minutes: Optional[float] = 0.0
    delay_difference_minutes: Optional[float] = 0.0
    arrival_delay_minutes: float
    scheduled_departure: str
    forecasted_departure: str
    departure_delay_minutes: float
    section_recovery_minutes: float = 0.0  # Time recovered or lost in section (e.g. -4.0 for recovered, +8.0 for delay added)
    cascading_breakdown: Optional[Dict[str, float]] = None  # Factors breakdown: Initial, Wait, Signal, Platform, Slow, Freight, Crew, Junction
    status: str  # PASSED, CURRENT, UPCOMING
    is_current_position: bool = False
    delay_reasons: List[ETABreakdownFactor] = []

class TrainRouteResponse(BaseModel):
    train_id: str
    train_number: str
    train_name: str
    origin_station_name: Optional[str] = None
    destination_station_name: Optional[str] = None
    current_station_name: Optional[str] = None
    next_station_name: Optional[str] = None
    total_delay_minutes: float
    status_message: str
    last_updated: str
    formatted_confidence_eta: str = ""
    route_items: List[StationRouteItem]

class CounterfactualRequestSchema(BaseModel):
    train_id: str = "TRAIN_12951"
    train_number: str = "12951"
    intervention_type: str = "PRIORITY_BOOST"  # PRIORITY_BOOST, TSR_IMPOSITION, WEATHER_SPEED_DROP
    section_id: Optional[str] = "NDLS-MTJ"
    corridor_name: Optional[str] = "WESTERN_LINE"
    speed_restriction_kmh: Optional[float] = 30.0
    duration_hours: Optional[float] = 2.0
    distance_km: Optional[float] = 50.0
    priority_level: Optional[int] = 1

class CounterfactualResponseSchema(BaseModel):
    intervention_type: str
    target_id: str
    baseline_eta: str
    intervention_eta: str
    eta_p10: str
    eta_p50: str
    eta_p90: str
    confidence_score: float
    delay_change_minutes: float
    network_passenger_minutes_added: float
    affected_cascading_trains_count: int
    junction_platform_conflicts: int
    cascading_train_summaries: List[Dict[str, Any]] = []
    route_comparison: List[Dict[str, Any]] = []



