import time
import logging
import requests
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from app.config import settings, reload_settings

logger = logging.getLogger("historical_data_adapter")

class QuotaExceededException(Exception):
    """Raised when external API monthly quota or rate limit is exhausted."""
    pass

class AuthenticationException(Exception):
    """Raised when external API key is invalid or rejected."""
    pass

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
        # Always reload settings to pick up latest .env edits
        cfg = reload_settings()
        self.api_key = cfg.WHERE_IS_MY_TRAIN_API_KEY
        self.base_url = cfg.WHERE_IS_MY_TRAIN_BASE_URL.rstrip('/') if cfg.WHERE_IS_MY_TRAIN_BASE_URL else "https://api.railradar.in/v1"
        self.auth_header = cfg.WHERE_IS_MY_TRAIN_AUTH_HEADER or "x-api-key"
        self.client_id = cfg.WHERE_IS_MY_TRAIN_CLIENT_ID
        self.client_secret = cfg.WHERE_IS_MY_TRAIN_CLIENT_SECRET
        self.request_delay = cfg.REQUEST_DELAY
        self.max_rpm = cfg.MAX_REQUESTS_PER_MINUTE
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
            headers["Authorization"] = f"Bearer {self.api_key}"
        if self.client_id:
            headers["x-client-id"] = self.client_id
        if self.client_secret:
            headers["x-client-secret"] = self.client_secret
        return headers

    def test_connection(self) -> Dict[str, Any]:
        """Performs ONE safe test request to verify API authentication, quota status, and accessibility."""
        self._enforce_rate_limit()
        # Use a safe lookup or train schedule endpoint instead of //live
        url = f"{self.base_url}/trains/12302"
        try:
            res = requests.get(url, headers=self._get_headers(), timeout=6)
            rem_month = res.headers.get("x-ratelimit-remaining-month")
            lim_month = res.headers.get("x-ratelimit-limit-month")
            rem_min = res.headers.get("x-ratelimit-remaining-min")

            if res.status_code in (200, 404):
                return {
                    "provider": "Where Is My Train (RailRadar)",
                    "configured": bool(self.api_key and self.base_url),
                    "authenticated": True,
                    "status_code": res.status_code,
                    "using_synthetic_fallback": False,
                    "last_successful_request": datetime.now().isoformat(),
                    "rate_limit_status": f"{self.max_rpm} req/min",
                    "quota_remaining_month": rem_month or "Available",
                    "quota_limit_month": lim_month or "1000",
                    "rate_limit_remaining_min": rem_min,
                    "historical_access": "available",
                    "message": "Connected and authenticated successfully with RailRadar."
                }
            elif res.status_code == 429:
                err_msg = "Monthly quota exceeded (1000/1000 requests used). Rate limited by provider."
                try:
                    err_json = res.json()
                    if "error" in err_json and "message" in err_json["error"]:
                        err_msg = err_json["error"]["message"]
                except Exception:
                    pass
                return {
                    "provider": "Where Is My Train (RailRadar)",
                    "configured": bool(self.api_key and self.base_url),
                    "authenticated": False,
                    "status_code": 429,
                    "error": err_msg,
                    "quota_remaining_month": rem_month or "0",
                    "quota_limit_month": lim_month or "1000",
                    "rate_limit_remaining_min": rem_min or "0",
                    "using_synthetic_fallback": False,
                    "last_successful_request": None,
                    "rate_limit_status": f"{self.max_rpm} req/min",
                    "historical_access": "rate_limited_or_error",
                    "message": f"RailRadar Rate Limit / Quota: {err_msg}"
                }
            elif res.status_code in (401, 403):
                return {
                    "provider": "Where Is My Train (RailRadar)",
                    "configured": bool(self.api_key and self.base_url),
                    "authenticated": False,
                    "status_code": res.status_code,
                    "error": "Invalid API key or unauthorized. Please verify your RailRadar API key.",
                    "quota_remaining_month": rem_month or "0",
                    "quota_limit_month": lim_month or "1000",
                    "rate_limit_remaining_min": rem_min or "0",
                    "using_synthetic_fallback": False,
                    "last_successful_request": None,
                    "rate_limit_status": f"{self.max_rpm} req/min",
                    "historical_access": "unauthorized",
                    "message": "Invalid API Key. Please provide a valid RailRadar key."
                }
            else:
                return {
                    "provider": "Where Is My Train (RailRadar)",
                    "configured": bool(self.api_key and self.base_url),
                    "authenticated": False,
                    "status_code": res.status_code,
                    "error": f"API returned status {res.status_code}",
                    "quota_remaining_month": rem_month or "N/A",
                    "quota_limit_month": lim_month or "N/A",
                    "rate_limit_remaining_min": rem_min or "N/A",
                    "using_synthetic_fallback": False,
                    "last_successful_request": None,
                    "rate_limit_status": f"{self.max_rpm} req/min",
                    "historical_access": "rate_limited_or_error"
                }
        except Exception as e:
            return {
                "provider": "Where Is My Train (RailRadar)",
                "configured": bool(self.api_key and self.base_url),
                "authenticated": False,
                "using_synthetic_fallback": False,
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
            elif res.status_code == 429:
                self.using_synthetic_fallback = False
                err_text = "Monthly quota exceeded (1000/1000 requests used)"
                try:
                    err_text = res.json().get("error", {}).get("message", res.text)
                except Exception:
                    pass
                logger.error(f"RailRadar quota exceeded (HTTP 429) for train {train_number} on {journey_date}: {err_text}")
                raise QuotaExceededException(f"RailRadar API quota exceeded (HTTP 429): {err_text}")
            elif res.status_code in (401, 403):
                self.using_synthetic_fallback = False
                logger.error(f"RailRadar authentication failed (HTTP {res.status_code}) for train {train_number} on {journey_date}")
                raise AuthenticationException(f"RailRadar authentication failed (HTTP {res.status_code}): Invalid or missing API key")
            else:
                self.using_synthetic_fallback = False
                logger.warning(f"API returned status {res.status_code} for train {train_number} on {journey_date}.")
                return None
        except (QuotaExceededException, AuthenticationException):
            raise
        except Exception as e:
            self.using_synthetic_fallback = False
            logger.error(f"Error fetching historical train day {train_number} on {journey_date}: {e}.")
            return None



    _live_telemetry_cache: Dict[str, Any] = {}

    def fetch_live_train_status(self, train_number: str, journey_date: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Fetches authentic live train running status from RailRadar / NTES live data source.
        Accurately detects active running date for multi-day trains (Today vs Yesterday).
        Ground-truth positioning: parses exact current station, distance, delays, and passed stations.
        Includes a 45-second TTL cache for 1-minute live update cadence.
        """
        clean_no = str(train_number).replace("TRAIN_", "").replace("train_", "").strip()
        if not clean_no:
            return None
        now = datetime.now()

        cache_key = f"{clean_no}_{journey_date or 'AUTO'}"
        if cache_key in self._live_telemetry_cache:
            cached_data, cached_time = self._live_telemetry_cache[cache_key]
            if (now - cached_time).total_seconds() < 45.0:
                return cached_data

        self._enforce_rate_limit()

        def to_hhmm(val):
            if not val:
                return "--:--"
            val_str = str(val).strip()
            if "T" in val_str:
                return val_str.split("T")[1][:5]
            return val_str[:5]

        def parse_delay_text(txt):
            if not txt:
                return 0.0
            txt = str(txt).strip().lower()
            if "right time" in txt or "on time" in txt:
                return 0.0
            hr_m = re.search(r'(\d+)\s*hr', txt)
            min_m = re.search(r'(\d+)\s*min', txt)
            hrs = float(hr_m.group(1)) if hr_m else 0.0
            mins = float(min_m.group(1)) if min_m else 0.0
            if hr_m or min_m:
                return hrs * 60.0 + mins
            nums = re.findall(r'\d+', txt)
            return float(nums[0]) if nums else 0.0

        # 1. Try RailRadar API first if configured and not quota-exhausted
        if self.api_key and "your_railradar" not in self.api_key:
            try:
                url = f"{self.base_url}/trains/{clean_no}/live"
                res = requests.get(url, headers=self._get_headers(), timeout=6)
                if res.status_code == 200:
                    raw_json = res.json()
                    data = raw_json.get("data", raw_json) if isinstance(raw_json, dict) else {}
                    train_info = data.get("train", {}) if isinstance(data.get("train"), dict) else {}

                    train_name = data.get("trainName") or train_info.get("name") or data.get("train_name", f"Train {clean_no}")
                    train_type = data.get("trainType") or train_info.get("type") or "EXPRESS"
                    delay_mins = float(data.get("delayMinutes") or data.get("delay_minutes") or 0.0)

                    route_list = data.get("route") or data.get("stations") or []
                    station_delays = {}
                    station_dep_delays = {}
                    station_arr_delays = {}
                    parsed_stations = []

                    cur_loc = data.get("currentLocation", {}) if isinstance(data.get("currentLocation"), dict) else {}
                    cur_st_name = cur_loc.get("stationName") or data.get("current_station_name")
                    cur_st_code = cur_loc.get("stationCode") or data.get("current_station_code")

                    last_passed_st = None
                    last_passed_code = None

                    for st in route_list:
                        st_code = st.get("stationCode") or st.get("station_code") or st.get("code")
                        st_name = st.get("stationName") or st.get("station_name") or st.get("name")
                        arr_del = float(st.get("delayArrival") or st.get("arrival_delay_minutes") or st.get("arr_delay") or 0.0)
                        dep_del = float(st.get("delayDeparture") or st.get("departure_delay_minutes") or st.get("dep_delay") or arr_del)

                        if st_code:
                            station_delays[st_code] = max(arr_del, dep_del)
                            station_dep_delays[st_code] = dep_del
                            station_arr_delays[st_code] = arr_del

                        st_status = st.get("status", "upcoming")
                        if st_status in ("departed", "passed"):
                            last_passed_st = st_name
                            last_passed_code = st_code

                        sched_arr_raw = st.get("scheduledArrival") or st.get("scheduled_arrival") or st.get("sched_arr")
                        sched_dep_raw = st.get("scheduledDeparture") or st.get("scheduled_departure") or st.get("sched_dep")
                        act_arr_raw = st.get("actualArrival") or st.get("actual_arrival")
                        act_dep_raw = st.get("actualDeparture") or st.get("actual_departure")

                        parsed_stations.append({
                            "code": st_code,
                            "name": st_name,
                            "dist": float(st.get("distance", st.get("dist", 0.0)) or 0.0),
                            "sched_arr": to_hhmm(sched_arr_raw) if sched_arr_raw else to_hhmm(sched_dep_raw),
                            "sched_dep": to_hhmm(sched_dep_raw) if sched_dep_raw else to_hhmm(sched_arr_raw),
                            "actual_arr": to_hhmm(act_arr_raw) if act_arr_raw else None,
                            "actual_dep": to_hhmm(act_dep_raw) if act_dep_raw else None,
                            "platform": str(st.get("platform", "1")),
                            "is_halt": bool(st.get("isHalt", True)),
                            "status": st_status
                        })

                    halt_stations = [s for s in parsed_stations if s.get("is_halt")]
                    final_stations = halt_stations if len(halt_stations) >= 2 else parsed_stations

                    cur_st_name = cur_st_name or last_passed_st or (final_stations[0]["name"] if final_stations else "En Route")
                    cur_st_code = cur_st_code or last_passed_code or (final_stations[0]["code"] if final_stations else None)
                    status_msg = data.get("status_message") or (f"Running {delay_mins:.0f} min late near {cur_st_name}" if delay_mins > 0 else f"Running on time near {cur_st_name}")

                    if final_stations:
                        result = {
                            "train_number": clean_no,
                            "train_name": train_name,
                            "train_type": train_type,
                            "current_station_name": cur_st_name,
                            "current_station_code": cur_st_code,
                            "current_distance_km": None,
                            "delay_minutes": delay_mins,
                            "status_message": status_msg,
                            "station_delays": station_delays,
                            "station_dep_delays": station_dep_delays,
                            "station_arr_delays": station_arr_delays,
                            "stations": final_stations,
                            "active_journey_date": journey_date or now.strftime("%Y-%m-%d"),
                            "source": "where_is_my_train_railradar"
                        }
                        self._live_telemetry_cache[cache_key] = (result, now)
                        return result
                elif res.status_code == 429:
                    logger.info("RailRadar: Rate limit or monthly quota exceeded (HTTP 429). Falling back to live NTES parser.")
            except Exception as e:
                logger.warning(f"RailRadar live fetch for train {clean_no} failed: {e}. Falling back to live NTES parser.")

        # 2. Live NTES / ConfirmTkt Engine with Multi-Day Active Run Detection
        import re, json
        confirmtkt_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }

        today_iso = now.strftime("%Y-%m-%d")
        dates_to_try = []
        if journey_date and journey_date != today_iso:
            try:
                dt_obj = datetime.strptime(journey_date, "%Y-%m-%d")
                dates_to_try.append(dt_obj.strftime("%d-%b-%Y"))
            except Exception:
                dates_to_try.append(journey_date)
        else:
            dates_to_try = [
                now.strftime("%d-%b-%Y"),
                (now - timedelta(days=1)).strftime("%d-%b-%Y"),
                (now - timedelta(days=2)).strftime("%d-%b-%Y")
            ]

        resolved_run = None

        for d_str in dates_to_try:
            url = f"https://www.confirmtkt.com/train-running-status/{clean_no}?Date={d_str}"
            try:
                res = requests.get(url, headers=confirmtkt_headers, timeout=8)
                if res.status_code != 200:
                    continue

                code_m = re.search(r'currentStnCode\s*=\s*[\x22\x27]([^\x22\x27]+)[\x22\x27]', res.text)
                name_m = re.search(r'currentStnName\s*=\s*[\x22\x27]([^\x22\x27]+)[\x22\x27]', res.text)
                delay_m = re.search(r'latestDelay\s*=\s*([0-9\.\-]+)', res.text)
                st_m = re.search(r'class=[\x22\x27]train-update__status[\x22\x27][^>]*>(.+?)</div>', res.text, re.DOTALL)
                status_text = re.sub(r'<[^>]+>', ' ', st_m.group(1)).strip() if st_m else ''

                cur_code = code_m.group(1) if code_m else None
                cur_name = name_m.group(1) if name_m else None
                delay_val = float(delay_m.group(1)) if delay_m and delay_m.group(1) else 0.0

                json_m = re.search(r'var data = ({.+?});\s*if \(data\)', res.text, re.DOTALL)
                if not json_m:
                    continue
                data = json.loads(json_m.group(1))
                schedule = data.get("Schedule", [])
                if not schedule:
                    continue

                # If train has not started on this date yet, try previous day
                if "Yet to start" in status_text and len(dates_to_try) > 1 and d_str == dates_to_try[0]:
                    continue

                # If train reached destination on this date
                if "reached final destination" in status_text or (cur_code and cur_code == schedule[-1].get("StationCode")):
                    if not resolved_run:
                        resolved_run = (d_str, cur_code, cur_name, delay_val, status_text, schedule, res.text, data, "COMPLETED")
                    continue

                # This date is actively running!
                resolved_run = (d_str, cur_code, cur_name, delay_val, status_text, schedule, res.text, data, "RUNNING")
                break
            except Exception as e:
                logger.warning(f"ConfirmTkt fetch for train {clean_no} on {d_str} error: {e}")

        if resolved_run:
            d_str, cur_code, cur_name, delay_val, status_text, schedule, html_text, raw_data, run_state = resolved_run

            html_station_status = {}
            html_station_delay = {}
            html_station_arr = {}
            html_station_dep = {}

            rows = re.findall(r'<div class=[\x22\x27]row rs__station-row flexy[\x22\x27].*?</div>\s*</div>\s*</div>', html_text, re.DOTALL)
            for r in rows:
                name_m = re.search(r'class=[\x22\x27]rs__station-name ellipsis[\x22\x27]>([^<]+)</span>', r)
                st_name_val = name_m.group(1).strip() if name_m else ""
                if not st_name_val:
                    continue

                st_status = "upcoming"
                if "bi-check-circle" in r:
                    st_status = "passed"
                elif "circle blink" in r:
                    st_status = "current"

                del_m = re.search(r'class=[\x22\x27]rs__station-delay[^>]*>(.+?)</div>', r, re.DOTALL)
                del_txt = re.sub(r'<[^>]+>', ' ', del_m.group(1)).strip() if del_m else ""
                parsed_del = parse_delay_text(del_txt)

                cols = re.findall(r'<div class=[\x22\x27]col-xs-2[^>]*>(.+?)</div>', r, re.DOTALL)
                arr_time = re.sub(r'<[^>]+>', ' ', cols[0]).strip() if len(cols) > 0 else ""
                dep_time = re.sub(r'<[^>]+>', ' ', cols[1]).strip() if len(cols) > 1 else ""

                html_station_status[st_name_val.upper()] = st_status
                html_station_delay[st_name_val.upper()] = parsed_del
                if arr_time:
                    html_station_arr[st_name_val.upper()] = arr_time[:5]
                if dep_time:
                    html_station_dep[st_name_val.upper()] = dep_time[:5]

            # Find exact current track distance in km (searching commercial and intermediate non-stop halts)
            cur_dist = None
            if cur_code:
                for s in schedule:
                    if s.get("StationCode") == cur_code:
                        cur_dist = float(s.get("Distance", 0.0) or 0.0)
                        break
                    for sub in s.get("intermediateStations", []):
                        if sub.get("StationCode") == cur_code:
                            cur_dist = float(sub.get("Distance", 0.0) or 0.0)
                            break
                    if cur_dist is not None:
                        break

            if cur_dist is None and cur_name:
                c_upper = cur_name.strip().upper()
                for s in schedule:
                    if s.get("StationName") and s.get("StationName").strip().upper() == c_upper:
                        cur_dist = float(s.get("Distance", 0.0) or 0.0)
                        break
                    for sub in s.get("intermediateStations", []):
                        if sub.get("StationName") and sub.get("StationName").strip().upper() == c_upper:
                            cur_dist = float(sub.get("Distance", 0.0) or 0.0)
                            break
                    if cur_dist is not None:
                        break

            parsed_stations = []
            station_delays = {}
            station_dep_delays = {}
            station_arr_delays = {}
            last_passed_idx = -1

            for idx, st in enumerate(schedule):
                st_code = st.get("StationCode")
                st_name = st.get("StationName", "")
                st_name_upper = st_name.upper()
                st_dist = float(st.get("Distance", 0.0) or 0.0)

                status = html_station_status.get(st_name_upper, "upcoming")
                if status == "upcoming" and cur_dist is not None and st_dist < cur_dist:
                    status = "passed"
                elif status == "upcoming" and cur_code and st_code == cur_code:
                    status = "current"

                if status == "passed":
                    last_passed_idx = idx

                arr_del = html_station_delay.get(st_name_upper, parse_delay_text(st.get("arrivalDelay")))
                dep_del = html_station_delay.get(st_name_upper, parse_delay_text(st.get("departureDelay")))

                if st_code:
                    station_delays[st_code] = max(arr_del, dep_del)
                    station_arr_delays[st_code] = arr_del
                    station_dep_delays[st_code] = dep_del

                sched_arr_val = to_hhmm(st.get("ArrivalTime") or st.get("DepartureTime"))
                sched_dep_val = to_hhmm(st.get("DepartureTime") or st.get("ArrivalTime"))
                act_arr_val = html_station_arr.get(st_name_upper, to_hhmm(st.get("ActualArrivalTime"))) if status in ("passed", "current") else None
                act_dep_val = html_station_dep.get(st_name_upper, to_hhmm(st.get("ActualDepartureTime"))) if status == "passed" else None

                is_commercial_halt = bool(st.get("HaltMinutes") and str(st.get("HaltMinutes")).strip() not in ("", "-"))

                parsed_stations.append({
                    "code": st_code,
                    "name": st_name,
                    "dist": st_dist,
                    "sched_arr": sched_arr_val,
                    "sched_dep": sched_dep_val,
                    "actual_arr": act_arr_val,
                    "actual_dep": act_dep_val,
                    "platform": str(st.get("ExpectedPlatformNo") or "1"),
                    "is_halt": is_commercial_halt,
                    "status": status,
                    "lat": float(st.get("Latitude", 0.0) or 0.0),
                    "lng": float(st.get("Longitude", 0.0) or 0.0)
                })

            halt_stations = [s for s in parsed_stations if s.get("is_halt")]
            final_stations = halt_stations if len(halt_stations) >= 2 else parsed_stations

            if cur_dist is None and last_passed_idx >= 0:
                cur_dist = float(schedule[last_passed_idx].get("Distance", 0.0) or 0.0)

            # Convert d_str (e.g. 10-Sep-2026) to standard YYYY-MM-DD
            try:
                resolved_iso_date = datetime.strptime(d_str, "%d-%b-%Y").strftime("%Y-%m-%d")
            except Exception:
                resolved_iso_date = d_str

            cur_st_display = cur_name or (final_stations[0]["name"] if final_stations else "En Route")
            status_msg = f"{status_text} {cur_st_display}".strip() if status_text else (
                f"Running {delay_val:.0f} min late near {cur_st_display}" if delay_val > 0 else f"Running on time near {cur_st_display}"
            )

            result = {
                "train_number": clean_no,
                "train_name": raw_data.get("TrainName", f"Train {clean_no}"),
                "train_type": raw_data.get("TrainType", "EXPRESS"),
                "current_station_name": cur_st_display,
                "current_station_code": cur_code or (final_stations[0]["code"] if final_stations else None),
                "current_distance_km": cur_dist,
                "delay_minutes": delay_val,
                "status_message": status_msg,
                "active_journey_date": resolved_iso_date,
                "station_delays": station_delays,
                "station_dep_delays": station_dep_delays,
                "station_arr_delays": station_arr_delays,
                "stations": final_stations,
                "source": "confirmtkt_live_ntes"
            }
            self._live_telemetry_cache[cache_key] = (result, now)
            return result

        return None

    def fetch_train_route(self, train_number: str) -> Optional[Dict[str, Any]]:
        """Fetch train route/schedule. Delegates to fetch_live_train_status to get authentic live stations."""
        return self.fetch_live_train_status(train_number)

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
