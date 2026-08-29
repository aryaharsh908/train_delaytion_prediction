import uuid
from datetime import datetime
from typing import List, Dict, Any
from app.schemas.schemas import COAEventSchema

class COASimulator:
    """
    Simulates Control Office Application (COA) operational event feed logs.
    """
    def __init__(self):
        self.event_logs: List[COAEventSchema] = []

    def log_event(self, event_type: str, description: str, train_id: str = None,
                  station_id: str = None, section_id: str = None,
                  severity: str = "MEDIUM", duration_min: float = 10.0) -> COAEventSchema:
        event = COAEventSchema(
            event_id=f"EVT-{uuid.uuid4().hex[:8].upper()}",
            timestamp=datetime.now().strftime("%H:%M:%S"),
            event_type=event_type,
            train_id=train_id,
            station_id=station_id,
            section_id=section_id,
            severity=severity,
            expected_duration_minutes=duration_min,
            description=description
        )
        self.event_logs.insert(0, event)
        if len(self.event_logs) > 50:
            self.event_logs.pop()
        return event

    def get_recent_events(self) -> List[COAEventSchema]:
        return self.event_logs
