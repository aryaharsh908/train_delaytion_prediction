import random
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class HistoricalDatasetGenerator:
    """
    Generates synthetic historical train running data for Indian Railways main corridors
    (e.g., New Delhi - Agra - Gwalior - Jhansi - Bhopal trunk line).
    Includes weather variations (fog season in Dec-Jan), section congestion, dwell delays,
    and priority recovery behavior.
    """
    def __init__(self):
        self.stations = [
            {"id": "NDLS", "name": "New Delhi", "lat": 28.6139, "lng": 77.2090, "dist": 0},
            {"id": "MTJ", "name": "Mathura Junction", "lat": 27.4924, "lng": 77.6737, "dist": 141},
            {"id": "AGC", "name": "Agra Cantt", "lat": 27.1577, "lng": 78.0081, "dist": 195},
            {"id": "GWL", "name": "Gwalior Junction", "lat": 26.2183, "lng": 78.1828, "dist": 313},
            {"id": "VGLJ", "name": "VGL Jhansi Junction", "lat": 25.4484, "lng": 78.5685, "dist": 410},
            {"id": "BINA", "name": "Bina Junction", "lat": 24.1704, "lng": 78.1856, "dist": 563},
            {"id": "BPL", "name": "Bhopal Junction", "lat": 23.2599, "lng": 77.4126, "dist": 702}
        ]
        
        self.train_configs = [
            {"number": "12951", "name": "Mumbai Rajdhani Express", "type": "RAJDHANI", "priority": 1, "avg_speed": 95},
            {"number": "12002", "name": "Bhopal Shatabdi Express", "type": "SHATABDI", "priority": 1, "avg_speed": 90},
            {"number": "12626", "name": "Kerala Express", "type": "SUPERFAST", "priority": 2, "avg_speed": 78},
            {"number": "12724", "name": "Telangana Express", "type": "SUPERFAST", "priority": 2, "avg_speed": 75},
            {"number": "11078", "name": "Jhelum Express", "type": "EXPRESS", "priority": 3, "avg_speed": 62},
            {"number": "18478", "name": "Kalinga Utkal Express", "type": "EXPRESS", "priority": 3, "avg_speed": 60}
        ]

    def generate_dataset(self, num_records: int = 5000) -> pd.DataFrame:
        random.seed(42)
        np.random.seed(42)
        
        records = []
        start_date = datetime(2025, 1, 1)
        
        runs_count = num_records // len(self.stations)
        
        for run_idx in range(runs_count):
            run_date = start_date + timedelta(days=random.randint(0, 360))
            train = random.choice(self.train_configs)
            day_of_week = run_date.weekday()
            is_fog_season = run_date.month in [12, 1]  # Dec-Jan fog in North India
            
            # Start departure from origin
            start_hour = random.choice([6, 11, 16, 21])
            scheduled_time = run_date.replace(hour=start_hour, minute=0, second=0)
            
            accumulated_delay = float(np.random.exponential(scale=5.0)) if random.random() > 0.4 else 0.0
            if is_fog_season and random.random() > 0.3:
                accumulated_delay += random.uniform(15, 60)
                
            prev_dist = 0
            
            for seq, station in enumerate(self.stations):
                dist_from_prev = station["dist"] - prev_dist
                prev_dist = station["dist"]
                
                section_id = f"{self.stations[seq-1]['id']}-{station['id']}" if seq > 0 else "ORIGIN"
                
                # Normal running time calculation (mins)
                if seq == 0:
                    sched_arr = scheduled_time
                    act_arr = sched_arr + timedelta(minutes=accumulated_delay)
                    sched_dep = sched_arr + timedelta(minutes=5)
                    act_dep = act_arr + timedelta(minutes=5)
                    arr_delay = accumulated_delay
                    dep_delay = accumulated_delay
                    section_travel_min = 0.0
                    sched_travel_min = 0.0
                    dwell_min = 5.0
                else:
                    sched_travel_min = (dist_from_prev / train["avg_speed"]) * 60
                    sched_arr = records[-1]["scheduled_departure"] + timedelta(minutes=sched_travel_min)
                    
                    # Delay factors
                    fog_penalty = random.uniform(8, 30) if (is_fog_season and seq in [1, 2, 3]) else 0.0
                    rain_penalty = random.uniform(5, 20) if run_date.month in [7, 8, 9] else 0.0 # Monsoon
                    
                    # Exaggerate weekend track maintenance delays to create strong day_of_week feature importance
                    weekend_penalty = random.uniform(10, 45) if run_date.weekday() in [5, 6] else 0.0
                    
                    congestion_penalty = float(np.random.exponential(scale=4.0)) if random.random() > 0.6 else 0.0
                    
                    # Delay recovery for high priority trains
                    recovery = 0.0
                    if train["priority"] == 1 and accumulated_delay > 10 and not fog_penalty:
                        recovery = min(accumulated_delay * 0.15, 8.0)
                        
                    delay_delta = fog_penalty + rain_penalty + weekend_penalty + congestion_penalty - recovery
                    accumulated_delay = max(0.0, accumulated_delay + delay_delta)
                    
                    act_arr = sched_arr + timedelta(minutes=accumulated_delay)
                    arr_delay = accumulated_delay
                    
                    # Dwell time
                    scheduled_dwell = 3.0 if seq < len(self.stations) - 1 else 0.0
                    actual_dwell = scheduled_dwell + (float(np.random.exponential(scale=2.0)) if random.random() > 0.7 else 0.0)
                    
                    sched_dep = sched_arr + timedelta(minutes=scheduled_dwell)
                    act_dep = act_arr + timedelta(minutes=actual_dwell)
                    dep_delay = (act_dep - sched_dep).total_seconds() / 60.0
                    accumulated_delay = dep_delay
                    
                    section_travel_min = (act_arr - records[-1]["actual_departure"]).total_seconds() / 60.0
                    dwell_min = actual_dwell
                    
                records.append({
                    "run_id": run_idx,
                    "train_id": f"TRAIN_{train['number']}",
                    "train_number": train["number"],
                    "train_name": train["name"],
                    "train_type": train["type"],
                    "train_priority": train["priority"],
                    "date": run_date.strftime("%Y-%m-%d"),
                    "day_of_week": day_of_week,
                    "is_fog_season": 1 if is_fog_season else 0,
                    "route_sequence": seq,
                    "station_id": station["id"],
                    "station_name": station["name"],
                    "latitude": station["lat"],
                    "longitude": station["lng"],
                    "distance_from_origin": station["dist"],
                    "section_id": section_id,
                    "scheduled_arrival": sched_arr,
                    "actual_arrival": act_arr,
                    "scheduled_departure": sched_dep,
                    "actual_departure": act_dep,
                    "arrival_delay": arr_delay,
                    "departure_delay": dep_delay,
                    "dwell_minutes": dwell_min,
                    "sched_section_travel_min": sched_travel_min,
                    "actual_section_travel_min": section_travel_min,
                    "delay_gained_in_section": section_travel_min - sched_travel_min if seq > 0 else 0.0
                })
                
        return pd.DataFrame(records)
