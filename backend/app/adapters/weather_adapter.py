from typing import Dict, Any, List
from app.adapters.base import WeatherAdapter

class MockWeatherAdapter(WeatherAdapter):
    """
    Mock & Spatial Weather Data Adapter.
    Spatially maps weather conditions (Fog, Rain, Visibility, Storm) to specific railway sections.
    """
    def __init__(self):
        self.active_weather_zones: List[Dict[str, Any]] = []

    def set_active_weather_zones(self, zones: List[Dict[str, Any]]):
        self.active_weather_zones = zones

    def get_weather_at_coordinates(self, lat: float, lng: float) -> Dict[str, Any]:
        for zone in self.active_weather_zones:
            # Check bounding box / radius
            z_lat, z_lng = zone["center_lat"], zone["center_lng"]
            radius_km = zone.get("radius_km", 50.0)
            
            # Approx distance calculation
            dist_km = ((lat - z_lat)**2 + (lng - z_lng)**2)**0.5 * 111.0
            if dist_km <= radius_km:
                return {
                    "condition": zone["condition"],  # FOG, HEAVY_RAIN, CLEAR
                    "visibility_meters": zone.get("visibility_meters", 150.0),
                    "temperature_c": zone.get("temperature_c", 14.0),
                    "wind_speed_kmh": zone.get("wind_speed_kmh", 12.0)
                }
                
        return {
            "condition": "CLEAR",
            "visibility_meters": 10000.0,
            "temperature_c": 26.0,
            "wind_speed_kmh": 10.0
        }

    def get_weather_for_section(self, section_id: str) -> Dict[str, Any]:
        for zone in self.active_weather_zones:
            if zone.get("affected_section_id") == section_id:
                return {
                    "condition": zone["condition"],
                    "visibility_meters": zone.get("visibility_meters", 150.0),
                    "speed_penalty_pct": zone.get("speed_penalty_pct", 0.4) # e.g. 40% speed reduction in dense fog
                }
        return {
            "condition": "CLEAR",
            "visibility_meters": 10000.0,
            "speed_penalty_pct": 0.0
        }
