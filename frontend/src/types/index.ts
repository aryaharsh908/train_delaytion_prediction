export interface Station {
  station_id: string;
  station_code: string;
  station_name: string;
  latitude: number;
  longitude: number;
  platform_count: number;
  occupied_platforms: number;
  scheduled_dwell_minutes: number;
  sequence_order: number;
}

export interface RailwaySection {
  section_id: string;
  from_station_id: string;
  to_station_id: string;
  distance_km: number;
  max_speed_kmh: number;
  current_speed_limit: number;
  track_type: string;
  is_blocked: boolean;
  active_weather_condition: string;
  active_visibility_meters: number;
  congestion_level: number;
  occupied_by_train_id?: string;
  coordinates: [number, number][];
}

export interface ETABreakdownFactor {
  factor_name: string;
  impact_minutes: number;
  description: string;
}

export interface ETAPrediction {
  train_id: string;
  train_number: string;
  target_station_id: string;
  target_station_name: string;
  scheduled_arrival: string;
  timetable_baseline_eta: string;
  ml_base_eta: string;
  dynamic_forecast_eta: string;
  eta_p10?: string;
  eta_p50?: string;
  eta_p90?: string;
  confidence_score?: number;
  crps_score?: number;
  model_architecture?: string;
  formatted_confidence_eta?: string;
  total_predicted_delay_minutes: number;
  confidence_80_min: string;
  confidence_80_max: string;
  confidence_95_min: string;
  confidence_95_max: string;
  on_time_probability: number;
  explainability_factors: ETABreakdownFactor[];
  monte_carlo_samples?: number[];
  last_updated: string;
}

export interface TrainState {
  train_id: string;
  train_number: string;
  train_name: string;
  train_type: string;
  priority: number;
  origin_station_name: string;
  destination_station_name: string;
  current_section_id: string;
  next_station_id: string;
  next_station_name: string;
  latitude: number;
  longitude: number;
  speed_kmh: number;
  current_delay_minutes: number;
  status: string;
  last_event_description: string;
  current_eta?: ETAPrediction;
}

export interface UnexpectedEvent {
  event_id: string;
  event_type: string;
  section_id: string;
  from_km: number;
  to_km: number;
  start_time: string;
  expected_end_time?: string;
  severity: string;
  visibility_meters: number;
  speed_restriction_kmh?: number;
  active: boolean;
}

export interface SimulationState {
  timestamp: string;
  is_running: boolean;
  speed_multiplier: number;
  active_events_count: number;
  trains: TrainState[];
  weather_zones: any[];
  incidents: UnexpectedEvent[];
}

export interface ModelMetrics {
  model_name: string;
  trained_at: string;
  sample_count: number;
  ml_mae: number;
  ml_rmse: number;
  ml_within_5min_pct: number;
  ml_within_10min_pct: number;
  naive_mae: number;
  naive_rmse: number;
  naive_within_5min_pct: number;
  naive_within_10min_pct: number;
  feature_importances: Record<string, number>;
  crps_score?: number;
  cascade_consistency_score?: number;
  model_architecture?: string;
}

export interface COAEvent {
  event_id: string;
  timestamp: string;
  event_type: string;
  train_id?: string;
  station_id?: string;
  section_id?: string;
  severity: string;
  expected_duration_minutes: number;
  description: string;
}

export interface StationRouteItem {
  station_id: string;
  station_code: string;
  station_name: string;
  distance_km: number;
  platform_number: string;
  scheduled_arrival: string;
  forecasted_arrival: string;
  ml_forecasted_arrival?: string;
  eta_p10?: string;
  eta_p50?: string;
  eta_p90?: string;
  confidence_margin_minutes?: number;
  live_telemetry_delay_minutes?: number;
  ml_predicted_delay_minutes?: number;
  delay_difference_minutes?: number;
  arrival_delay_minutes: number;
  scheduled_departure: string;
  forecasted_departure: string;
  departure_delay_minutes: number;
  section_recovery_minutes?: number;
  cascading_breakdown?: Record<string, number>;
  status: string;
  is_current_position: boolean;
  delay_reasons: ETABreakdownFactor[];
}

export interface TrainRouteResponse {
  train_id: string;
  train_number: string;
  train_name: string;
  origin_station_name?: string;
  destination_station_name?: string;
  current_station_name?: string;
  next_station_name?: string;
  status_message: string;
  total_delay_minutes: number;
  last_updated: string;
  formatted_confidence_eta?: string;
  route_items: StationRouteItem[];
}

export interface CounterfactualRequest {
  train_id: string;
  train_number: string;
  intervention_type: 'PRIORITY_BOOST' | 'TSR_IMPOSITION' | 'WEATHER_SPEED_DROP';
  section_id?: string;
  corridor_name?: string;
  speed_restriction_kmh?: number;
  duration_hours?: number;
  distance_km?: number;
  priority_level?: number;
}

export interface CounterfactualResponse {
  intervention_type: string;
  target_id: string;
  baseline_eta: string;
  intervention_eta: string;
  eta_p10: string;
  eta_p50: string;
  eta_p90: string;
  confidence_score: number;
  delay_change_minutes: number;
  network_passenger_minutes_added: number;
  affected_cascading_trains_count: number;
  junction_platform_conflicts: number;
  cascading_train_summaries: any[];
  route_comparison: any[];
}
