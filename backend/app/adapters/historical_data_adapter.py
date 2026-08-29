import time
import logging
import requests
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from app.config import settings

logger = logging.getLogger("historical_data_adapter")

class HistoricalDataAdapter(ABC):
    """
    Abstract interface for fetching historical train running records and station schedules.
    Must be completely separated from the ML prediction model.
    """
    
    @abstractmethod
    def fetch_train_history(
        self, train_number: str, start_date: str, end_date: str
    ) -> List[Dict[str, Any]]:
        """Fetch historical train runs over a date range."""
        pass

    @abstractmethod
    def fetch_train_day(
        self, train_number: str, journey_date: str
    ) -> Optional[Dict[str, Any]]:
        """Fetch historical running data for a single train on a specific journey date."""
        pass

    @abstractmethod
    def fetch_train_route(
        self, train_number: str
    ) -> Optional[Dict[str, Any]]:
        """Fetch official station-by-station route schedule for a train."""
        pass


class WhereIsMyTrainHistoricalAdapter(HistoricalDataAdapter):
    """
    Official Historical Data Adapter configured for RailRadar / Where Is My Train API.
    Reads credentials and rate limits dynamically from Settings / environment variables.
    """

    def __init__(self):
        self.api_key = settings.WHERE_IS_MY_TRAIN_API_KEY
        self.base_url = settings.WHERE_IS_MY_TRAIN_BASE_URL.rstrip('/')
        self.auth_header = settings.WHERE_IS_MY_TRAIN_AUTH_HEADER
        self.client_id = settings.WHERE_IS_MY_TRAIN_CLIENT_ID
        self.client_secret = settings.WHERE_IS_MY_TRAIN_CLIENT_SECRET
        self.request_delay = settings.REQUEST_DELAY
        self.max_rpm = settings.MAX_REQUESTS_PER_MINUTE
        self.last_request_time = 0.0
        self.using_synthetic_fallback = False

    def _enforce_rate_limit(self):
        """Applies configured request delay and rate limiting to respect API provider limits."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.request_delay:
            time.sleep(self.request_delay - elapsed)
        self.last_request_time = time.time()

    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "User-Agent": "SIH26028-ETA-System/1.0",
            "Accept": "application/json"
        }
        if self.api_key:
            headers[self.auth_header] = self.api_key
        if self.client_id:
            headers["x-client-id"] = self.client_id
        if self.client_secret:
            headers["x-client-secret"] = self.client_secret
        return headers

    def test_connection(self) -> Dict[str, Any]:
        """Performs ONE safe test request to verify API authentication and accessibility."""
        self._enforce_rate_limit()
        test_train = "12951"
        url = f"{self.base_url}/trains/{test_train}/live"
        try:
            res = requests.get(url, headers=self._get_headers(), timeout=5)
            is_auth = res.status_code in (200, 404)
            return {
                "provider": "Where Is My Train (RailRadar)",
                "configured": bool(self.api_key and self.base_url),
                "authenticated": is_auth,
                "status_code": res.status_code,
                "using_synthetic_fallback": self.using_synthetic_fallback,
                "last_successful_request": datetime.now().isoformat() if res.status_code == 200 else None,
                "rate_limit_status": f"{self.max_rpm} req/min (Delay: {self.request_delay}s)",
                "historical_access": "available" if res.status_code == 200 else "rate_limited_or_error"
            }
        except Exception as e:
            return {
                "provider": "Where Is My Train (RailRadar)",
                "configured": bool(self.api_key and self.base_url),
                "authenticated": False,
                "using_synthetic_fallback": True,
                "error": str(e),
                "last_successful_request": None,
                "rate_limit_status": f"{self.max_rpm} req/min",
                "historical_access": "unavailable"
            }

    def fetch_train_day(self, train_number: str, journey_date: str) -> Optional[Dict[str, Any]]:
        self._enforce_rate_limit()
        url = f"{self.base_url}/trains/{train_number}/live"
        params = {"date": journey_date}
        try:
            res = requests.get(url, headers=self._get_headers(), params=params, timeout=10)
            if res.status_code == 200:
                self.using_synthetic_fallback = False
                raw_json = res.json()
                return {
                    "source": "where_is_my_train_railradar",
                    "retrieved_at": datetime.now().isoformat(),
                    "journey_date": journey_date,
                    "train_number": train_number,
                    "api_version": settings.WHERE_IS_MY_TRAIN_API_VERSION,
                    "payload": raw_json
                }
            else:
                self.using_synthetic_fallback = False
                logger.error(f"API returned status {res.status_code} for train {train_number} on {journey_date}. No mock fallback allowed.")
                return None
        except Exception as e:
            self.using_synthetic_fallback = False
            logger.error(f"Error fetching historical train day {train_number} on {journey_date}: {e}. No mock fallback allowed.")
            return None



    _live_telemetry_cache: Dict[str, Any] = {}

    def fetch_live_train_status(self, train_number: str) -> Optional[Dict[str, Any]]:
        """
        Fetches authentic live train running status from RailRadar / NTES live data source.
        Parses actual live delay in minutes, current location, and station-wise delays.
        Includes a 30-second TTL cache to prevent rate-limiting (HTTP 429).
        """
        clean_no = train_number.replace("TRAIN_", "").replace("train_", "")
        now = datetime.now()

        # Check 30-second cache
        if clean_no in self._live_telemetry_cache:
            cached_data, cached_time = self._live_telemetry_cache[clean_no]
            if (now - cached_time).total_seconds() < 30.0:
                return cached_data

        self._enforce_rate_limit()

        # 1. Try RailRadar API first
        try:
            url = f"{self.base_url}/trains/{clean_no}/live"
            res = requests.get(url, headers=self._get_headers(), timeout=5)
            if res.status_code == 200:
                data = res.json()
                result = {
                    "train_number": clean_no,
                    "train_name": data.get("train_name", f"Train {clean_no}"),
                    "current_station_name": data.get("current_station_name", "En Route"),
                    "current_station_code": data.get("current_station_code"),
                    "delay_minutes": float(data.get("delay_minutes", 0.0)),
                    "status_message": data.get("status_message", "Running On Time"),
                    "station_delays": data.get("station_delays", {}),
                    "station_dep_delays": data.get("station_dep_delays", {}),
                    "station_arr_delays": data.get("station_arr_delays", {}),
                    "source": "railradar_live_api"
                }
                self._live_telemetry_cache[clean_no] = (result, now)
                return result
        except Exception:
            pass

        # 2. Fall back to ConfirmTkt live HTML parsing
        url = f"https://www.confirmtkt.com/train-running-status/{clean_no}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
        try:
            res = requests.get(url, headers=headers, timeout=6)
            if res.status_code == 200:
                import json, re
                for m in re.finditer(r'data\s*=\s*(\{.+?\});', res.text, re.DOTALL):
                    try:
                        data = json.loads(m.group(1))
                        schedule = data.get("Schedule", [])
                        max_delay = 0.0
                        last_passed_st = None
                        last_passed_code = None
                        last_dep_delay = 0.0
                        station_delays = {}
                        station_dep_delays = {}
                        station_arr_delays = {}
                        
                        def parse_del(val):
                            if not val:
                                return 0.0
                            if isinstance(val, (int, float)):
                                return float(val)
                            nums = re.findall(r'\d+', str(val))
                            return float(nums[0]) if nums else 0.0

                        for st in schedule:
                            st_code = st.get("StationCode")
                            st_name = st.get("StationName")
                            arr_del = parse_del(st.get("arrivalDelay") or st.get("DelayInArrival"))
                            dep_del = parse_del(st.get("departureDelay") or st.get("DelayInDeparture") or arr_del)
                            dep_flag = st.get("isHasDeparted") or st.get("HasDeparted") or False
                            arr_flag = st.get("isHasArrived") or st.get("HasArrived") or False
                            
                            if st_code:
                                station_delays[st_code] = max(arr_del, dep_del)
                                station_dep_delays[st_code] = dep_del
                                station_arr_delays[st_code] = arr_del
                                
                            if dep_flag or arr_flag or dep_del > 0 or arr_del > 0:
                                last_passed_st = st_name
                                last_passed_code = st_code
                                last_dep_delay = dep_del if dep_del > 0 else arr_del
                                if max(dep_del, arr_del) > max_delay:
                                    max_delay = max(dep_del, arr_del)

                        raw_delay = data.get("Delay") or data.get("CurrentDelay")
                        delay_mins = last_dep_delay if last_dep_delay > 0 else max_delay
                        if raw_delay:
                            raw_del_val = parse_del(raw_delay)
                            if raw_del_val > 0:
                                delay_mins = raw_del_val

                        # NEVER fall back to data.get("StationName") which is the destination station name
                        cur_st_name = data.get("CurrentStationName") or last_passed_st or (schedule[0].get("StationName") if schedule else "En Route")
                        cur_st_code = data.get("CurrentStationCode") or last_passed_code or (schedule[0].get("StationCode") if schedule else None)

                        self.using_synthetic_fallback = False
                        result = {
                            "train_number": clean_no,
                            "train_name": data.get("TrainName", f"Train {clean_no}"),
                            "current_station_name": cur_st_name,
                            "current_station_code": cur_st_code,
                            "delay_minutes": delay_mins,
                            "status_message": f"Running {delay_mins:.0f} min late near {cur_st_name}",
                            "station_delays": station_delays,
                            "station_dep_delays": station_dep_delays,
                            "station_arr_delays": station_arr_delays,
                            "source": "confirmtkt_live_ntes"
                        }
                        self._live_telemetry_cache[clean_no] = (result, now)
                        return result
                    except Exception:
                        pass

        except Exception as e:
            logger.warning(f"Live telemetry fetch for train {clean_no} failed: {e}.")
        
        self.using_synthetic_fallback = True
        return None

    def fetch_train_route(self, train_number: str) -> Optional[Dict[str, Any]]:

        self._enforce_rate_limit()
        url = f"{self.base_url}/trains/{train_number}/route"
        try:
            res = requests.get(url, headers=self._get_headers(), timeout=10)
            if res.status_code == 200:
                return res.json()
            return None
        except Exception as e:
            logger.error(f"Error fetching route for train {train_number}: {e}")
            return None

    def fetch_train_history(self, train_number: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        results = []
        curr = start_dt
        while curr <= end_dt:
            date_str = curr.strftime("%Y-%m-%d")
            data = self.fetch_train_day(train_number, date_str)
            if data:
                results.append(data)
            curr += timedelta(days=1)
        return results


class MockHistoricalDataAdapter(HistoricalDataAdapter):
    """
    Synthetic Historical Data Adapter.
    Generates realistic, clearly labeled historical data for local offline development.
    Active automatically when no official API key is provided.
    """

    def fetch_train_day(self, train_number: str, journey_date: str) -> Optional[Dict[str, Any]]:
        # Generate synthetic stations with full realistic delay chain
        stations = [
            {"code": "NDLS", "name": "New Delhi", "seq": 1, "sched_arr": "16:55", "sched_dep": "16:55", "dist": 0.0},
            {"code": "MTJ", "name": "Mathura Junction", "seq": 2, "sched_arr": "18:24", "sched_dep": "18:26", "dist": 141.0},
            {"code": "KOTA", "name": "Kota Junction", "seq": 3, "sched_arr": "21:40", "sched_dep": "21:50", "dist": 465.0},
            {"code": "RTM", "name": "Ratlam Junction", "seq": 4, "sched_arr": "00:45", "sched_dep": "00:50", "dist": 731.0},
            {"code": "BRC", "name": "Vadodara Junction", "seq": 5, "sched_arr": "03:48", "sched_dep": "03:58", "dist": 992.0},
            {"code": "ST", "name": "Surat", "seq": 6, "sched_arr": "05:33", "sched_dep": "05:38", "dist": 1122.0},
            {"code": "MMCT", "name": "Mumbai Central", "seq": 7, "sched_arr": "08:35", "sched_dep": "08:35", "dist": 1385.0}
        ]

        # Seed pseudo-random variance based on date hash for deterministic reproducibility
        import hashlib
        date_hash = int(hashlib.md5(f"{train_number}_{journey_date}".encode()).hexdigest(), 16)
        base_delay = (date_hash % 25)

        # 8-factor cascading delay breakdown synthesis
        initial_delay = float(date_hash % 8)
        wait_delay = float((date_hash >> 2) % 6)
        signal_delay = float((date_hash >> 4) % 5)
        platform_delay = float((date_hash >> 6) % 7)
        slow_delay = float((date_hash >> 8) % 6)
        freight_delay = float((date_hash >> 10) % 10)
        crew_delay = float((date_hash >> 12) % 8)
        junction_delay = float((date_hash >> 14) % 12)
        total_delay = initial_delay + wait_delay + signal_delay + platform_delay + slow_delay + freight_delay + crew_delay + junction_delay

        station_records = []
        accumulated_delay = base_delay
        for st in stations:
            # Vary delay slightly per station to mimic real-world chain progress
            station_added_delay = ((st["seq"] * 3) % 7) - 1.0
            accumulated_delay = max(0.0, accumulated_delay + station_added_delay)

            # Convert scheduled time string to actual timestamp strings
            sched_arr_dt = datetime.strptime(st["sched_arr"], "%H:%M")
            sched_dep_dt = datetime.strptime(st["sched_dep"], "%H:%M")

            act_arr_dt = sched_arr_dt + timedelta(minutes=accumulated_delay)
            act_dep_dt = sched_dep_dt + timedelta(minutes=accumulated_delay + 2)

            station_records.append({
                "station_sequence": st["seq"],
                "station_code": st["code"],
                "station_name": st["name"],
                "scheduled_arrival": st["sched_arr"],
                "actual_arrival": act_arr_dt.strftime("%H:%M"),
                "scheduled_departure": st["sched_dep"],
                "actual_departure": act_dep_dt.strftime("%H:%M"),
                "arrival_delay_minutes": round(accumulated_delay, 1),
                "departure_delay_minutes": round(accumulated_delay + 2.0, 1),
                "latitude": 28.6139 - (st["dist"] * 0.01),
                "longitude": 77.2090 + (st["dist"] * 0.005),
                "distance_from_origin": st["dist"],
                "distance_to_destination": round(1385.0 - st["dist"], 1),
                "section_id": f"{st['code']}-NEXT",
                "cascading_factors": {
                    "initial_delay": initial_delay,
                    "wait_delay": wait_delay,
                    "signal_restriction": signal_delay,
                    "platform_occupancy": platform_delay,
                    "slow_section": slow_delay,
                    "freight_ahead": freight_delay,
                    "crew_issue": crew_delay,
                    "junction_congestion": junction_delay,
                    "total_cascading_delay": round(total_delay, 1)
                }
            })

        return {
            "source": "mock_synthetic_historical",
            "retrieved_at": datetime.now().isoformat(),
            "journey_date": journey_date,
            "train_number": train_number,
            "train_name": "Rajdhani Express",
            "train_type": "SUPERFAST_EXPRESS",
            "api_version": "v1_mock",
            "payload": {
                "train_number": train_number,
                "journey_date": journey_date,
                "stations": station_records
            }
        }

    def fetch_train_route(self, train_number: str) -> Optional[Dict[str, Any]]:
        return {"train_number": train_number, "status": "mock_route_available"}

    def fetch_train_history(self, train_number: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        results = []
        curr = start_dt
        while curr <= end_dt:
            date_str = curr.strftime("%Y-%m-%d")
            data = self.fetch_train_day(train_number, date_str)
            if data:
                results.append(data)
            curr += timedelta(days=1)
        return results


def get_historical_adapter() -> HistoricalDataAdapter:
    """Factory function: Returns WhereIsMyTrainHistoricalAdapter if API key configured, otherwise MockHistoricalDataAdapter."""
    if settings.WHERE_IS_MY_TRAIN_API_KEY and settings.WHERE_IS_MY_TRAIN_BASE_URL:
        return WhereIsMyTrainHistoricalAdapter()
    return MockHistoricalDataAdapter()
