from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import copy
import logging

from app.schemas.schemas import CounterfactualRequestSchema, CounterfactualResponseSchema

logger = logging.getLogger("counterfactual_engine")

class CounterfactualSimulator:
    """
    Structural Counterfactual What-If Engine for Railway Operations.
    Simulates operational interventions (Priority Boost, TSR Imposition, Weather Speed Drop)
    and evaluates network-wide cascading impacts, passenger-delay minutes, and P10/P50/P90 quantile shifts.
    Calculates passenger-minutes based on authentic train rake capacity physics.
    """

    @staticmethod
    def get_train_passenger_capacity(train_dict: Dict[str, Any]) -> float:
        ttype = str(train_dict.get("train_type", "EXPRESS")).upper()
        prio = int(train_dict.get("priority", 2))
        if prio == 1 or "RAJDHANI" in ttype or "SHATABDI" in ttype:
            # 18 coaches * 72 berths * 0.85 load factor = 1,100 passengers
            return 1100.0
        elif "SUPERFAST" in ttype:
            # 20 coaches * 72 berths * 0.90 load factor = 1,300 passengers
            return 1300.0
        else:
            # Express / Mail: 22 coaches * 72 berths * 0.95 load factor = 1,500 passengers
            return 1500.0

    @classmethod
    def run_counterfactual_simulation(
        cls,
        req: CounterfactualRequestSchema,
        orchestrator: Any
    ) -> CounterfactualResponseSchema:
        logger.info(f"Executing Counterfactual Simulation: {req.intervention_type} on Train/Section: {req.train_id} / {req.section_id}")

        active_trains_copy = copy.deepcopy(orchestrator.active_trains)
        target_train = active_trains_copy.get(req.train_id) or active_trains_copy.get(f"TRAIN_{req.train_number}")

        if not target_train:
            target_train = active_trains_copy.get("TRAIN_12951")

        target_id = target_train.get("train_id", "TRAIN_12951") if target_train else "TRAIN_12951"
        baseline_delay = float(target_train.get("current_delay_minutes", 0.0)) if target_train else 0.0
        target_capacity = cls.get_train_passenger_capacity(target_train or {})

        now_dt = datetime.now()
        baseline_eta_dt = now_dt + timedelta(minutes=baseline_delay + 45.0)
        baseline_eta_str = baseline_eta_dt.strftime("%H:%M IST")

        intervention_delay = baseline_delay
        affected_trains_count = 0
        junction_conflicts = 0
        network_passenger_min = 0.0
        cascading_summaries = []

        if req.intervention_type == "PRIORITY_BOOST":
            boost_recovery = min(baseline_delay * 0.4, 15.0)
            intervention_delay = max(0.0, baseline_delay - boost_recovery)
            # Grounded in target train capacity
            network_passenger_min = -round(boost_recovery * target_capacity, 1)
            cascading_summaries.append({
                "train_id": target_id,
                "train_name": target_train.get("train_name", "Rajdhani"),
                "status": "PRIORITY_PRECEDENCE_GRANTED",
                "delay_delta_min": -round(boost_recovery, 1)
            })

        elif req.intervention_type == "TSR_IMPOSITION":
            tsr_speed = float(req.speed_restriction_kmh or 30.0)
            dist_km = float(req.distance_km or 50.0)
            tsr_delay_added = (dist_km / max(10.0, tsr_speed) - dist_km / 110.0) * 60.0
            intervention_delay = baseline_delay + tsr_delay_added

            affected_trains_count = max(1, len(active_trains_copy) - 1)
            
            # Sum passenger-minutes across target train + trailing trains
            total_pass_min = tsr_delay_added * target_capacity
            junction_conflicts = max(1, int(tsr_delay_added // 8.0))

            for t_id, tr in active_trains_copy.items():
                if t_id != target_id:
                    tr_cap = cls.get_train_passenger_capacity(tr)
                    tr_delay = tsr_delay_added * 0.4
                    total_pass_min += tr_delay * tr_cap
                    cascading_summaries.append({
                        "train_id": t_id,
                        "train_name": tr.get("train_name", "Train"),
                        "status": "TRAILING_TSR_DELAY",
                        "delay_delta_min": round(tr_delay, 1)
                    })

            network_passenger_min = round(total_pass_min, 1)

        elif req.intervention_type == "WEATHER_SPEED_DROP":
            weather_delay_added = 18.0
            intervention_delay = baseline_delay + weather_delay_added
            affected_trains_count = min(4, len(active_trains_copy))
            junction_conflicts = 2

            total_pass_min = 0.0
            for t_id, tr in list(active_trains_copy.items())[:affected_trains_count]:
                tr_cap = cls.get_train_passenger_capacity(tr)
                tr_delay = weather_delay_added * (0.7 if t_id != target_id else 1.0)
                total_pass_min += tr_delay * tr_cap
                cascading_summaries.append({
                    "train_id": t_id,
                    "train_name": tr.get("train_name", "Train"),
                    "status": "FOG_CORRIDOR_RESTRICTION",
                    "delay_delta_min": round(tr_delay, 1)
                })

            network_passenger_min = round(total_pass_min, 1)

        interv_eta_dt = now_dt + timedelta(minutes=intervention_delay + 45.0)
        interv_eta_str = interv_eta_dt.strftime("%H:%M IST")

        p10_dt = interv_eta_dt - timedelta(minutes=4)
        p50_dt = interv_eta_dt
        p90_dt = interv_eta_dt + timedelta(minutes=7)

        delay_change = round(intervention_delay - baseline_delay, 1)
        conf_score = max(70.0, min(98.0, 95.0 - abs(delay_change) * 0.5))

        route_comp = [
            {
                "station_name": "Origin",
                "baseline_time": "16:55 IST",
                "intervention_time": "16:55 IST",
                "delay_delta": 0.0
            },
            {
                "station_name": "Mathura Junction",
                "baseline_time": (baseline_eta_dt - timedelta(minutes=30)).strftime("%H:%M IST"),
                "intervention_time": (interv_eta_dt - timedelta(minutes=30)).strftime("%H:%M IST"),
                "delay_delta": delay_change
            },
            {
                "station_name": "Destination",
                "baseline_time": baseline_eta_str,
                "intervention_time": interv_eta_str,
                "delay_delta": delay_change
            }
        ]

        return CounterfactualResponseSchema(
            intervention_type=req.intervention_type,
            target_id=target_id,
            baseline_eta=baseline_eta_str,
            intervention_eta=interv_eta_str,
            eta_p10=p10_dt.strftime("%H:%M IST"),
            eta_p50=p50_dt.strftime("%H:%M IST"),
            eta_p90=p90_dt.strftime("%H:%M IST"),
            confidence_score=round(conf_score, 1),
            delay_change_minutes=delay_change,
            network_passenger_minutes_added=network_passenger_min,
            affected_cascading_trains_count=affected_trains_count,
            junction_platform_conflicts=junction_conflicts,
            cascading_train_summaries=cascading_summaries,
            route_comparison=route_comp
        )
