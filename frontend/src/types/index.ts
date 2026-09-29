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
  ml_status_flag?: string;
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
  active_journey_date?: string;
  formatted_confidence_eta?: string;
  route_items: StationRouteItem[];
}

export interface CounterfactualRequest {
  train_id?: string;
  train_number?: string;
  intervention_type?: string;
  injected_delay_minutes?: number;
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
  train_name?: string;
  train_number?: string;
  baseline_eta: string;
  intervention_eta: string;
  baseline_delay_minutes?: number;
  intervention_delay_minutes?: number;
  eta_p10: string;
  eta_p50: string;
  eta_p90: string;
  delay_p10?: number;
  delay_p50?: number;
  delay_p90?: number;
  confidence_score: number;
  delay_change_minutes: number;
  network_passenger_minutes_added: number;
  affected_cascading_trains_count: number;
  junction_platform_conflicts: number;
  cascading_train_summaries: any[];
  route_comparison: any[];
  corridor_risk?: string;
  escalated_risk?: string;
  total_cascaded_impact_min?: number;
  net_cascaded_escalation_min?: number;
  downstream_absorption?: any[];
}

export interface TrajectoryPoint {
  station_code: string;
  station_name: string;
  distance_km: number;
  scheduled_time_str: string;
  reactive_time_str: string;
  proactive_time_str: string;
  p10_time_str: string;
  p90_time_str: string;
  scheduled_delay_min: number;
  reactive_delay_min: number;
  proactive_delay_min: number;
  p10_delay_min: number;
  p90_delay_min: number;
  is_conflict_point: boolean;
  conflict_label?: string | null;
}

export interface TrainETAComparison {
  train_id: string;
  train_number: string;
  train_name: string;
  train_type: string;
  origin_station_name: string;
  destination_station_name: string;
  current_station_name: string;
  speed_kmh: number;
  scheduled_timetable_eta: string;
  current_reactive_estimate: string;
  current_delay_minutes: number;
  proactive_forecast_eta: string;
  proactive_delay_minutes: number;
  uncertainty_interval: string;
  eta_p10: string;
  eta_p50: string;
  eta_p90: string;
  delay_p10: number;
  delay_p50: number;
  delay_p90: number;
  forecast_confidence_pct: number;
  status_message: string;
  trajectory_band: TrajectoryPoint[];
}

export interface JunctionConflictFactorBreakdown {
  converging_traffic_density_pct: number;
  approach_track_congestion_pct: number;
  priority_clearance_precedence_pct: number;
}

export interface ApproachingService {
  train_number: string;
  train_name: string;
  train_id: string;
  sched_arr: string;
  expected_arr: string;
  delay_min: number;
}

export interface RankedJunctionConflict {
  station_code: string;
  station_name: string;
  station_id: string;
  conflict_score: number;
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH';
  approaching_trains_count: number;
  approaching_eta_min: number;
  expected_impact_window_min: string;
  impact_min_low: number;
  impact_min_high: number;
  factor_breakdown: JunctionConflictFactorBreakdown;
  affected_services: ApproachingService[];
  lat?: number;
  lng?: number;
}

export interface PropagationChainItem {
  step: number;
  type: 'SOURCE_TRAIN' | 'JUNCTION_BOTTLENECK' | 'DOWNSTREAM_SERVICE';
  title: string;
  subtitle: string;
  delay_display: string;
  delay_minutes?: number;
  induced_delay_minutes?: number;
  total_predicted_delay?: number;
  risk_badge: string;
  train_id?: string;
  train_number?: string;
  station_code?: string;
  conflict_score?: number;
}

export interface DownstreamAbsorptionRecord {
  train_number: string;
  train_name: string;
  baseline_induced_delay: string;
  simulated_induced_delay: string;
  net_escalation: string;
  net_escalation_minutes: number;
}

export interface DownstreamPropagationResponse {
  source_train_id: string;
  source_train_number: string;
  source_train_name: string;
  source_delay_minutes: number;
  critical_junction_code: string;
  critical_junction_name: string;
  critical_conflict_score: number;
  critical_risk_level: 'LOW' | 'MEDIUM' | 'HIGH';
  downstream_exposed_services_count: number;
  total_induced_network_delay_minutes: number;
  propagation_chain: PropagationChainItem[];
  downstream_absorption: DownstreamAbsorptionRecord[];
}

export interface CorridorHealthSummary {
  corridor_name: string;
  subtitle: string;
  active_trains: number;
  junctions_at_risk: number;
  bottleneck_sections: number;
  affected_services: number;
  corridor_health: number;
  corridor_health_status: string;
  system_status: string;
}
