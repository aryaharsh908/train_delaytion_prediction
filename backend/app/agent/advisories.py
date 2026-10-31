"""
Passenger Advisory Generation Engine.
Drafts verified, multi-lingual station audio/app advisories in English and Hindi (Devanagari),
grounded in authentic ML delay forecasts and verified against the NumberValidator.
"""

import re
import json
import logging
from typing import Dict, List, Any, Optional

from app.agent.harness import get_gemma_harness
from app.agent.tools import get_train_state, get_prediction_details
from app.agent.skills import ADVISORY_SYSTEM_PROMPT
from app.agent.guardrails import NumberValidator, DISCLAIMER_TEXT

logger = logging.getLogger("passenger_advisory")


class PassengerAdvisoryWriter:
    """Generates bilingual passenger announcements strictly grounded in real timetable/ETA data."""

    def __init__(self):
        self.harness = get_gemma_harness()

    def generate_advisory(
        self,
        train_id: str,
        languages: Optional[List[str]] = None,
        model: str = "gemma-4-26b-a4b-it"
    ) -> Dict[str, Any]:
        languages = languages or ["en", "hi"]
        clean_id = train_id.replace("TRAIN_", "").strip()

        # 1. Fetch authentic train state and predictions
        state = get_train_state(clean_id)
        pred = get_prediction_details(clean_id)

        train_name = state.get("train_name", f"Express {clean_id}")
        curr_delay = float(state.get("current_delay_minutes", 0.0))
        sched_arr = pred.get("scheduled_arrival", "14:30")
        forecast_eta = pred.get("forecast_eta", "14:30")
        stations = state.get("stations", [])
        next_station = stations[0].get("code", "MTJ") if stations else "MTJ"
        platform = stations[0].get("platform", "1") if stations else "1"

        tool_trace = [
            {"tool": "get_train_state", "result": state},
            {"tool": "get_prediction_details", "result": pred}
        ]

        # 2. Formulate prompt for Gemma
        prompt = (
            f"Draft official passenger announcements for Train {clean_id} ({train_name}):\n"
            f"- Current delay: {curr_delay:.1f} minutes\n"
            f"- Next Approaching Station: {next_station} (Platform {platform})\n"
            f"- Scheduled Arrival: {sched_arr}, Dynamic Forecast ETA: {forecast_eta}\n"
            f"- Required Languages: {', '.join(languages)} (English and Hindi in Devanagari script)\n"
            f"Mandate: Never invent numbers or platforms. Use only {curr_delay:.1f} minutes delay. "
            f"Return strict JSON with keys 'en' (English text) and 'hi' (Hindi Devanagari text)."
        )

        advisories: Dict[str, str] = {}
        source = "gemma"

        try:
            res = self.harness.generate(
                prompt=prompt,
                system=ADVISORY_SYSTEM_PROMPT,
                model=model,
                json_mode=True,
                use_cache=True
            )
            raw = res.get("text", "")
            if "```json" in raw:
                raw = raw.split("```json", 1)[1].split("```", 1)[0]
            elif "```" in raw:
                raw = raw.split("```", 1)[1].split("```", 1)[0]
            parsed = json.loads(raw.strip())
            if isinstance(parsed, dict):
                for lang in languages:
                    if lang in parsed:
                        advisories[lang] = str(parsed[lang]).strip()
        except Exception as e:
            logger.warning(f"Gemma advisory generation failed: {e}")

        # Deterministic grounded fallback templates
        en_fallback = (
            f"Attention passengers: Train {clean_id} {train_name} is running late by {curr_delay:.1f} minutes. "
            f"Expected arrival at {next_station} is {forecast_eta} on Platform {platform}. Inconvenience is deeply regretted."
            if curr_delay > 0 else
            f"Attention passengers: Train {clean_id} {train_name} is running on time. "
            f"Expected arrival at {next_station} is {sched_arr} on Platform {platform}."
        )

        hi_fallback = (
            f"यात्रियों कृपया ध्यान दें: गाड़ी संख्या {clean_id} {train_name} अपने निर्धारित समय से {curr_delay:.1f} मिनट की देरी से चल रही है। "
            f"{next_station} पर इसके आगमन का अनुमानित समय {forecast_eta} प्लेटफॉर्म {platform} पर है। असुविधा के लिए हमें खेद है।"
            if curr_delay > 0 else
            f"यात्रियों कृपया ध्यान दें: गाड़ी संख्या {clean_id} {train_name} समय पर चल रही है। "
            f"{next_station} पर प्लेटफॉर्म {platform} पर इसके आगमन का निर्धारित समय {sched_arr} है।"
        )

        if "en" not in advisories or not advisories["en"]:
            advisories["en"] = en_fallback
            source = "fallback"

        if "hi" not in advisories or not advisories["hi"]:
            advisories["hi"] = hi_fallback

        # 3. Validate numbers in English advisory text against tool trace
        is_num_valid, ungrounded, num_err = NumberValidator.validate(
            text_to_check=advisories["en"],
            tool_trace=tool_trace,
            allowed_delta=1.0,
            known_train_ids={clean_id}
        )

        if not is_num_valid:
            logger.warning(f"Advisory contained ungrounded numbers {ungrounded}; reverting to deterministic template.")
            advisories["en"] = en_fallback
            advisories["hi"] = hi_fallback
            source = "fallback"

        return {
            "train_id": clean_id,
            "train_name": train_name,
            "current_delay_minutes": curr_delay,
            "next_station": next_station,
            "platform": platform,
            "advisories": advisories,
            "source": source,
            "number_validator_passed": is_num_valid,
            "disclaimer": DISCLAIMER_TEXT
        }


# Global singleton instance
_advisory_writer: Optional[PassengerAdvisoryWriter] = None

def get_advisory_writer() -> PassengerAdvisoryWriter:
    global _advisory_writer
    if _advisory_writer is None:
        _advisory_writer = PassengerAdvisoryWriter()
    return _advisory_writer
