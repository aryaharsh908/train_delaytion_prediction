from typing import List
from app.adapters.base import COAAdapter
from app.schemas.schemas import COAEventSchema

class MockCOAAdapter(COAAdapter):
    """
    Mock implementation of Control Office Application (COA) operational events stream.
    Emits events like SIGNAL_HALT, PRECEDENCE, PLATFORM_OCCUPIED, MAINTENANCE_BLOCK.
    Can be replaced by IndianRailwaysCOAAdapter for live IR integration.
    """
    def __init__(self, simulation_orchestrator=None):
        self.orchestrator = simulation_orchestrator

    def fetch_recent_events(self) -> List[COAEventSchema]:
        if not self.orchestrator:
            return []
        return self.orchestrator.get_coa_event_logs()
