import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from app.graph.railway_graph import RailwayNetworkGraph
from app.ml.predictor import ETAPredictor
from app.ml.online_updater import OnlineSectionUpdater
from app.filters.kalman_filter import TrainTelemetryFilter
from app.filters.changepoint_detector import CUSUMChangePointDetector
from app.filters.anomaly_detector import AnomalyDetector
from app.propagation.delay_propagator import DelayPropagationEngine, CascadingDelayEngine
from app.monte_carlo.simulator import MonteCarloETASimulator
from app.explainability.explainer import ETAExplainer
from app.simulation.rtis_simulator import RTISSimulator
from app.simulation.coa_simulator import COASimulator
from app.simulation.event_simulator import IncidentEventSimulator
from app.schemas.schemas import ETAPredictionSchema, TrainStateSchema, SimulationStateSchema


logger = logging.getLogger("simulation_orchestrator")
from app.adapters.historical_data_adapter import get_historical_adapter


class SimulationOrchestrator:

    """
    Central Simulation & Dynamic ETA Orchestrator.
    Manages active trains, processes real-time telemetry, runs Kalman filtering, change-point & anomaly detection,
    evaluates network delay propagation, executes Monte Carlo simulations, and computes explainable ETAs.
    """
    def __init__(self):
        self.is_running = True
        self.speed_multiplier = 1.0  # Strict 1:1 real-time requested
        self.current_sim_time = datetime.now()
        
        # Engines
        self.graph = RailwayNetworkGraph()
        self.predictor = ETAPredictor()
        self.eta_predictor = self.predictor
        self.online_updater = OnlineSectionUpdater()
        self.kalman = TrainTelemetryFilter()
        self.changepoint_detectors = {}
        self.anomaly_detector = AnomalyDetector()
        self.propagator = DelayPropagationEngine(self.graph)
        self.monte_carlo = MonteCarloETASimulator(num_samples=100)
        
        # Simulators
        self.rtis_sim = RTISSimulator(self.graph)
        self.coa_sim = COASimulator()
        self.incident_sim = IncidentEventSimulator()
        
        # Smoothed Delay Cache for ETA Stabilization (EMA filter)
        self.smoothed_delays: Dict[str, float] = {}
        self.auto_incidents_enabled: bool = False
        self.tick_count: int = 0
        
        # Active state
        self.active_trains: Dict[str, Dict[str, Any]] = {}
        self._seen_train_numbers: set = set()
        self._initialize_default_trains()
        
        # Demo Step Tracker
        self.demo_step = 0

    def _initialize_default_trains(self):
        """Initializes corridor trains from authentic DB records; additional trains populate dynamically upon user input."""
        self.active_trains = {}
        try:
            from app.analytics.corridor_conflict_engine import CorridorConflictEngine
            engine = CorridorConflictEngine(self)
            initial_records = engine._get_active_train_records()
            for r in initial_records:
                self.active_trains[r["train_id"]] = r
                if r["train_id"] not in self.changepoint_detectors:
                    try:
                        self.changepoint_detectors[r["train_id"]] = CUSUMChangePointDetector()
                    except Exception:
                        pass
        except Exception as e:
            logger.warning(f"Could not hydrate initial corridor trains: {e}")


    def get_current_timestamp(self) -> str:
        return self.current_sim_time.strftime("%H:%M:%S") + " IST"

    def tick_simulation(self, delta_real_seconds: float = 1.0):
        """Advances the simulation by 1:1 strict real time."""
        if not self.is_running:
            return

        # STRESS-TEST FIX: Lock simulator clock strictly to real-time IST clock
        self.current_sim_time = datetime.now()
        sim_delta_seconds = delta_real_seconds * self.speed_multiplier
        self.kalman.set_speed_multiplier(self.speed_multiplier)

        # 1. Evaluate network delay propagation
        prop_delays = self.propagator.compute_network_propagation(self.active_trains)

        # 2. Advance train telemetry
        for t_id, train in self.active_trains.items():
            try:
                if train.get("status") == "ARRIVED":
                    continue
                    
                # Apply Kalman Filter to raw position/speed
                filt_lat, filt_lng, filt_speed = self.kalman.filter_telemetry(
                    t_id, train["lat"], train["lng"], train["speed_kmh"]
                )
                train["filtered_lat"] = filt_lat
                train["filtered_lng"] = filt_lng
                train["filtered_speed"] = filt_speed

                # Record telemetry run in online section updater
                curr_sec = train.get("current_section_id", "NDLS-MTJ")
                running_time = max(1.0, (train.get("section_progress_km", 1.0) / max(10.0, train.get("speed_kmh", 80.0))) * 60.0)
                self.online_updater.record_section_run(
                    section_id=curr_sec,
                    actual_running_time_min=running_time,
                    meta={"train_id": t_id, "speed": train["speed_kmh"]}
                )

                # Advance train position along section
                train = self.rtis_sim.step_train_movement(train, sim_delta_seconds)
                
                # Check Change-Point Detection on speed drop
                if t_id not in self.changepoint_detectors:
                    self.changepoint_detectors[t_id] = CUSUMChangePointDetector()
                cp_result = self.changepoint_detectors[t_id].add_data_point(train.get("speed_kmh", 0.0))
                if cp_result["change_detected"] and cp_result["direction"] == "SPEED_DROP":
                    self.coa_sim.log_event(
                        event_type="UNSCHEDULED_SPEED_DROP",
                        description=f"Sudden speed drop detected on {train['train_name']} ({train['speed_kmh']} km/h)",
                        train_id=t_id,
                        section_id=train["current_section_id"],
                        severity="HIGH"
                    )

                # Apply propagated delay addition
                p_delay = prop_delays.get(t_id, 0.0)
                if p_delay > 0:
                    train["current_delay_minutes"] += p_delay * 0.05  # Gradually accumulate
                    train["status"] = "SLIGHT_DELAY" if train["current_delay_minutes"] < 20 else "CRITICAL_DELAY"
            except Exception as e:
                print(f"Error ticking simulation for train {t_id}: {e}")

    def compute_dynamic_eta(self, train_id: str) -> Optional[ETAPredictionSchema]:
        clean_id = train_id.replace("TRAIN_", "").strip()
        normalized_id = f"TRAIN_{clean_id}"
        train = self.active_trains.get(train_id) or self.active_trains.get(normalized_id) or self.active_trains.get(clean_id)
        if not train:
            for t in self.active_trains.values():
                if (isinstance(t, dict) and (t.get("train_id") in (train_id, normalized_id) or t.get("train_number") == clean_id)) or \
                   (getattr(t, "train_id", None) in (train_id, normalized_id) or getattr(t, "train_number", None) == clean_id):
                    train = t
                    break
        if not train:
            self.sync_live_telemetry(clean_id)
            train = self.active_trains.get(normalized_id) or self.active_trains.get(clean_id)

        if not train:
            return None

        dest_id = train.get("destination_station_id") or (train.get("stations", [])[-1]["code"] if train.get("stations") else "DEST")
        dest_name = train.get("destination_station_name") or (train.get("stations", [])[-1]["name"] if train.get("stations") else "Destination")
        
        train_num_str = str(train.get("train_number", ""))
        dest_sched_arr_str = train.get("destination_sched_arr") or (train.get("stations", [])[-1]["sched_arr"] if train.get("stations") else "12:00")

        # Parse dest_sched_arr_str (e.g. "08:35") into actual scheduled datetime matching current IST date
        now_dt = self.current_sim_time
        try:
            sh, sm = map(int, dest_sched_arr_str.split(":"))
            base_sched_arr = now_dt.replace(hour=sh, minute=sm, second=0, microsecond=0)
            if base_sched_arr < now_dt - timedelta(hours=12):
                base_sched_arr += timedelta(days=1)
        except Exception:
            base_sched_arr = self.current_sim_time + timedelta(minutes=90)

        timetable_eta_str = base_sched_arr.strftime("%H:%M IST")

        # Get downstream sections
        last_st = train.get("last_station_id") or train.get("current_station_code") or (train.get("stations", [])[0]["code"] if train.get("stations") else "ORIG")
        curr_sec_id = train.get("current_section_id") or f"{last_st}-{dest_id}"
        downstream_sections = self.graph.get_downstream_sections(last_st, dest_id) if hasattr(self.graph, "get_downstream_sections") else [curr_sec_id]
        if not downstream_sections:
            downstream_sections = [curr_sec_id]

        # 1. Base ML predictions for section travel times
        total_ml_travel_min = 0.0
        sec_list_mc = []
        
        for idx, sec_id in enumerate(downstream_sections):
            sec_info = self.graph.sections_dict.get(sec_id, {"dist": 80.0, "mps": 110.0})
            sched_min = (sec_info["dist"] / sec_info["mps"]) * 60.0
            
            # A3: Feed live online section stats into prediction
            online_stats = None
            if hasattr(self.online_updater, 'get_online_section_stats'):
                sec_med, sec_std = self.online_updater.get_online_section_stats(sec_id)
                online_stats = {"median": sec_med, "std": sec_std}
            
            st_code = sec_id.split("-")[0] if "-" in sec_id else sec_id
            nxt_code = sec_id.split("-")[1] if "-" in sec_id else None
            ml_pred_min = self.predictor.predict_section_travel_time(
                train_priority=train.get("priority", 3),
                train_type=train.get("train_type", "EXPRESS"),
                day_of_week=self.current_sim_time.weekday(),
                is_fog_season=1 if self.current_sim_time.month in [12, 1] else 0,
                distance_from_origin=train.get("section_progress_km", 0.0),
                route_sequence=idx + 1,
                arrival_delay=train.get("current_delay_minutes", 0.0),
                sched_section_travel_min=sched_min,
                online_section_stats=online_stats,
                station_code=st_code,
                next_station_code=nxt_code,
                journey_date=self.current_sim_time.strftime("%Y-%m-%d")
            )
            total_ml_travel_min += ml_pred_min
            sec_list_mc.append({"section_id": sec_id, "scheduled_travel_min": sched_min})

        ml_eta_dt = now_dt + timedelta(minutes=total_ml_travel_min)
        
        # Sanity Clamp: ML ETA shouldn't blindly drift 13 hours off-schedule due to additive errors.
        # Max bound: timetable + (3x current delay) + 120 minutes buffer
        curr_delay_for_clamp = train.get("current_delay_minutes", 0.0)
        max_logical_eta = base_sched_arr + timedelta(minutes=(curr_delay_for_clamp * 3) + 120)
        min_logical_eta = base_sched_arr - timedelta(minutes=30)
        
        if ml_eta_dt > max_logical_eta or ml_eta_dt < min_logical_eta:
            print(f"[WARNING] Train {train_id} ML ETA wildly drifted ({ml_eta_dt.strftime('%H:%M')}). Clamping to schedule bounds.")
            # Fallback to schedule-based estimate
            fallback_travel_min = sum((self.graph.sections_dict.get(sid, {}).get("dist", 80) / self.graph.sections_dict.get(sid, {}).get("mps", 110)) * 60 for sid in downstream_sections)
            ml_eta_dt = now_dt + timedelta(minutes=fallback_travel_min + curr_delay_for_clamp)

        ml_base_eta_str = ml_eta_dt.strftime("%H:%M IST")

        # 2. Dynamic Real-Time Factors with Train Priority Precedence Pattern
        curr_delay = train.get("current_delay_minutes", 0.0)
        priority = train.get("priority", 2)
        
        # Priority multipliers: Priority 1 (Rajdhani/Shatabdi) gets precedence, Priority 3 (Express) yields
        priority_mult = 0.7 if priority == 1 else (1.0 if priority == 2 else 1.5)

        # Weather impact
        weather_delay = 0.0
        sec_obj = self.graph.sections_dict.get(curr_sec_id, {})
        weather_cond = sec_obj.get("weather", "CLEAR")
        if weather_cond == "FOG":
            weather_delay = 12.0 * priority_mult
        elif weather_cond == "HEAVY_RAIN":
            weather_delay = 7.0 * priority_mult

        # Incidents impact
        incidents = self.incident_sim.get_incidents_for_section(curr_sec_id)
        if incidents:
            inc = incidents[0]
            if inc.event_type == "SIGNAL_FAILURE":
                curr_delay += 10.0 * priority_mult
            elif inc.event_type == "TRACK_FAILURE":
                curr_delay += 25.0 * priority_mult
            elif inc.event_type == "ACCIDENT":
                curr_delay += 45.0 * priority_mult

        # Junction congestion / precedence hold
        junction_delay = 0.0
        if sec_obj.get("congestion", 0.0) > 0.5:
            junction_delay = 8.0 * priority_mult

        platform_hold = 0.0
        if train.get("status") == "PLATFORM_HOLD":
            platform_hold = 5.0

        # Recovery calculation (high priority trains recover lost time faster)
        recovery = 0.0
        if priority == 1 and curr_delay > 10.0 and weather_delay == 0:
            recovery = min(curr_delay * 0.35, 10.0)

        # Raw Total Delay
        raw_total_delay = max(0.0, curr_delay + weather_delay + junction_delay + platform_hold - recovery)
        
        # 3. EMA Smoothing Filter to Eliminate Artificial ETA Fluctuation
        t_id = train["train_id"]
        if t_id not in self.smoothed_delays:
            self.smoothed_delays[t_id] = raw_total_delay
        else:
            # Alpha = 0.15 for rock-solid stability without random jumps
            self.smoothed_delays[t_id] = round(0.15 * raw_total_delay + 0.85 * self.smoothed_delays[t_id], 1)

        dynamic_total_delay = self.smoothed_delays[t_id]
        dynamic_eta_dt = base_sched_arr + timedelta(minutes=dynamic_total_delay)
        dynamic_forecast_eta_str = dynamic_eta_dt.strftime("%H:%M IST")

        # 4. Monte Carlo Simulation for Confidence Intervals
        mc_result = self.monte_carlo.simulate_future_eta(
            train_info=train,
            remaining_sections=sec_list_mc,
            current_delay_min=dynamic_total_delay,
            active_weather_penalty=weather_delay,
            junction_congestion_min=junction_delay
        )

        conf_80_min_dt = base_sched_arr + timedelta(minutes=mc_result["ci_80_min_delay"])
        conf_80_max_dt = base_sched_arr + timedelta(minutes=mc_result["ci_80_max_delay"])
        conf_95_min_dt = base_sched_arr + timedelta(minutes=mc_result["ci_95_min_delay"])
        conf_95_max_dt = base_sched_arr + timedelta(minutes=mc_result["ci_95_max_delay"])

        # 5. Explainability Breakdown
        factors = ETAExplainer.generate_explanation(
            current_delay_min=curr_delay,
            weather_delay_min=weather_delay,
            junction_congestion_min=junction_delay,
            platform_hold_min=platform_hold,
            recovery_min=recovery,
            weather_condition=weather_cond
        )

        p10_dt = base_sched_arr + timedelta(minutes=mc_result["ci_80_min_delay"])
        p50_dt = base_sched_arr + timedelta(minutes=dynamic_total_delay)
        p90_dt = base_sched_arr + timedelta(minutes=mc_result["ci_80_max_delay"])

        # A7: Use real CRPS score from model metadata, not hardcoded 0.85
        real_crps = getattr(self.predictor, 'crps_score', 0.0)
        real_arch = self.predictor.metadata.get('model_architecture', 'HYBRID_TGNN_GBDT') if hasattr(self.predictor, 'metadata') else 'HYBRID_TGNN_GBDT'

        # A7: Compute real formatted confidence margin from MC spread
        mc_spread_min = round((mc_result['ci_80_max_delay'] - mc_result['ci_80_min_delay']) / 2.0, 0)
        mc_spread_min = max(1, int(mc_spread_min))

        return ETAPredictionSchema(
            train_id=train["train_id"],
            train_number=train["train_number"],
            target_station_id=dest_id,
            target_station_name=dest_name,
            scheduled_arrival=base_sched_arr.strftime("%H:%M IST"),
            timetable_baseline_eta=timetable_eta_str,
            ml_base_eta=ml_base_eta_str,
            dynamic_forecast_eta=dynamic_forecast_eta_str,
            eta_p10=p10_dt.strftime("%H:%M IST"),
            eta_p50=p50_dt.strftime("%H:%M IST"),
            eta_p90=p90_dt.strftime("%H:%M IST"),
            confidence_score=round(max(60.0, min(99.0, 100.0 - (dynamic_total_delay * 0.3))), 1),
            crps_score=real_crps,
            model_architecture=real_arch,
            formatted_confidence_eta=f"{dynamic_forecast_eta_str} ± {mc_spread_min} min",
            total_predicted_delay_minutes=round(dynamic_total_delay, 1),
            confidence_80_min=conf_80_min_dt.strftime("%H:%M"),
            confidence_80_max=conf_80_max_dt.strftime("%H:%M"),
            confidence_95_min=conf_95_min_dt.strftime("%H:%M"),
            confidence_95_max=conf_95_max_dt.strftime("%H:%M"),
            on_time_probability=mc_result["on_time_probability"],
            explainability_factors=factors,
            monte_carlo_samples=mc_result.get("samples", []),
            last_updated=datetime.now().strftime("%H:%M:%S IST")
        )






    def trigger_sih_demo_step(self) -> Dict[str, Any]:
        """
        Executes the step-by-step SIH Predefined Demonstration Scenario.
        Visually demonstrates dynamic ETA recalculation across sequential events:
        Initial 22:41 -> Signal Hold (+10m) -> Fog Entry (+9m) -> Precedence Hold (+7m) -> Clearance (-5m) -> Final ETA
        """
        self.demo_step += 1
        train = next(iter(self.active_trains.values()), None)
        if not train:
            self.demo_step = 0
            return {"demo_step": 0, "description": "No active train. Please search and track a train first."}

        t_id = train["train_id"]
        t_name = train.get("train_name", "Train")
        t_sec = train.get("current_section_id", "MAIN")
        t_next = train.get("next_station_id", "NEXT")

        desc = ""
        if self.demo_step == 1:
            desc = f"STEP 1: Initial State. {t_name} running on schedule."
            train["current_delay_minutes"] = 0.0
            train["status"] = "ON_TIME"
        elif self.demo_step == 2:
            desc = f"STEP 2: Signal Halt Injected. {t_name} stopped at signal outside {t_next}. Delay +10m."
            train["current_delay_minutes"] = 10.0
            train["speed_kmh"] = 0.0
            train["status"] = "SIGNAL_HALT"
            self.coa_sim.log_event("SIGNAL_HALT", f"Signal halt outside {t_next} for track clearance (+10m)", t_id, t_next, severity="HIGH")
        elif self.demo_step == 3:
            desc = f"STEP 3: Fog Zone Entry. En-route section {t_sec} affected by dense fog. Speed restricted to 45 km/h (+9m penalty)."
            train["current_delay_minutes"] = 19.0
            train["status"] = "INCIDENT_AFFECTED"
            self.graph.update_section_state(t_sec, weather="FOG")
            self.incident_sim.inject_incident("FOG", t_sec, severity="HIGH", visibility_m=180.0)
            self.coa_sim.log_event("WEATHER_ALERT", f"Dense fog reported on section {t_sec}. MPS reduced to 45 km/h", t_id, section_id=t_sec, severity="HIGH")
        elif self.demo_step == 4:
            desc = f"STEP 4: Junction Precedence Hold. Preceding freight train holding junction (+7m delay propagation)."
            train["current_delay_minutes"] = 26.0
            train["status"] = "CRITICAL_DELAY"
            self.graph.update_section_state(t_sec, congestion=0.8)
            self.coa_sim.log_event("PRECEDENCE", f"Junction route conflict. Held for crossing train (+7m)", t_id, station_id=t_next, severity="HIGH")
        elif self.demo_step == 5:
            desc = f"STEP 5: Fog Clears & High-Speed Recovery. Weather cleared. High priority run recovers 5 mins."
            train["current_delay_minutes"] = 21.0
            train["speed_kmh"] = 110.0
            train["status"] = "SLIGHT_DELAY"
            self.graph.update_section_state(t_sec, weather="CLEAR", congestion=0.0)
            self.incident_sim.clear_all_incidents()
            self.coa_sim.log_event("WEATHER_CLEARED", f"Track clear for high speed running on {t_sec}", t_id, section_id=t_sec, severity="LOW")
        else:
            self.demo_step = 0
            return self.trigger_sih_demo_step()

        eta_schema = self.compute_dynamic_eta(t_id)
        return {
            "demo_step": self.demo_step,
            "description": desc,
            "train_state": train,
            "updated_eta": eta_schema.dict() if eta_schema else None
        }

    def _build_delay_reasons_for_section(self, section_id: str, train_dict: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        A7: Builds explainable delay_reasons from active incidents, weather, and congestion
        on the given section. Returns list of ETABreakdownFactor-compatible dicts.
        """
        reasons = []
        
        # Check active incidents on this section
        incidents = self.incident_sim.get_incidents_for_section(section_id)
        for inc in incidents:
            impact_map = {
                "SIGNAL_FAILURE": 15.0,
                "TRACK_FAILURE": 30.0,
                "ACCIDENT": 45.0,
                "FOG": 12.0,
                "HEAVY_RAIN": 8.0,
                "CHAIN_PULLING": 12.0,
                "MAINTENANCE_BLOCK": 25.0,
                "PLATFORM_OCCUPIED": 12.0,
                "JUNCTION_CONGESTION": 10.0,
            }
            impact = impact_map.get(inc.event_type, 10.0)
            reasons.append({
                "factor_name": inc.event_type.replace("_", " ").title(),
                "impact_minutes": impact,
                "description": f"Active {inc.event_type.lower().replace('_', ' ')} on section {section_id} (severity: {inc.severity})"
            })

        # Check weather on section
        sec_obj = self.graph.sections_dict.get(section_id, {})
        weather = sec_obj.get("weather", "CLEAR")
        if weather == "FOG":
            reasons.append({
                "factor_name": "Dense Fog",
                "impact_minutes": 12.0,
                "description": f"Fog speed restriction active on {section_id} (visibility < 200m)"
            })
        elif weather == "HEAVY_RAIN":
            reasons.append({
                "factor_name": "Heavy Monsoon Rain",
                "impact_minutes": 7.0,
                "description": f"Rain-induced speed restriction on {section_id}"
            })

        # Check congestion
        congestion = sec_obj.get("congestion", 0.0)
        if congestion > 0.5:
            reasons.append({
                "factor_name": "Junction Congestion",
                "impact_minutes": round(congestion * 10.0, 1),
                "description": f"Route conflict / precedence hold at {section_id} (congestion: {congestion:.0%})"
            })

        # Check train-specific status
        train_status = train_dict.get("status", "ON_TIME") if isinstance(train_dict, dict) else getattr(train_dict, "status", "ON_TIME")
        if train_status == "PLATFORM_HOLD":
            reasons.append({
                "factor_name": "Platform Hold",
                "impact_minutes": 5.0,
                "description": "Train held at platform awaiting route clearance"
            })
        elif train_status == "SIGNAL_HALT":
            reasons.append({
                "factor_name": "Signal Halt",
                "impact_minutes": 10.0,
                "description": "Train stopped at signal for track clearance"
            })

        # Check priority-based recovery (negative = time recovered)
        priority = train_dict.get("priority", 3) if isinstance(train_dict, dict) else getattr(train_dict, "priority", 3)
        curr_delay = train_dict.get("current_delay_minutes", 0.0) if isinstance(train_dict, dict) else getattr(train_dict, "current_delay_minutes", 0.0)
        if priority == 1 and curr_delay > 10.0 and weather == "CLEAR":
            recovery = min(curr_delay * 0.35, 10.0)
            reasons.append({
                "factor_name": "High Priority Recovery",
                "impact_minutes": -round(recovery, 1),
                "description": "Rajdhani/Shatabdi priority precedence — recovering lost time at MPS"
            })

        return reasons

    def reset_simulation(self):
        self.is_running = True
        self.demo_step = 0
        self.incident_sim.clear_all_incidents()
        self._initialize_default_trains()
        self.graph._initialize_default_corridor()

    def get_full_simulation_state(self) -> SimulationStateSchema:
        train_schemas = []
        for t_id, train in self.active_trains.items():
            eta_data = self.compute_dynamic_eta(t_id)
            train_schemas.append(TrainStateSchema(
                train_id=train.get("train_id", t_id),
                train_number=train.get("train_number", ""),
                train_name=train.get("train_name", ""),
                train_type=train.get("train_type", "EXPRESS"),
                priority=train.get("priority", 2),
                origin_station_name=train.get("origin_station_name", "Origin"),
                destination_station_name=train.get("destination_station_name", "Destination"),
                current_section_id=train.get("current_section_id", ""),
                next_station_id=train.get("next_station_id", ""),
                next_station_name=train.get("next_station_name", ""),
                latitude=float(train.get("lat") or 0.0),
                longitude=float(train.get("lng") or 0.0),
                speed_kmh=float(train.get("speed_kmh") or 0.0),
                current_delay_minutes=float(train.get("current_delay_minutes") or 0.0),
                status=train.get("status", "ON_TIME"),
                last_event_description=train.get("last_event_description", "Normal operations"),
                current_eta=eta_data
            ))

        weather_zones = []
        for sec_id, sec in self.graph.sections_dict.items():
            if sec.get("weather") != "CLEAR":
                coords = sec.get("coords", [[0, 0], [0, 0]])
                weather_zones.append({
                    "section_id": sec_id,
                    "condition": sec.get("weather"),
                    "center_lat": (coords[0][0] + coords[1][0]) / 2.0,
                    "center_lng": (coords[0][1] + coords[1][1]) / 2.0,
                    "radius_km": 30.0
                })

        return SimulationStateSchema(
            timestamp=self.get_current_timestamp(),
            is_running=self.is_running,
            speed_multiplier=self.speed_multiplier,
            active_events_count=len(self.incident_sim.active_incidents),
            trains=train_schemas,
            weather_zones=weather_zones,
            incidents=self.incident_sim.active_incidents
        )

    def trigger_background_backfill_if_unseen(self, train_number: str) -> None:
        """
        Checks if train has been seen or ingested previously.
        If unseen, starts a background worker thread to backfill historical runs
        via ResumableHistoricalCollector without blocking live API response.
        """
        clean_train_num = train_number.replace("TRAIN_", "").strip()
        if not clean_train_num or clean_train_num in self._seen_train_numbers:
            return

        self._seen_train_numbers.add(clean_train_num)

        import threading
        def _backfill_worker():
            try:
                from app.db.database import SessionLocal, engine
                from app.db.models import Base, HistoricalTrainRun, CollectionJob
                from app.services.historical_collector import ResumableHistoricalCollector
                from datetime import datetime, timedelta

                Base.metadata.create_all(bind=engine)
                db = SessionLocal()
                try:
                    existing_runs = db.query(HistoricalTrainRun).filter(HistoricalTrainRun.train_number == clean_train_num).first()
                    if existing_runs:
                        return
                    existing_job = db.query(CollectionJob).filter(CollectionJob.train_number == clean_train_num).first()
                    if existing_job and existing_job.status in ("RUNNING", "COMPLETED"):
                        return

                    logger.info(f"[ORCHESTRATOR] Starting background historical backfill for unseen train {clean_train_num}")
                    collector = ResumableHistoricalCollector(db)
                    today = datetime.now()
                    start_date = (today - timedelta(days=14)).strftime("%Y-%m-%d")
                    end_date = (today - timedelta(days=1)).strftime("%Y-%m-%d")

                    job = collector.create_job(clean_train_num, start_date, end_date)
                    collector.run_job(job.job_id)
                    logger.info(f"[ORCHESTRATOR] Completed background backfill for train {clean_train_num}")
                finally:
                    db.close()
            except Exception as e:
                logger.warning(f"[ORCHESTRATOR] Background backfill failed for train {clean_train_num}: {e}")

        thread = threading.Thread(target=_backfill_worker, daemon=True, name=f"backfill_{clean_train_num}")
        thread.start()

    def sync_live_telemetry(self, train_number: str, journey_date: Optional[str] = None) -> Optional[float]:
        """
        Synchronizes live telemetry from RailRadar / NTES API adapter.
        If train is not yet active, dynamically instantiates it with authentic stations from the API.
        Returns live delay in minutes, or None if train is not found.
        """
        try:
            clean_train_num = train_number.replace("TRAIN_", "").strip()
            normalized_id = f"TRAIN_{clean_train_num}"

            from app.adapters.historical_data_adapter import WhereIsMyTrainHistoricalAdapter
            adapter = WhereIsMyTrainHistoricalAdapter()
            live_status = adapter.fetch_live_train_status(clean_train_num, journey_date=journey_date)

            if not live_status or "delay_minutes" not in live_status:
                logger.warning(f"[ORCHESTRATOR] Train {clean_train_num} not found or no live telemetry available.")
                return None

            live_delay = float(live_status.get("delay_minutes", 0.0))
            st_val = "HEAVY_DELAY" if live_delay >= 15 else ("SLIGHT_DELAY" if live_delay >= 5 else "ON_TIME")
            cur_st_code = live_status.get("current_station_code")
            cur_st_name = live_status.get("current_station_name")
            cur_dist_km = live_status.get("current_distance_km")
            active_j_date = live_status.get("active_journey_date")
            st_delays = live_status.get("station_delays", {})
            st_dep_delays = live_status.get("station_dep_delays", {})
            st_arr_delays = live_status.get("station_arr_delays", {})
            stations = live_status.get("stations", [])

            # Dynamic Graph Registration for any new stations & section edges
            if stations and hasattr(self, "graph") and hasattr(self.graph, "register_route_stations"):
                self.graph.register_route_stations(stations)

            # Check if train already exists in active_trains
            train_found = False
            trains_list = list(self.active_trains.values()) if isinstance(self.active_trains, dict) else self.active_trains
            for t in trains_list:
                t_num = getattr(t, "train_number", None) or (t.get("train_number") if isinstance(t, dict) else None)
                t_id = getattr(t, "train_id", None) or (t.get("train_id") if isinstance(t, dict) else None)
                if t_num == clean_train_num or t_id == normalized_id:
                    train_found = True
                    if isinstance(t, dict):
                        t["current_delay_minutes"] = live_delay
                        t["status"] = st_val
                        t["station_delays"] = st_delays
                        t["station_dep_delays"] = st_dep_delays
                        t["station_arr_delays"] = st_arr_delays
                        if cur_dist_km is not None:
                            t["current_distance_km"] = cur_dist_km
                        if active_j_date:
                            t["active_journey_date"] = active_j_date
                        if stations:
                            t["stations"] = stations
                        if cur_st_code:
                            t["current_station_code"] = cur_st_code
                            t["next_station_id"] = cur_st_code
                        if cur_st_name:
                            t["current_station_name"] = cur_st_name
                            t["next_station_name"] = cur_st_name
                    else:
                        try:
                            setattr(t, "current_delay_minutes", live_delay)
                            setattr(t, "status", st_val)
                            setattr(t, "station_delays", st_delays)
                            setattr(t, "station_dep_delays", st_dep_delays)
                            setattr(t, "station_arr_delays", st_arr_delays)
                            if cur_dist_km is not None:
                                setattr(t, "current_distance_km", cur_dist_km)
                            if active_j_date:
                                setattr(t, "active_journey_date", active_j_date)
                            if cur_st_code:
                                setattr(t, "next_station_id", cur_st_code)
                            if cur_st_name:
                                setattr(t, "next_station_name", cur_st_name)
                        except Exception:
                            pass
                    break

            if not train_found:
                # Dynamically instantiate new train record from authentic API response
                origin_name = stations[0]["name"] if stations else "Origin"
                origin_code = stations[0]["code"] if stations else "ORIG"
                dest_name = stations[-1]["name"] if stations else "Destination"
                dest_code = stations[-1]["code"] if stations else "DEST"
                dest_sched_arr = stations[-1]["sched_arr"] if stations else "23:59"
                train_name = live_status.get("train_name") or f"Train {clean_train_num}"

                new_train = {
                    "train_id": normalized_id,
                    "train_number": clean_train_num,
                    "train_name": train_name,
                    "priority": 1,
                    "status": st_val,
                    "current_delay_minutes": live_delay,
                    "origin_station_id": origin_code,
                    "origin_station_name": origin_name,
                    "destination_station_id": dest_code,
                    "destination_station_name": dest_name,
                    "destination_sched_arr": dest_sched_arr,
                    "stations": stations,
                    "current_section_id": f"{stations[0]['code']}-{stations[1]['code']}" if len(stations) > 1 else f"{origin_code}-{dest_code}",
                    "last_station_id": origin_code,
                    "next_station_id": cur_st_code or (stations[1]["code"] if len(stations) > 1 else (stations[0]["code"] if stations else "ST1")),
                    "next_station_name": cur_st_name or (stations[1]["name"] if len(stations) > 1 else (stations[0]["name"] if stations else "Station")),
                    "current_distance_km": cur_dist_km,
                    "active_journey_date": active_j_date or journey_date,
                    "lat": float(stations[0].get("lat", 28.6139)) if stations and stations[0].get("lat") else 28.6139,
                    "lng": float(stations[0].get("lng", 77.2090)) if stations and stations[0].get("lng") else 77.2090,
                    "distance_into_section_km": 15.0,
                    "speed_kmh": 110.0,
                    "station_delays": st_delays,
                    "station_dep_delays": st_dep_delays,
                    "station_arr_delays": st_arr_delays,
                }
                if isinstance(self.active_trains, dict):
                    self.active_trains[normalized_id] = new_train
                elif isinstance(self.active_trains, list):
                    self.active_trains.append(new_train)

                if normalized_id not in self.changepoint_detectors:
                    try:
                        self.changepoint_detectors[normalized_id] = CUSUMChangePointDetector()
                    except Exception:
                        pass

            # Non-blocking background historical backfill trigger for unseen trains
            self.trigger_background_backfill_if_unseen(clean_train_num)

            return live_delay

        except Exception as e:
            logger.error(f"[ORCHESTRATOR] Could not sync live RTIS telemetry for train {train_number}: {e}")
            return None

    def get_train_route_timeline(self, train_id: str, journey_date: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Returns the full station-by-station route timeline for a train."""
        from datetime import datetime, timedelta
        today_str = datetime.now().strftime("%Y-%m-%d")
        effective_date = journey_date if journey_date else today_str
        
        clean_train_num = train_id.replace("TRAIN_", "") if "TRAIN_" in train_id else train_id

        is_live = False
        if effective_date == today_str:
            is_live = True
        else:
            # Check if effective_date spans into today based on authentic route
            normalized_id = f"TRAIN_{clean_train_num}"
            train_obj = self.active_trains.get(normalized_id) if isinstance(self.active_trains, dict) else None
            stations_def = train_obj.get("stations") if train_obj else None
            if not stations_def:
                from app.adapters.historical_data_adapter import WhereIsMyTrainHistoricalAdapter
                adapter = WhereIsMyTrainHistoricalAdapter()
                route_res = adapter.fetch_train_route(clean_train_num)
                stations_def = route_res.get("stations") if route_res else None

            if stations_def and len(stations_def) > 0 and stations_def[0].get("sched_dep"):
                try:
                    start_h, start_m = map(int, stations_def[0]["sched_dep"].split(":"))
                    start_dt = datetime.strptime(effective_date, "%Y-%m-%d").replace(hour=start_h, minute=start_m)
                    
                    end_dt = start_dt
                    current_abs = start_h * 60 + start_m
                    for st in stations_def[1:]:
                        if st.get("sched_arr") and ":" in st["sched_arr"]:
                            h, m = map(int, st["sched_arr"].split(":"))
                            if (h*60 + m) < current_abs:
                                end_dt += timedelta(days=1)
                            current_abs = h*60 + m
                    
                    now = datetime.now()
                    if start_dt <= now <= (end_dt + timedelta(minutes=360)): 
                        is_live = True
                except Exception:
                    pass
        
        timeline = self._get_live_route_timeline(train_id, effective_date) if is_live else self._get_historical_route_timeline(train_id, effective_date)
        if timeline:
            self.trigger_background_backfill_if_unseen(clean_train_num)
        return timeline

    def _get_live_route_timeline(self, train_id: str, journey_date: str) -> Optional[Dict[str, Any]]:
        from datetime import datetime, timedelta
        normalized_id = train_id if train_id.startswith("TRAIN_") else f"TRAIN_{train_id}"
        clean_train_num = train_id.replace("TRAIN_", "")

        # Automatically sync live telemetry
        live_telemetry_synced_delay = self.sync_live_telemetry(clean_train_num, journey_date=journey_date)

        found_train = None
        
        trains_list = list(self.active_trains.values()) if isinstance(self.active_trains, dict) else self.active_trains
        for t in trains_list:
            t_id = getattr(t, "train_id", None) or (t.get("train_id") if isinstance(t, dict) else None)
            t_num = getattr(t, "train_number", None) or (t.get("train_number") if isinstance(t, dict) else None)
            if t_id == normalized_id or t_num == clean_train_num:
                found_train = t
                break

        if not found_train:
            from app.db.database import SessionLocal
            from app.db.models import HistoricalTrainRun
            db = SessionLocal()
            try:
                db_runs = db.query(HistoricalTrainRun).filter(
                    HistoricalTrainRun.train_number == clean_train_num
                ).order_by(HistoricalTrainRun.station_sequence).all()
                if db_runs:
                    db_stations = []
                    seen_st = set()
                    for r in db_runs:
                        if r.station_code not in seen_st:
                            seen_st.add(r.station_code)
                            db_stations.append({
                                "code": r.station_code,
                                "name": r.station_name or r.station_code,
                                "dist": float(r.distance_from_origin or 0.0),
                                "sched_arr": r.scheduled_arrival or "--:--",
                                "sched_dep": r.scheduled_departure or "--:--",
                                "platform": "1",
                                "is_halt": True,
                                "status": "upcoming"
                            })
                    if db_stations:
                        new_train = {
                            "train_id": normalized_id,
                            "train_number": clean_train_num,
                            "train_name": getattr(db_runs[0], "train_name", None) or f"Train {clean_train_num}",
                            "priority": 1,
                            "status": "ON_TIME",
                            "current_delay_minutes": 0.0,
                            "origin_station_id": db_stations[0]["code"],
                            "origin_station_name": db_stations[0]["name"],
                            "destination_station_id": db_stations[-1]["code"],
                            "destination_station_name": db_stations[-1]["name"],
                            "destination_sched_arr": db_stations[-1]["sched_arr"],
                            "stations": db_stations,
                            "current_section_id": f"{db_stations[0]['code']}-{db_stations[1]['code']}" if len(db_stations) > 1 else f"{db_stations[0]['code']}-END",
                            "last_station_id": db_stations[0]["code"],
                            "next_station_id": db_stations[1]["code"] if len(db_stations) > 1 else db_stations[0]["code"],
                            "next_station_name": db_stations[1]["name"] if len(db_stations) > 1 else db_stations[0]["name"],
                            "active_journey_date": journey_date,
                            "speed_kmh": 90.0,
                            "station_delays": {},
                            "station_dep_delays": {},
                            "station_arr_delays": {},
                        }
                        if isinstance(self.active_trains, dict):
                            self.active_trains[normalized_id] = new_train
                        found_train = new_train
            finally:
                db.close()

        if not found_train:
            return None

        # Helper extract function
        def get_val(obj, key, default=None):
            if isinstance(obj, dict):
                return obj.get(key, default)
            return getattr(obj, key, default)

        train_id_val = get_val(found_train, "train_id", normalized_id)
        train_num_val = get_val(found_train, "train_number", clean_train_num)
        train_name_val = get_val(found_train, "train_name", f"Train {clean_train_num}")
        origin_val = get_val(found_train, "origin_station_name", "Origin")
        dest_val = get_val(found_train, "destination_station_name", "Destination")
        current_delay = get_val(found_train, "current_delay_minutes", live_telemetry_synced_delay if live_telemetry_synced_delay is not None else 0.0)
        next_st_id = get_val(found_train, "next_station_id", "ST1")
        next_st_name = get_val(found_train, "next_station_name", "Upcoming Station")
        st_delays_map = get_val(found_train, "station_delays", {})
        st_dep_delays_map = get_val(found_train, "station_dep_delays", {})
        st_arr_delays_map = get_val(found_train, "station_arr_delays", {})

        stations_def = get_val(found_train, "stations", None)
        if not stations_def:
            from app.adapters.historical_data_adapter import WhereIsMyTrainHistoricalAdapter
            adapter = WhereIsMyTrainHistoricalAdapter()
            route_info = adapter.fetch_train_route(clean_train_num)
            stations_def = route_info.get("stations") if route_info else None

        if not stations_def or len(stations_def) == 0:
            return None

        # Ground Truth Positioning based on Live Telemetry
        cur_dist_km = get_val(found_train, "current_distance_km")
        cur_st_code = get_val(found_train, "current_station_code")
        cur_st_name = get_val(found_train, "current_station_name", "")

        current_idx = None

        # Strategy 1: Exact track distance matching against commercial halts
        if cur_dist_km is not None and cur_dist_km > 0:
            for idx in range(len(stations_def)):
                st_dist = float(stations_def[idx].get("dist", 0.0) or 0.0)
                if st_dist >= cur_dist_km:
                    # Train is approaching or at stations_def[idx]
                    current_idx = idx
                    break
            if current_idx is None:
                current_idx = len(stations_def) - 1

        # Strategy 2: Match current station code or name against route stations
        if current_idx is None and cur_st_code:
            for idx, st in enumerate(stations_def):
                if st.get("code") == cur_st_code or (cur_st_name and cur_st_name.upper() in st.get("name", "").upper()):
                    if st.get("status") == "passed":
                        current_idx = min(len(stations_def) - 1, idx + 1)
                    else:
                        current_idx = idx
                    break

        # Strategy 3: Check last passed station from authentic station status list
        if current_idx is None:
            last_passed = -1
            for idx, st in enumerate(stations_def):
                if st.get("status") == "passed":
                    last_passed = idx
            if last_passed >= 0:
                current_idx = min(len(stations_def) - 1, last_passed + 1)

        # Strategy 4: Fallback to schedule calculation only if telemetry is absent
        if current_idx is None:
            from datetime import datetime
            now_time = datetime.now()
            start_h, start_m = map(int, stations_def[0]["sched_dep"].split(":")) if (stations_def[0].get("sched_dep") and ":" in stations_def[0]["sched_dep"]) else (0, 0)
            try:
                journey_dt = datetime.strptime(journey_date, "%Y-%m-%d")
            except Exception:
                journey_dt = now_time
            start_dt = journey_dt.replace(hour=start_h, minute=start_m)
            elapsed_mins_since_start = (now_time - start_dt).total_seconds() / 60.0
            if elapsed_mins_since_start < 0:
                elapsed_mins_since_start = 0
            real_time_idx = 0
            cumulative_mins = 0
            last_abs = start_h * 60 + start_m
            for idx, st in enumerate(stations_def):
                sched_arr_val = st.get("sched_arr", "00:00")
                arr_h, arr_m = map(int, sched_arr_val.split(":")) if ":" in sched_arr_val else (0, 0)
                curr_abs = arr_h * 60 + arr_m
                if curr_abs < last_abs:
                    cumulative_mins += (24 * 60 - last_abs + curr_abs)
                else:
                    cumulative_mins += (curr_abs - last_abs)
                last_abs = curr_abs
                if elapsed_mins_since_start >= cumulative_mins + current_delay:
                    real_time_idx = idx
                else:
                    break
            current_idx = min(len(stations_def) - 1, real_time_idx + 1)

        # Determine actual header station states
        actual_next_station = stations_def[current_idx]["name"]
        actual_prev_station = stations_def[current_idx-1]["name"] if current_idx > 0 else stations_def[0]["name"]

        route_items = []
        passed_current = False
        accumulated_ml_delay = max(0.0, current_delay)
        active_section_id = f"{stations_def[current_idx-1]['code'] if current_idx > 0 else stations_def[0]['code']}-{stations_def[current_idx]['code']}"

        # Known major junction keywords for congestion / shunting delay additions
        junction_keywords = ["JN", "JUNCTION", "CENTRAL", "TERMINUS", "CANTT", "DDU", "CNB", "PRYJ", "RTM", "BRC", "BPL", "NGP", "BPQ", "BZA", "KPD", "TVC"]

        for idx, st in enumerate(stations_def):
            st_code = st["code"]
            st_name = st["name"].upper()

            # If train is moving between prev_st and current_st, insert In-Between section item
            if idx == current_idx and current_idx > 0:
                prev_st = stations_def[idx - 1]
                st_A_name = prev_st["name"]
                st_B_name = st["name"]
                prev_d = float(prev_st.get("dist", 0.0) or 0.0)
                curr_d = float(st.get("dist", 0.0) or 0.0)
                sec_dist = max(5.0, curr_d - prev_d)

                if cur_dist_km is not None and prev_d <= cur_dist_km <= curr_d and sec_dist > 0:
                    in_between_dist = cur_dist_km
                    progress_pct = min(0.98, max(0.02, (cur_dist_km - prev_d) / sec_dist))
                else:
                    dist_into = get_val(found_train, "distance_into_section_km", 25.0)
                    progress_pct = min(0.95, max(0.05, dist_into / sec_dist))
                    in_between_dist = round(prev_d + (sec_dist * progress_pct), 1)

                speed_val = get_val(found_train, "speed_kmh", 110.0)
                
                route_items.append({
                    "station_id": f"INBETWEEN_{prev_st['code']}_{st['code']}",
                    "station_code": f"ENROUTE_{prev_st['code']}_{st['code']}",
                    "station_name": f"En Route: {st_A_name} ➔ {st_B_name}",
                    "distance_km": in_between_dist,
                    "platform_number": "TRACK",
                    "scheduled_arrival": "--:--",
                    "scheduled_departure": "--:--",
                    "forecasted_arrival": "LIVE NOW",
                    "forecasted_departure": "LIVE NOW",
                    "arrival_delay_minutes": current_delay,
                    "departure_delay_minutes": current_delay,
                    "ml_forecasted_arrival": "LIVE NOW",
                    "live_telemetry_delay_minutes": current_delay,
                    "ml_predicted_delay_minutes": current_delay,
                    "delay_difference_minutes": 0.0,
                    "status": "CURRENT",
                    "is_current_position": True,
                    "is_in_between": True,
                    "in_between_from_station": st_A_name,
                    "in_between_to_station": st_B_name,
                    "in_between_progress_pct": round(progress_pct * 100, 1),
                    "speed_kmh": speed_val,
                    "delay_reasons": self._build_delay_reasons_for_section(active_section_id, found_train)
                })
                passed_current = True
                is_current = False
                status_str = "UPCOMING"
            elif idx == current_idx and not passed_current:
                is_current = True
                status_str = "CURRENT"
                passed_current = True
            elif idx < current_idx and not passed_current:
                is_current = False
                status_str = "PASSED"
            else:
                is_current = False
                status_str = "UPCOMING"

            # Parse scheduled time
            sched_arr_str = st.get("sched_arr", "00:00")
            sched_dep_str = st.get("sched_dep", "00:00")
            arr_h, arr_m = map(int, sched_arr_str.split(":")) if ":" in sched_arr_str else (0, 0)
            dep_h, dep_m = map(int, sched_dep_str.split(":")) if ":" in sched_dep_str else (0, 0)

            # Station-specific departure delay vs arrival delay from live telemetry
            specific_arr_del = st_arr_delays_map.get(st_code, st_delays_map.get(st_code))
            specific_dep_del = st_dep_delays_map.get(st_code, st_delays_map.get(st_code))

            # Determine Live Delay for station
            if status_str in ("PASSED", "CURRENT"):
                st_live_arr_del = specific_arr_del if specific_arr_del is not None else current_delay
                st_live_dep_del = specific_dep_del if specific_dep_del is not None else st_live_arr_del
                st_live_delay = st_live_dep_del
                st_ml_delay = st_live_delay
                accumulated_ml_delay = st_live_delay
                ml_status_flag = "LIVE"
            else:
                # UPCOMING Station: Dynamic ML Delay Progression using historical station arrival delay records
                prev_st = stations_def[idx - 1] if idx > 0 else st
                is_junction = any(jk in st_name or jk in st_code for jk in junction_keywords)

                # Calculate station-to-station historical median delay delta
                total_route_km = float(stations_def[-1].get("dist", 1000.0)) if stations_def else 1000.0
                curr_km = float(stations_def[current_idx].get("dist", 0.0)) if current_idx < len(stations_def) else 0.0
                rem_km = max(1.0, total_route_km - curr_km)
                station_dist_from_curr = max(0.0, float(st.get("dist", 0.0)) - curr_km)
                
                # Compound historical bottleneck delay factor
                hist_bottleneck_factor = 1.35 if is_junction else 1.05
                hist_accumulated_delta = (station_dist_from_curr / rem_km) * 20.0 * hist_bottleneck_factor

                # Parse actual journey date for weekday pattern and calendar anomaly
                journey_dt = None
                for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%d-%m-%Y"):
                    try:
                        journey_dt = datetime.strptime(str(journey_date)[:10], fmt)
                        break
                    except Exception:
                        pass
                if journey_dt is None:
                    journey_dt = datetime.now()

                nxt_st_code = stations_def[idx + 1]["code"] if idx + 1 < len(stations_def) else None
                sched_hour_frac = float(arr_h) + (arr_m / 60.0)

                if hasattr(self, "predictor") and self.predictor is not None:
                    try:
                        _, gbr_pred, _, _, _ = self.predictor.predict_multi_quantile_delays(
                            current_delay_min=current_delay + hist_accumulated_delta,
                            station_sequence=idx + 1,
                            distance_from_origin=float(st.get("dist", 0.0)),
                            total_distance=total_route_km,
                            day_of_week=float(journey_dt.weekday()),
                            month=float(journey_dt.month),
                            hour=sched_hour_frac,
                            station_code=st_code,
                            next_station_code=nxt_st_code,
                            journey_date=journey_date
                        )
                        st_ml_delay = round(max(current_delay, gbr_pred), 1)
                        ml_status_flag = "ONLINE"
                    except Exception as e:
                        import logging
                        logging.getLogger("orchestrator").error(f"Model prediction failed: {e}")
                        st_ml_delay = round(current_delay + hist_accumulated_delta, 1)
                        ml_status_flag = "UNAVAILABLE_SCHEDULE_ESTIMATE"
                else:
                    st_ml_delay = round(current_delay + hist_accumulated_delta, 1)
                    ml_status_flag = "UNAVAILABLE_SCHEDULE_ESTIMATE"

                st_live_arr_del = current_delay
                st_live_dep_del = current_delay
                st_live_delay = current_delay

            # Format Live Telemetry forecasted arrival & departure using station-specific delays
            live_arr_m = (arr_m + int(st_live_arr_del)) % 60
            live_arr_h = (arr_h + (arr_m + int(st_live_arr_del)) // 60) % 24

            live_dep_m = (dep_m + int(st_live_dep_del)) % 60
            live_dep_h = (dep_h + (dep_m + int(st_live_dep_del)) // 60) % 24

            # Format ML Model Predicted forecasted arrival
            ml_arr_m = (arr_m + int(st_ml_delay)) % 60
            ml_arr_h = (arr_h + (arr_m + int(st_ml_delay)) // 60) % 24

            if status_str == "CURRENT":
                now_time_str = datetime.now().strftime("%H:%M IST")
                forecasted_arr_str = f"LIVE NOW ({now_time_str})"
                forecasted_dep_str = f"LIVE NOW ({now_time_str})"
                ml_forecasted_arr_str = f"LIVE NOW ({now_time_str})"
            else:
                forecasted_arr_str = f"{live_arr_h:02d}:{live_arr_m:02d}"
                forecasted_dep_str = f"{live_dep_h:02d}:{live_dep_m:02d}"
                ml_forecasted_arr_str = f"{ml_arr_h:02d}:{ml_arr_m:02d}"

            diff_delay = round(st_ml_delay - st_live_delay, 1)

            # Calculate Quantiles P10, P50, P90 using exact journey weekday & calendar date pattern
            journey_dt = None
            for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%d-%m-%Y"):
                try:
                    journey_dt = datetime.strptime(str(journey_date)[:10], fmt)
                    break
                except Exception:
                    pass
            if journey_dt is None:
                journey_dt = datetime.now()

            nxt_st = stations_def[idx + 1] if idx + 1 < len(stations_def) else None
            nxt_st_code = nxt_st["code"] if nxt_st else None
            sec_dist_to_next = max(1.0, float(nxt_st.get("dist", 0.0) or 0.0) - float(st.get("dist", 0.0) or 0.0)) if nxt_st else 80.0

            p10_del = max(0.0, st_ml_delay - 5.0)
            p50_del = st_ml_delay
            p90_del = st_ml_delay + 10.0
            if hasattr(self, "predictor") and self.predictor is not None:
                try:
                    p10_del, p50_del, p90_del, conf_score, crps_val = self.predictor.predict_multi_quantile_delays(
                        current_delay_min=st_ml_delay,
                        station_sequence=idx + 1,
                        distance_from_origin=float(st.get("dist", 0.0) or 0.0),
                        total_distance=float(stations_def[-1].get("dist", 1000.0) or 1000.0) if stations_def else 1000.0,
                        day_of_week=float(journey_dt.weekday()),
                        month=float(journey_dt.month),
                        hour=float(arr_h) + (arr_m / 60.0),
                        station_code=st_code,
                        next_station_code=nxt_st_code,
                        journey_date=journey_date
                    )
                except Exception as e:
                    pass

            p10_m = (arr_m + int(p10_del)) % 60
            p10_h = (arr_h + (arr_m + int(p10_del)) // 60) % 24

            p50_m = (arr_m + int(p50_del)) % 60
            p50_h = (arr_h + (arr_m + int(p50_del)) // 60) % 24

            p90_m = (arr_m + int(p90_del)) % 60
            p90_h = (arr_h + (arr_m + int(p90_del)) // 60) % 24

            eta_p10_str = f"{p10_h:02d}:{p10_m:02d}"
            eta_p50_str = f"{p50_h:02d}:{p50_m:02d}"
            eta_p90_str = f"{p90_h:02d}:{p90_m:02d}"
            conf_margin = round((p90_del - p10_del) / 2.0, 1)

            temporal_engine = getattr(self.predictor, "temporal_engine", None)
            same_wd_pattern = None
            date_anomaly_val = None
            recovery_cap = None
            if temporal_engine:
                try:
                    same_wd_pattern, _ = temporal_engine.get_same_weekday_delay(st_code, idx + 1, journey_dt.weekday())
                    date_anomaly_val = temporal_engine.get_calendar_date_anomaly(st_code, idx + 1, journey_dt)
                    recovery_cap, _ = temporal_engine.get_section_delay_recovery_capability(st_code, nxt_st_code, distance_km=sec_dist_to_next)
                except Exception as e:
                    pass

            route_items.append({
                "station_id": st["code"],
                "station_code": st["code"],
                "station_name": st["name"],
                "distance_km": st.get("dist", 0.0),
                "platform_number": st.get("platform", "1"),
                "scheduled_arrival": sched_arr_str,
                "scheduled_departure": sched_dep_str,
                "forecasted_arrival": forecasted_arr_str,
                "forecasted_departure": forecasted_dep_str,
                "arrival_delay_minutes": round(st_live_arr_del, 1),
                "departure_delay_minutes": round(st_live_dep_del, 1),
                "ml_forecasted_arrival": ml_forecasted_arr_str,
                "eta_p10": eta_p10_str,
                "eta_p50": eta_p50_str,
                "eta_p90": eta_p90_str,
                "confidence_margin_minutes": conf_margin,
                "live_telemetry_delay_minutes": round(st_live_dep_del, 1),
                "ml_predicted_delay_minutes": st_ml_delay,
                "delay_difference_minutes": diff_delay,
                "same_weekday_pattern_minutes": round(same_wd_pattern, 1) if same_wd_pattern is not None else None,
                "calendar_date_anomaly_minutes": round(date_anomaly_val, 1) if date_anomaly_val is not None else 0.0,
                "chain_recovery_capability_minutes": round(recovery_cap, 1) if recovery_cap is not None else 0.0,
                "status": status_str,
                "is_current_position": is_current,
                "ml_status_flag": ml_status_flag,
                "delay_reasons": self._build_delay_reasons_for_section(active_section_id, found_train) if status_str != "PASSED" else []
            })

        # Determine actual textual marker
        if current_idx >= len(stations_def) - 1:
            status_msg = f"Arrived at {dest_val} — journey completed"
        else:
            status_msg = f"Running {current_delay:.0f} min late near {actual_next_station}" if current_delay > 5 else f"Running On Time near {actual_next_station}"

        eta_prediction = self.compute_dynamic_eta(train_id_val)
        formatted_eta = eta_prediction.formatted_confidence_eta if eta_prediction else f"{current_delay:.0f} min late"

        return {
            "train_id": train_id_val,
            "train_number": train_num_val,
            "train_name": train_name_val,
            "origin_station_name": origin_val,
            "destination_station_name": dest_val,
            "current_station_name": actual_prev_station if current_idx < len(stations_def)-1 else dest_val,
            "next_station_name": actual_next_station if current_idx < len(stations_def)-1 else "-",
            "total_delay_minutes": current_delay,
            "status_message": status_msg,
            "last_updated": self.get_current_timestamp(),
            "active_journey_date": get_val(found_train, "active_journey_date", journey_date),
            "formatted_confidence_eta": formatted_eta,
            "route_items": route_items
        }

    def _get_historical_route_timeline(self, train_id: str, journey_date: str) -> Optional[Dict[str, Any]]:
        from app.db.database import SessionLocal
        from app.db.models import HistoricalTrainRun
        
        db = SessionLocal()
        try:
            clean_train_num = train_id.replace("TRAIN_", "")
            
            runs = db.query(HistoricalTrainRun).filter(
                HistoricalTrainRun.train_number == clean_train_num,
                HistoricalTrainRun.journey_date == journey_date
            ).order_by(HistoricalTrainRun.station_sequence).all()
            
            if not runs:
                # Attempt to fetch historical day from adapter
                try:
                    from app.adapters.historical_data_adapter import WhereIsMyTrainHistoricalAdapter
                    from app.services.historical_normalizer import HistoricalNormalizer
                    adapter = WhereIsMyTrainHistoricalAdapter()
                    raw_day = adapter.fetch_train_day(clean_train_num, journey_date)
                    if raw_day:
                        normalized = HistoricalNormalizer.normalize_journey(raw_day)
                        if normalized:
                            for rec in normalized:
                                db.add(rec)
                            db.commit()
                            runs = normalized
                except Exception as e:
                    logger.warning(f"Failed fetching historical day from adapter: {e}")

            if not runs:
                # Train/date has no historical records and cannot be fetched; return None (never substitute another train)
                return None
            
            origin = runs[0].station_name or runs[0].station_code
            dest = runs[-1].station_name or runs[-1].station_code

            temporal_engine = getattr(self.predictor, "temporal_engine", None)
            try:
                dt_obj = datetime.strptime(str(journey_date)[:10], "%Y-%m-%d")
                wd = dt_obj.weekday()
            except Exception:
                dt_obj = datetime.now()
                wd = dt_obj.weekday()

            route_items = []
            for idx, run in enumerate(runs):
                same_wd_pattern = None
                date_anomaly_val = None
                recovery_cap = None
                if temporal_engine:
                    nxt_code = runs[idx + 1].station_code if idx + 1 < len(runs) else None
                    sec_dist = max(1.0, float(runs[idx + 1].distance_from_origin or 0.0) - float(run.distance_from_origin or 0.0)) if idx + 1 < len(runs) else 80.0
                    same_wd_pattern, _ = temporal_engine.get_same_weekday_delay(run.station_code, idx + 1, wd)
                    date_anomaly_val = temporal_engine.get_calendar_date_anomaly(run.station_code, idx + 1, dt_obj)
                    recovery_cap, _ = temporal_engine.get_section_delay_recovery_capability(run.station_code, nxt_code, distance_km=sec_dist)

                route_items.append({
                    "station_id": run.station_code,
                    "station_code": run.station_code,
                    "station_name": run.station_name,
                    "distance_km": run.distance_from_origin or 0.0,
                    "platform_number": "1",
                    "scheduled_arrival": run.scheduled_arrival or "-",
                    "scheduled_departure": run.scheduled_departure or "-",
                    "forecasted_arrival": run.actual_arrival or "-",
                    "forecasted_departure": run.actual_departure or "-",
                    "arrival_delay_minutes": run.arrival_delay_minutes or 0.0,
                    "departure_delay_minutes": run.departure_delay_minutes or 0.0,
                    "ml_forecasted_arrival": "-",
                    "eta_p10": None,
                    "eta_p50": None,
                    "eta_p90": None,
                    "confidence_margin_minutes": None,
                    "live_telemetry_delay_minutes": run.departure_delay_minutes or 0.0,
                    "ml_predicted_delay_minutes": 0.0,
                    "delay_difference_minutes": 0.0,
                    "same_weekday_pattern_minutes": round(same_wd_pattern, 1) if same_wd_pattern is not None else None,
                    "calendar_date_anomaly_minutes": round(date_anomaly_val, 1) if date_anomaly_val is not None else 0.0,
                    "chain_recovery_capability_minutes": round(recovery_cap, 1) if recovery_cap is not None else 0.0,
                    "status": "PASSED",
                    "is_current_position": False,
                    "ml_status_flag": "HISTORICAL",
                    "delay_reasons": []
                })
                
            return {
                "train_id": train_id,
                "train_number": clean_train_num,
                "train_name": getattr(runs[0], "train_name", None) or f"Train {clean_train_num}",
                "origin_station_name": origin,
                "destination_station_name": dest,
                "current_station_name": dest,
                "next_station_name": "-",
                "total_delay_minutes": runs[-1].arrival_delay_minutes or 0.0,
                "status_message": f"Historical Journey Completed (Dest: {dest})",
                "formatted_confidence_eta": "-",
                "last_updated": self.get_current_timestamp(),
                "route_items": route_items
            }
        finally:
            db.close()

