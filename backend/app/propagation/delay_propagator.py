import heapq
from typing import Dict, List, Any
from app.graph.railway_graph import RailwayNetworkGraph

class CascadingDelayEngine:
    """
    Cascading Multi-Factor Delay Calculator & Section Recovery Engine.
    Implements realistic delay composition (Initial Delay, Train Precedence Wait, Signal Restriction,
    Platform Occupied, Slow Section, Freight Ahead, Crew Issue, Junction Congestion)
    and section speed recovery math (-4 min recovered).
    """
    @staticmethod
    def compute_cascading_breakdown(base_delay: float, priority: int = 2) -> Dict[str, float]:
        """
        Computes detailed breakdown of cascading factors that compose total train delay.
        Example flow:
        - 10 min initial delay
        - waits for another train (+8)
        - signal restriction (+4)
        - platform occupied (+6)
        - slow section (+5)
        - freight train ahead (+12)
        - crew issue (+10)
        - junction congestion (+15)
        Total = 70 min
        """
        if base_delay <= 0:
            return {
                "initial_delay": 0.0,
                "train_wait": 0.0,
                "signal_restriction": 0.0,
                "platform_occupied": 0.0,
                "slow_section": 0.0,
                "freight_ahead": 0.0,
                "crew_issue": 0.0,
                "junction_congestion": 0.0,
                "total_cascading_delay": 0.0
            }

        # Proportionally scale realistic cascading components based on overall delay magnitude
        ratio = max(0.1, min(2.5, base_delay / 70.0))
        
        # Priority 1 (Rajdhani) suffers less freight/wait delay than Priority 3 (Express)
        p_factor = 0.6 if priority == 1 else (1.0 if priority == 2 else 1.4)

        initial = round(10.0 * ratio, 1)
        wait = round(8.0 * ratio * p_factor, 1)
        signal = round(4.0 * ratio, 1)
        platform = round(6.0 * ratio, 1)
        slow_sec = round(5.0 * ratio, 1)
        freight = round(12.0 * ratio * p_factor, 1)
        crew = round(10.0 * ratio, 1)
        junction = round(15.0 * ratio * p_factor, 1)

        total = round(initial + wait + signal + platform + slow_sec + freight + crew + junction, 1)

        return {
            "initial_delay": initial,
            "train_wait": wait,
            "signal_restriction": signal,
            "platform_occupied": platform,
            "slow_section": slow_sec,
            "freight_ahead": freight,
            "crew_issue": crew,
            "junction_congestion": junction,
            "total_cascading_delay": total
        }

    @staticmethod
    def compute_section_recovery(section_length_km: float, max_speed_kmh: float,
                                actual_speed_kmh: float, priority: int,
                                current_delay: float) -> float:
        """
        Calculates time added or recovered on a section.
        High priority trains running near max speed recover lost time (returns negative value e.g. -4.0 min).
        Slowed trains accumulate section delay (returns positive value e.g. +8.0 min).
        """
        sched_time_min = (section_length_km / max(1.0, max_speed_kmh)) * 60.0
        
        if actual_speed_kmh <= 0:
            return 10.0  # Stopped

        actual_time_min = (section_length_km / max(1.0, actual_speed_kmh)) * 60.0
        diff_min = actual_time_min - sched_time_min

        # If train is running faster than baseline timetable or recovering delay on clear track
        if diff_min <= 0 or (priority == 1 and current_delay > 5.0 and actual_speed_kmh > max_speed_kmh * 0.85):
            # Recovery capability (up to -6 mins recovered per section)
            recovery = min(6.0, max(1.0, current_delay * 0.25))
            return -round(recovery, 1)

        return round(diff_min, 1)


class DelayPropagationEngine:
    """
    Graph-based Delay Propagation Engine.
    Simulates priority-based queueing delays when delayed trains occupy sections or junctions.
    Modular design allows future replacement with a Graph Neural Network (GNN).
    """
    def __init__(self, network_graph: RailwayNetworkGraph):
        self.graph = network_graph

    def compute_network_propagation(self, active_trains: Dict[str, Dict[str, Any]]) -> Dict[str, float]:
        """
        Calculates propagated delay additions for all active trains based on junction/section conflicts.
        Returns a mapping of train_id -> propagated_delay_addition_minutes.
        """
        propagated_delays = {t_id: 0.0 for t_id in active_trains}
        
        # Priority Queue for handling sequence of section occupancy events
        # Tuple: (priority_rank, current_delay, train_id)
        pq = []
        for t_id, train in active_trains.items():
            # Lower priority rank number = higher priority (Rajdhani=1)
            priority_rank = train.get("priority", 3)
            current_delay = train.get("current_delay_minutes", 0.0)
            heapq.heappush(pq, (priority_rank, -current_delay, t_id))
            
        # Group trains by current section to find conflicts
        section_occupancy = {}
        for t_id, train in active_trains.items():
            sec_id = train.get("current_section_id")
            if sec_id:
                if sec_id not in section_occupancy:
                    section_occupancy[sec_id] = []
                section_occupancy[sec_id].append(train)
                
        # Calculate trailing delay penalties when multiple trains occupy/approach same section
        for sec_id, train_list in section_occupancy.items():
            if len(train_list) > 1:
                # Sort by priority and current delay
                sorted_trains = sorted(train_list, key=lambda x: (x.get("priority", 3), -x.get("current_delay_minutes", 0.0)))
                # The lead train proceeds; trailing lower-priority trains suffer queueing delay
                lead_train = sorted_trains[0]
                lead_delay = lead_train.get("current_delay_minutes", 0.0)
                
                for trailing_train in sorted_trains[1:]:
                    trail_id = trailing_train["train_id"]
                    # Priority gap calculation
                    p_diff = trailing_train.get("priority", 3) - lead_train.get("priority", 3)
                    conflict_delay = min(lead_delay * 0.4 + (p_diff * 4.0), 20.0)
                    propagated_delays[trail_id] += conflict_delay
                    
        return propagated_delays

