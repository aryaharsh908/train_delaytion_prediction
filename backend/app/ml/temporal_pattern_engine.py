import os
import json
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, Any, Tuple, Optional, List
import numpy as np
from sqlalchemy.orm import Session

from app.config import settings
from app.db.models import HistoricalTrainRun

logger = logging.getLogger("temporal_pattern_engine")

class TemporalPatternEngine:
    """
    2-Year Temporal Pattern, Specific Date Anomaly & Chain Delay Recovery Engine.
    
    Functions:
    1. Same-Weekday 2-Year Pattern: Evaluates the specific day-of-week historical baseline
       (e.g. Saturday status vs past 104 Saturdays over 2 years, NOT continuous adjacent days).
    2. Specific Date & Month Anomaly Recognition: Detects recurring calendar date delays
       where delays were historically abnormal (e.g. festivals, seasonal fog/monsoon spikes).
    3. Cascading Delay Chain & Recovery Dynamics: Tracks section-by-section delay recovery
       and delay compounding across the 2-year training history.
    """

    PROFILE_CACHE_PATH = os.path.join(settings.MODEL_DIR, "temporal_profiles.json")

    def __init__(self, db: Optional[Session] = None):
        self.db = db
        self.weekday_profiles: Dict[str, Dict[str, float]] = {}
        self.date_anomaly_profiles: Dict[str, float] = {}
        self.recovery_profiles: Dict[str, Dict[str, float]] = {}
        self.is_loaded = False
        self.load_or_compute_profiles()

    def load_or_compute_profiles(self, force_recompute: bool = False):
        """Loads cached temporal profiles from disk or computes them from the database."""
        if not force_recompute and os.path.exists(self.PROFILE_CACHE_PATH):
            try:
                with open(self.PROFILE_CACHE_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.weekday_profiles = data.get("weekday_profiles", {})
                    self.date_anomaly_profiles = data.get("date_anomaly_profiles", {})
                    self.recovery_profiles = data.get("recovery_profiles", {})
                    self.is_loaded = True
                    logger.info(f"Loaded {len(self.weekday_profiles)} weekday profiles and {len(self.date_anomaly_profiles)} date anomaly profiles from cache.")
                    return
            except Exception as e:
                logger.warning(f"Failed loading cached temporal profiles: {e}. Recomputing from DB...")

        if self.db is not None:
            self.compute_and_persist_profiles()

    def compute_and_persist_profiles(self):
        """Extracts complete 2-year distributions from HistoricalTrainRun and saves to disk."""
        if self.db is None:
            logger.warning("No database session provided to compute temporal profiles.")
            return

        runs = self.db.query(
            HistoricalTrainRun.train_number,
            HistoricalTrainRun.journey_date,
            HistoricalTrainRun.station_code,
            HistoricalTrainRun.station_sequence,
            HistoricalTrainRun.distance_from_origin,
            HistoricalTrainRun.arrival_delay_minutes
        ).filter(
            HistoricalTrainRun.arrival_delay_minutes.isnot(None),
            HistoricalTrainRun.journey_date.isnot(None)
        ).all()

        if not runs:
            logger.warning("No historical runs found in database to compute profiles.")
            return

        # 1. Day-of-the-Week Grouping (Station + Sequence + Weekday 0..6)
        # Weekday: 0=Mon, 1=Tue, 2=Wed, 3=Thu, 4=Fri, 5=Sat, 6=Sun
        weekday_groups = defaultdict(list)
        overall_station_delays = defaultdict(list)
        calendar_date_groups = defaultdict(list)
        journey_runs = defaultdict(list)

        for r in runs:
            train_no, j_date, st_code, st_seq, dist_orig, arr_delay = r
            delay = float(arr_delay)
            st_code = st_code or "UNK"
            st_seq = int(st_seq or 1)
            sec_key = f"{st_code}_{st_seq}"
            overall_station_delays[sec_key].append(delay)
            overall_station_delays[st_code].append(delay)

            # Fast integer date parsing
            dt_str = str(j_date)[:10]
            try:
                y, m, d = int(dt_str[:4]), int(dt_str[5:7]), int(dt_str[8:10])
                dt = datetime(y, m, d)
                wd = dt.weekday()
                weekday_groups[f"{sec_key}_wd{wd}"].append(delay)
                weekday_groups[f"{st_code}_wd{wd}"].append(delay)
                weekday_groups[f"GLOBAL_wd{wd}"].append(delay)

                mm_dd = f"{m:02d}-{d:02d}"
                calendar_date_groups[f"{sec_key}_{mm_dd}"].append(delay)
                calendar_date_groups[f"{st_code}_{mm_dd}"].append(delay)
                calendar_date_groups[f"GLOBAL_{mm_dd}"].append(delay)
            except Exception:
                pass

            journey_runs[(train_no, j_date)].append((st_seq, st_code, float(dist_orig or 0.0), delay))

        # Build Weekday Profiles (Median, Std, Sample Count, Anomaly Ratio)
        new_weekday_profiles = {}
        for key, delay_list in weekday_groups.items():
            if delay_list:
                med = float(np.median(delay_list))
                mean_val = float(np.mean(delay_list))
                std_val = float(np.std(delay_list)) if len(delay_list) > 1 else 1.5
                p75_val = float(np.percentile(delay_list, 75)) if len(delay_list) >= 4 else med
                new_weekday_profiles[key] = {
                    "median_delay": round(med, 2),
                    "mean_delay": round(mean_val, 2),
                    "std_delay": round(std_val, 2),
                    "p75_delay": round(p75_val, 2),
                    "samples": len(delay_list)
                }

        # Build Date & Month Anomaly Profiles (Relative to section baseline)
        base_station_medians = {
            k: float(np.median(delays)) for k, delays in overall_station_delays.items() if delays
        }

        new_date_anomaly_profiles = {}
        for date_key, delay_list in calendar_date_groups.items():
            if delay_list and len(delay_list) >= 2:
                date_med = float(np.median(delay_list))
                base_key = date_key.rsplit("_", 1)[0]
                base_med = base_station_medians.get(base_key, 10.0)
                anomaly_delta = round(date_med - base_med, 2)
                if abs(anomaly_delta) >= 2.0 or "GLOBAL_" in date_key:
                    new_date_anomaly_profiles[date_key] = anomaly_delta

        # 3. Section Delay Recovery & Compounding Dynamics
        # Track station-by-station recovery (where arr_delay[i+1] < arr_delay[i])
        new_recovery_profiles = {}
        recovery_observations = defaultdict(list)
        compounding_observations = defaultdict(list)

        for (train_no, j_date), station_runs in journey_runs.items():
            station_runs.sort(key=lambda s: s[0])
            for i in range(len(station_runs) - 1):
                cur_seq, cur_st, cur_dist, c_del = station_runs[i]
                nxt_seq, nxt_st, nxt_dist, n_del = station_runs[i + 1]
                sec_pair_key = f"{cur_st}_{nxt_st}"

                if c_del > 5.0: # Train was running late
                    delay_recovered = max(0.0, c_del - n_del)
                    recovery_observations[sec_pair_key].append(delay_recovered)
                    recovery_observations[f"{cur_st}_NEXT"].append(delay_recovered)

                delay_added = max(0.0, n_del - c_del)
                compounding_observations[sec_pair_key].append(delay_added)
                compounding_observations[f"{cur_st}_NEXT"].append(delay_added)

        for sec_key, rec_list in recovery_observations.items():
            if rec_list:
                comp_list = compounding_observations.get(sec_key, [0.0])
                avg_rec = float(np.mean(rec_list))
                avg_comp = float(np.mean(comp_list))
                rec_prob = float(np.mean([1.0 if r > 1.0 else 0.0 for r in rec_list]))
                new_recovery_profiles[sec_key] = {
                    "mean_recovery_minutes": round(avg_rec, 2),
                    "mean_compounding_minutes": round(avg_comp, 2),
                    "recovery_probability": round(rec_prob, 2),
                    "samples": len(rec_list)
                }

        self.weekday_profiles = new_weekday_profiles
        self.date_anomaly_profiles = new_date_anomaly_profiles
        self.recovery_profiles = new_recovery_profiles
        self.is_loaded = True

        # Persist to disk
        os.makedirs(settings.MODEL_DIR, exist_ok=True)
        with open(self.PROFILE_CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump({
                "weekday_profiles": self.weekday_profiles,
                "date_anomaly_profiles": self.date_anomaly_profiles,
                "recovery_profiles": self.recovery_profiles,
                "generated_at": datetime.now().isoformat(),
                "total_runs_analyzed": len(runs)
            }, f, indent=2)

        logger.info(f"Successfully computed and saved 2-year temporal profiles to {self.PROFILE_CACHE_PATH}.")

    def get_same_weekday_delay(self, station_code: str, station_sequence: int, target_weekday: int, default_median: float = 12.0) -> Tuple[float, float]:
        """
        Retrieves the 2-year historical median and volatility specifically for target_weekday
        (e.g., Saturday = 5) on this exact section.
        """
        key1 = f"{station_code}_{station_sequence}_wd{target_weekday}"
        key2 = f"{station_code}_wd{target_weekday}"
        key3 = f"GLOBAL_wd{target_weekday}"

        prof = self.weekday_profiles.get(key1) or self.weekday_profiles.get(key2) or self.weekday_profiles.get(key3)
        if prof:
            return prof.get("median_delay", default_median), prof.get("std_delay", 1.5)

        # Heuristic weekday scaling if specific station has low samples
        # Saturdays and Sundays typically have higher congestion on passenger corridors (+20-35%)
        weekday_mult = 1.30 if target_weekday == 5 else (1.20 if target_weekday == 6 else (1.10 if target_weekday == 0 else 1.0))
        return default_median * weekday_mult, 1.8

    def get_calendar_date_anomaly(self, station_code: str, station_sequence: int, dt: datetime) -> float:
        """
        Recognizes abnormal delay patterns on specific calendar dates of specific months
        (e.g., recurring festival surges, seasonal fog peaks, monsoon slowdowns) from past 2 years.
        """
        mm_dd = dt.strftime("%m-%d")
        sec_key = f"{station_code}_{station_sequence}_{mm_dd}"
        st_key = f"{station_code}_{mm_dd}"
        glob_key = f"GLOBAL_{mm_dd}"

        if sec_key in self.date_anomaly_profiles:
            return self.date_anomaly_profiles[sec_key]
        if st_key in self.date_anomaly_profiles:
            return self.date_anomaly_profiles[st_key]
        if glob_key in self.date_anomaly_profiles:
            return self.date_anomaly_profiles[glob_key]

        # Check recurring Indian Railway seasonal anomaly windows
        month = dt.month
        day = dt.day

        # 1. Peak North Indian Fog Season (Dec 15 - Jan 31): High recurring abnormal delay (+20 to +40 mins)
        if (month == 12 and day >= 15) or (month == 1 and day <= 31):
            return 22.5
        
        # 2. Monsoon Infiltration Season (July 5 - Aug 15): Speed restrictions (+10 to +18 mins)
        if (month == 7 and day >= 5) or (month == 8 and day <= 15):
            return 12.0

        # 3. Peak Diwali / Chhath Festival Surge (Late October - Early November): High passenger load (+15 to +30 mins)
        if (month == 10 and day >= 20) or (month == 11 and day <= 10):
            return 18.0

        return 0.0

    def get_section_delay_recovery_capability(self, station_code: str, next_station_code: Optional[str] = None, distance_km: float = 80.0) -> Tuple[float, float]:
        """
        Evaluates the section's historical delay recovery rate and compounding tendency.
        Returns (mean_recovery_minutes, recovery_probability).
        """
        pair_key = f"{station_code}_{next_station_code}" if next_station_code else None
        next_key = f"{station_code}_NEXT"

        prof = (self.recovery_profiles.get(pair_key) if pair_key else None) or self.recovery_profiles.get(next_key)
        if prof:
            base_rec = prof.get("mean_recovery_minutes", 0.0)
            base_prob = prof.get("recovery_probability", 0.0)
            dist_factor = min(1.5, max(0.2, distance_km / 80.0))
            return round(base_rec * dist_factor, 2), round(base_prob * min(1.0, dist_factor), 2)

        # Longer clear sections (>80km) between major junctions provide recovery slack
        if distance_km >= 80.0:
            return round(min(distance_km * 0.08, 12.0), 1), 0.65
        return 0.5, 0.20
