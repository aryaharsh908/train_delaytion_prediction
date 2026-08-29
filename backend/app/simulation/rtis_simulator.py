import math
from typing import Dict, Any, List

class RTISSimulator:
    """
    Continuous RTIS Train Telemetry Generator.
    Simulates train movement along railway polylines, updating position, speed, and current delay.
    """
    def __init__(self, railway_graph):
        self.graph = railway_graph

    def step_train_movement(self, train: Dict[str, Any], sim_time_step_seconds: float) -> Dict[str, Any]:
        """
        Advances train position along its current section polyline according to its speed.
        Synchronizes station names and section progress.
        """
        sec_id = train["current_section_id"]
        sec = self.graph.sections_dict.get(sec_id)
        if not sec:
            return train

        coords = sec.get("coords", [])
        if len(coords) < 2:
            return train

        start_lat, start_lng = coords[0]
        end_lat, end_lng = coords[1]

        # Calculate effective speed considering section limits and weather
        base_speed = min(train.get("target_speed", 110.0), sec.get("current_speed_limit", 110.0))
        
        # Weather reduction
        if sec.get("weather") == "FOG":
            base_speed = min(base_speed, 45.0)
        elif sec.get("weather") == "HEAVY_RAIN":
            base_speed = min(base_speed, 65.0)
            
        if sec.get("is_blocked"):
            base_speed = 0.0

        train["speed_kmh"] = base_speed

        dist_moved_km = (base_speed / 3600.0) * sim_time_step_seconds
        total_sec_dist = max(0.1, float(sec.get("dist", 80.0)))

        current_progress = train.get("section_progress_km", 0.0) + dist_moved_km

        if current_progress >= total_sec_dist:
            train["section_progress_km"] = 0.0
            next_st_id = sec["to"]
            train["last_station_id"] = next_st_id
            
            downstream = self.graph.get_downstream_stations(next_st_id, train["destination_station_id"])
            if downstream:
                next_id = downstream[0]
                train["next_station_id"] = next_id
                st_info = self.graph.stations_dict.get(next_id, {})
                train["next_station_name"] = st_info.get("name", st_info.get("station_name", next_id))
                train["current_section_id"] = f"{next_st_id}-{next_id}"
                if train["current_section_id"] not in self.graph.sections_dict:
                    train["current_section_id"] = f"{next_id}-{next_st_id}"
            else:
                train["status"] = "ARRIVED"
                train["speed_kmh"] = 0.0
                return train
        else:
            train["section_progress_km"] = current_progress

        fraction = min(1.0, max(0.0, current_progress / total_sec_dist))
        train["lat"] = round(start_lat + fraction * (end_lat - start_lat), 6)
        train["lng"] = round(start_lng + fraction * (end_lng - start_lng), 6)

        return train
