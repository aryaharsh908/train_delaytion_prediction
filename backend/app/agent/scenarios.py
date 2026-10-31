"""
Disruption Scenario Generator for Delhi-Mumbai Corridor Evaluation.
Generates structured test scenarios encompassing single conflicts, cascades, platform congestion,
dense fog speed penalties, and sensor dropouts.
"""

import json
import random
import uuid
import logging
from typing import Dict, List, Any, Optional

from app.agent.harness import get_gemma_harness
from app.agent.skills import SKILLS_REGISTRY
from app.agent.guardrails import DISCLAIMER_TEXT

logger = logging.getLogger("scenario_generator")

SCENARIO_CATEGORIES = [
    "single_junction_conflict",
    "multi_train_cascade",
    "platform_congestion",
    "weather_fog_restriction",
    "sensor_dropout"
]

SAMPLE_JUNCTIONS = ["MTJ", "KOTA", "RTM", "BRC", "BSR"]
SAMPLE_TRAINS = ["12951", "12952", "12953", "12954", "12002", "12001", "22436", "22435", "12414", "12909"]


class ScenarioGenerator:
    """Generates synthetic corridor disruption benchmarks for evaluation."""

    def __init__(self):
        self.harness = get_gemma_harness()

    def generate_scenario(
        self,
        category: Optional[str] = None,
        junction_code: Optional[str] = None,
        primary_train: Optional[str] = None,
        model: str = "gemma-4-26b-a4b-it"
    ) -> Dict[str, Any]:
        cat = category or random.choice(SCENARIO_CATEGORIES)
        junc = junction_code or random.choice(SAMPLE_JUNCTIONS)
        t_pri = primary_train or random.choice(SAMPLE_TRAINS)
        t_sec = random.choice([t for t in SAMPLE_TRAINS if t != t_pri])

        scenario_id = f"SCEN_{uuid.uuid4().hex[:8].upper()}"

        # Programmatic scenario schema
        scenario = {
            "scenario_id": scenario_id,
            "category": cat,
            "junction_code": junc,
            "primary_train_id": t_pri,
            "secondary_train_ids": [t_sec],
            "title": f"{cat.replace('_', ' ').title()} at {junc}",
            "description": f"Converging headway conflict between Train {t_pri} and Train {t_sec} approaching {junc}.",
            "initial_state": {
                "train_positions": {
                    t_pri: {"station": junc, "distance_km": 14.5, "speed_kmh": 110, "delay_min": 12.0},
                    t_sec: {"station": junc, "distance_km": 18.0, "speed_kmh": 90, "delay_min": 5.0}
                },
                "weather": "FOG" if "fog" in cat else "CLEAR",
                "active_block": f"{junc}_APPROACH_UP",
                "minimum_safety_headway_min": 7.0
            },
            "disclaimer": DISCLAIMER_TEXT
        }

        if cat == "platform_congestion":
            t_third = random.choice([t for t in SAMPLE_TRAINS if t not in (t_pri, t_sec)])
            scenario["secondary_train_ids"].append(t_third)
            scenario["initial_state"]["train_positions"][t_third] = {
                "station": junc, "distance_km": 22.0, "speed_kmh": 80, "delay_min": 18.0
            }
            scenario["description"] = f"Three trains converging on two available platform roads at {junc}."

        elif cat == "weather_fog_restriction":
            scenario["initial_state"]["speed_limit_kmh"] = 60.0
            scenario["description"] = f"Visibility below 180m near {junc}. 60 km/h caution order active."

        return scenario


# Global singleton instance
_scenario_generator: Optional[ScenarioGenerator] = None

def get_scenario_generator() -> ScenarioGenerator:
    global _scenario_generator
    if _scenario_generator is None:
        _scenario_generator = ScenarioGenerator()
    return _scenario_generator
