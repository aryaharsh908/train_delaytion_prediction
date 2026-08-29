import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List

class MonteCarloETASimulator:
    """
    Monte Carlo Simulation Engine for ETA Uncertainty.
    Runs 100+ stochastic future scenario simulations based on historical section variances
    and active weather/operational conditions.
    """
    def __init__(self, num_samples: int = 100):
        self.num_samples = num_samples

    def simulate_future_eta(self,
                           train_info: Dict[str, Any],
                           remaining_sections: List[Dict[str, Any]],
                           current_delay_min: float,
                           active_weather_penalty: float = 0.0,
                           junction_congestion_min: float = 0.0) -> Dict[str, Any]:
        """
        Runs Monte Carlo iterations for remaining sections.
        Returns:
        - median_delay_min
        - ci_80_min, ci_80_max
        - ci_95_min, ci_95_max
        - on_time_probability
        - sample_distribution
        """
        simulated_total_delays = []
        
        base_priority = train_info.get("priority", 3)
        
        for _ in range(self.num_samples):
            sample_delay = current_delay_min
            
            for sec in remaining_sections:
                sched_min = sec.get("scheduled_travel_min", 30.0)
                sec_id = sec.get("section_id", "")
                
                # Stochastic travel time variance (log-normal distribution)
                sec_variance = np.random.lognormal(mean=0.1, sigma=0.25) * sched_min
                sec_delay_delta = max(-3.0, sec_variance - sched_min)
                
                # Weather & Fog uncertainty factor
                if active_weather_penalty > 0:
                    fog_impact = np.random.uniform(active_weather_penalty * 0.7, active_weather_penalty * 1.4)
                else:
                    fog_impact = 0.0
                    
                # Congestion uncertainty factor
                if junction_congestion_min > 0:
                    cong_impact = np.random.exponential(scale=junction_congestion_min)
                else:
                    cong_impact = 0.0
                    
                # High-priority recovery chance
                recovery = 0.0
                if base_priority == 1 and sample_delay > 10.0 and fog_impact == 0:
                    recovery = np.random.uniform(1.0, 4.0)
                    
                sample_delay += sec_delay_delta + fog_impact + cong_impact - recovery
                sample_delay = max(0.0, sample_delay)
                
            simulated_total_delays.append(sample_delay)
            
        simulated_total_delays.sort()
        
        median_delay = float(np.median(simulated_total_delays))
        p10 = float(np.percentile(simulated_total_delays, 10))
        p90 = float(np.percentile(simulated_total_delays, 90))
        p2_5 = float(np.percentile(simulated_total_delays, 2.5))
        p97_5 = float(np.percentile(simulated_total_delays, 97.5))
        
        # On-time probability (arriving within schedule + 10 mins)
        on_time_count = sum(1 for d in simulated_total_delays if d <= 10.0)
        on_time_prob = float(on_time_count / self.num_samples)
        
        return {
            "median_delay_min": round(median_delay, 1),
            "ci_80_min_delay": round(p10, 1),
            "ci_80_max_delay": round(p90, 1),
            "ci_95_min_delay": round(p2_5, 1),
            "ci_95_max_delay": round(p97_5, 1),
            "on_time_probability": round(on_time_prob, 2),
            "samples": [round(s, 1) for s in simulated_total_delays[:30]] # Sample subset for charts
        }
