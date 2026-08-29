from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from app.schemas.schemas import RTISTelemetrySchema, COAEventSchema, UnexpectedEventSchema

class HistoricalDataAdapter(ABC):
    """Interface for Ingesting Historical Train Running Data."""
    @abstractmethod
    def load_historical_runs(self) -> List[Dict[str, Any]]:
        pass

class RTISAdapter(ABC):
    """Interface for Real-Time Train Information System Telemetry Feed."""
    @abstractmethod
    def fetch_latest_telemetry(self, train_id: str) -> Optional[RTISTelemetrySchema]:
        pass
    
    @abstractmethod
    def fetch_all_telemetry(self) -> List[RTISTelemetrySchema]:
        pass

class COAAdapter(ABC):
    """Interface for Control Office Application Operational Events Feed."""
    @abstractmethod
    def fetch_recent_events(self) -> List[COAEventSchema]:
        pass

class WeatherAdapter(ABC):
    """Interface for Spatial Weather Data Feed."""
    @abstractmethod
    def get_weather_at_coordinates(self, lat: float, lng: float) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def get_weather_for_section(self, section_id: str) -> Dict[str, Any]:
        pass
