"""
Operations Reporting Engine: Shift Handover & Post-Incident Disruption Analysis.
Powered by Gemma 4 with event log timeline reconstruction, downstream propagation modeling,
and regulatory rule grounding.
"""

import re
import json
import uuid
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from app.agent.harness import get_gemma_harness
from app.agent.tools import get_event_log, get_propagation_graph, get_active_alerts
from app.agent.skills import HANDOVER_SYSTEM_PROMPT, POST_INCIDENT_SYSTEM_PROMPT
from app.agent.guardrails import DISCLAIMER_TEXT

logger = logging.getLogger("agent_reports")


class ReportGenerator:
    """Generates formal operational reports for shift handovers and safety post-mortems."""

    def __init__(self):
        self.harness = get_gemma_harness()

    def generate_shift_handover(
        self,
        shift_id: Optional[str] = None,
        time_range: Optional[str] = None,
        model: str = "gemma-4-26b-a4b-it"
    ) -> Dict[str, Any]:
        """Compiles formal end-of-shift handover briefing for incoming Section Controller."""
        events_data = get_event_log()
        alerts_data = get_active_alerts()

        events_list = events_data.get("events", [])
        alerts_list = alerts_data.get("alerts", [])

        prompt = (
            f"Generate a formal Shift Handover Report for the Delhi-Mumbai Western Trunk Corridor.\n"
            f"- Active Alerts Count: {len(alerts_list)}\n"
            f"- Recent Dispatch Order Events: {json.dumps(events_list[:6])}\n"
            f"- Active Alert Details: {json.dumps(alerts_list[:4])}\n\n"
            f"Synthesize: 1) Executive Summary 2) Critical Incidents Handled 3) Open Corridor Bottlenecks 4) Handover Checklist.\n"
            f"Output strict JSON with keys: 'summary', 'incidents_handled', 'active_bottlenecks', 'open_action_items', 'report_markdown'."
        )

        structured_report = None
        source = "gemma"

        try:
            res = self.harness.generate(
                prompt=prompt,
                system=HANDOVER_SYSTEM_PROMPT,
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
            if isinstance(parsed, dict) and "summary" in parsed:
                structured_report = parsed
        except Exception as e:
            logger.warning(f"Gemma handover generation failed: {e}")

        # Deterministic fallback handover report
        if not structured_report:
            source = "fallback"
            structured_report = {
                "summary": "Shift Handover: Western Trunk Corridor operations maintained within safety parameters. Mathura-Kota junction headways normalized.",
                "incidents_handled": [
                    {"event_id": "EVT_001", "type": "HEADWAY_REGULATION", "status": "RESOLVED", "description": "Superfast train precedence enforced at MTJ"}
                ],
                "active_bottlenecks": ["MTJ-BTE 4th Line Convergence", "KOTA Yard Reception"],
                "open_action_items": [
                    "Monitor trailing interval of Train 12951 past Mathura",
                    "Verify clearing of cautionary speed orders near Bayana Jn"
                ],
                "report_markdown": (
                    "### Operational Shift Handover Briefing\n"
                    "- **Corridor**: Delhi - Mumbai Western Trunk Route (Mathura - Kota Section)\n"
                    "- **Status**: STABLE (No active block obstructions)\n"
                    "- **Signal Regimes**: 4-Aspect Automatic Signaling operating nominally\n"
                    "- **Handover Priority**: Maintain 7-minute separation for upcoming Vande Bharat service"
                )
            }

        structured_report["report_type"] = "shift_handover"
        structured_report["source"] = source
        structured_report["disclaimer"] = DISCLAIMER_TEXT
        structured_report["timestamp"] = datetime.now().isoformat()
        return structured_report

    def generate_post_incident(
        self,
        incident_id: Optional[str] = None,
        train_id: Optional[str] = None,
        model: str = "gemma-4-26b-a4b-it"
    ) -> Dict[str, Any]:
        """Reconstructs incident timeline, root-cause chain, and downstream cascading propagation."""
        inc_id = incident_id or "INC_2026_042"
        target_train = (train_id or "12951").replace("TRAIN_", "")

        events_data = get_event_log()
        prop_data = get_propagation_graph(target_train)

        events_list = events_data.get("events", [])
        propagation = prop_data.get("propagation", {})

        prompt = (
            f"Conduct an official Post-Incident Disruption Investigation Report for Incident {inc_id} involving Train {target_train}:\n"
            f"- Downstream Cascading Propagation: {json.dumps(propagation)}\n"
            f"- Chronological Event Log: {json.dumps(events_list[:8])}\n\n"
            f"Determine: 1) Root Cause 2) Propagation Timeline 3) Secondary Trains Affected 4) Applicable Operating Rules (e.g. PREC-01, HEAD-02) 5) Preventative Corrective Actions.\n"
            f"Output strict JSON with keys: 'incident_id', 'root_cause', 'timeline', 'cascading_trains_count', 'rule_citations', 'corrective_actions', 'summary'."
        )

        structured_report = None
        source = "gemma"

        try:
            res = self.harness.generate(
                prompt=prompt,
                system=POST_INCIDENT_SYSTEM_PROMPT,
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
            if isinstance(parsed, dict) and "root_cause" in parsed:
                structured_report = parsed
        except Exception as e:
            logger.warning(f"Gemma post-incident analysis failed: {e}")

        # Deterministic fallback post-incident analysis
        if not structured_report:
            source = "fallback"
            cascading_count = len(propagation.get("affected_trains", [])) if isinstance(propagation, dict) else 2
            structured_report = {
                "incident_id": inc_id,
                "summary": f"Incident Investigation for Train {target_train}: Converging headway conflict at junction resolved via precedence regulation.",
                "root_cause": "Concurrently converging services into single platform approach block without adequate safety interval.",
                "timeline": [
                    {"time": "14:10", "event": f"Train {target_train} entered cautionary signal block"},
                    {"time": "14:14", "event": "Section Controller issued regulation order holding secondary train"},
                    {"time": "14:22", "event": "Corridor headway restored, main through line cleared"}
                ],
                "cascading_trains_count": cascading_count,
                "rule_citations": ["PREC-01", "HEAD-02"],
                "corrective_actions": [
                    "Enforce automatic loop regulation when trailing gap falls below 18 km",
                    "Calibrate dynamic ETA model for earlier junction approach notification"
                ]
            }

        structured_report["report_type"] = "post_incident"
        structured_report["source"] = source
        structured_report["disclaimer"] = DISCLAIMER_TEXT
        structured_report["timestamp"] = datetime.now().isoformat()
        return structured_report


# Global singleton instance
_report_generator: Optional[ReportGenerator] = None

def get_report_generator() -> ReportGenerator:
    global _report_generator
    if _report_generator is None:
        _report_generator = ReportGenerator()
    return _report_generator
