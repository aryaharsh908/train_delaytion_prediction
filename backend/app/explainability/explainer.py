from typing import List, Dict, Any
from app.schemas.schemas import ETABreakdownFactor

class ETAExplainer:
    """
    Explainability Engine for ETA Predictions.
    Decomposes dynamic ETA updates into human-understandable factor contributions.
    """
    @classmethod
    def generate_explanation(cls,
                             current_delay_min: float,
                             weather_delay_min: float,
                             junction_congestion_min: float,
                             platform_hold_min: float,
                             recovery_min: float,
                             weather_condition: str = "FOG") -> List[ETABreakdownFactor]:
        factors = []
        
        # 1. Base accumulated delay
        if current_delay_min > 0:
            factors.append(ETABreakdownFactor(
                factor_name="Current Accumulated Delay",
                impact_minutes=round(current_delay_min, 1),
                description=f"Recorded delay carried forward from previous stations (+{round(current_delay_min, 1)} mins)"
            ))
            
        # 2. Weather impact
        if weather_delay_min > 0:
            cond_label = "Dense Fog Speed Penalty" if weather_condition == "FOG" else "Heavy Rain Speed Restriction"
            factors.append(ETABreakdownFactor(
                factor_name=cond_label,
                impact_minutes=round(weather_delay_min, 1),
                description=f"En-route speed restriction due to {weather_condition.lower()} (+{round(weather_delay_min, 1)} mins)"
            ))
            
        # 3. Junction Congestion & Precedence
        if junction_congestion_min > 0:
            factors.append(ETABreakdownFactor(
                factor_name="Junction Congestion & Precedence",
                impact_minutes=round(junction_congestion_min, 1),
                description=f"Queueing hold for higher-priority train precedence (+{round(junction_congestion_min, 1)} mins)"
            ))
            
        # 4. Platform Occupancy
        if platform_hold_min > 0:
            factors.append(ETABreakdownFactor(
                factor_name="Station Platform Hold",
                impact_minutes=round(platform_hold_min, 1),
                description=f"Unscheduled wait for platform vacancy at approaching station (+{round(platform_hold_min, 1)} mins)"
            ))
            
        # 5. Expected Recovery
        if recovery_min > 0:
            factors.append(ETABreakdownFactor(
                factor_name="High-Speed Section Recovery",
                impact_minutes=-round(recovery_min, 1),
                description=f"Expected time catch-up in high-speed MPS sections (-{round(recovery_min, 1)} mins)"
            ))
            
        if not factors:
            factors.append(ETABreakdownFactor(
                factor_name="Normal Timetable Schedule",
                impact_minutes=0.0,
                description="Train running smoothly on schedule"
            ))
            
        return factors
