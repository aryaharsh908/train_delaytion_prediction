import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from app.schemas.schemas import UnexpectedEventSchema

class IncidentEventSimulator:
    """
    Manages interactive incident injections for demonstration and testing.
    Supports FOG, HEAVY_RAIN, SIGNAL_FAILURE, PLATFORM_OCCUPIED, JUNCTION_CONGESTION, MAINTENANCE_BLOCK, ACCIDENT.
    """
    def __init__(self):
        self.active_incidents: List[UnexpectedEventSchema] = []

    def inject_incident(self, event_type: str, section_id: str,
                        severity: str = "HIGH", duration_min: float = 20.0,
                        visibility_m: float = 150.0, speed_rest_kmh: float = 30.0) -> UnexpectedEventSchema:
        start_t = datetime.now()
        end_t = start_t + timedelta(minutes=duration_min)
        
        inc = UnexpectedEventSchema(
            event_id=f"INC-{uuid.uuid4().hex[:6].upper()}",
            event_type=event_type,
            section_id=section_id,
            from_km=0.0,
            to_km=100.0,
            start_time=start_t.strftime("%H:%M:%S"),
            expected_end_time=end_t.strftime("%H:%M:%S"),
            severity=severity,
            visibility_meters=visibility_m,
            speed_restriction_kmh=speed_rest_kmh,
            active=True
        )
        self.active_incidents.append(inc)
        return inc

    def clear_incident(self, incident_id: str):
        self.active_incidents = [inc for inc in self.active_incidents if inc.event_id != incident_id]

    def clear_all_incidents(self):
        self.active_incidents = []

    def get_incidents_for_section(self, section_id: str) -> List[UnexpectedEventSchema]:
        return [inc for inc in self.active_incidents if inc.section_id == section_id and inc.active]
