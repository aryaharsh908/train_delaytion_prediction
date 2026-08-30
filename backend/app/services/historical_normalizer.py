import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from app.db.models import HistoricalTrainRun

logger = logging.getLogger("historical_normalizer")

class HistoricalNormalizer:
    """
    Standardizes raw API responses (RailRadar / Where Is My Train), JSON dumps, or CSV records
    into internal HistoricalTrainRun models. Missing fields are stored strictly as None (NULL).
    """

    @staticmethod
    def normalize_station_record(
        train_number: str,
        journey_date: str,
        station_data: Dict[str, Any],
        source: str = "unknown",
        train_name: Optional[str] = None,
        train_type: Optional[str] = None
    ) -> HistoricalTrainRun:

        def get_clean_val(val: Any) -> Optional[Any]:
            if val is None or val == "" or val == "N/A" or val == "NULL":
                return None
            return val

        def parse_float(val: Any) -> Optional[float]:
            try:
                if val is not None and val != "":
                    return float(val)
            except (ValueError, TypeError):
                pass
            return None

        def parse_int(val: Any) -> int:
            try:
                if val is not None:
                    return int(val)
            except (ValueError, TypeError):
                pass
            return 0

        st_seq = parse_int(station_data.get("station_sequence", station_data.get("seq", station_data.get("sequence", 0))))
        st_code = str(station_data.get("station_code", station_data.get("code", station_data.get("stationCode", "UNK"))))
        st_name = str(station_data.get("station_name", station_data.get("name", station_data.get("stationName", st_code))))

        sched_arr = get_clean_val(station_data.get("scheduled_arrival", station_data.get("sched_arr", station_data.get("scheduledArrival"))))
        act_arr = get_clean_val(station_data.get("actual_arrival", station_data.get("act_arr", station_data.get("actualArrival"))))

        sched_dep = get_clean_val(station_data.get("scheduled_departure", station_data.get("sched_dep", station_data.get("scheduledDeparture"))))
        act_dep = get_clean_val(station_data.get("actual_departure", station_data.get("act_dep", station_data.get("actualDeparture"))))

        arr_delay = parse_float(station_data.get("arrival_delay_minutes", station_data.get("arr_delay", station_data.get("delayInArrival"))))
        dep_delay = parse_float(station_data.get("departure_delay_minutes", station_data.get("dep_delay", station_data.get("delayInDeparture"))))

        from datetime import datetime
        def calc_delay(sched: str, act: str) -> float:
            try:
                s = datetime.fromisoformat(sched)
                a = datetime.fromisoformat(act)
                return (a - s).total_seconds() / 60.0
            except:
                return 0.0

        if arr_delay is None and sched_arr and act_arr:
            arr_delay = calc_delay(sched_arr, act_arr)
        if dep_delay is None and sched_dep and act_dep:
            dep_delay = calc_delay(sched_dep, act_dep)

        lat = parse_float(station_data.get("latitude", station_data.get("lat")))
        lng = parse_float(station_data.get("longitude", station_data.get("lng")))

        dist_orig = parse_float(station_data.get("distance_from_origin", station_data.get("dist", station_data.get("distance"))))
        dist_dest = parse_float(station_data.get("distance_to_destination", station_data.get("dist_dest")))

        sec_id = get_clean_val(station_data.get("section_id"))

        return HistoricalTrainRun(
            train_number=train_number,
            train_name=train_name,
            train_type=train_type,
            journey_date=journey_date,
            station_sequence=st_seq,
            station_code=st_code,
            station_name=st_name,
            scheduled_arrival=sched_arr,
            actual_arrival=act_arr,
            scheduled_departure=sched_dep,
            actual_departure=act_dep,
            arrival_delay_minutes=arr_delay,
            departure_delay_minutes=dep_delay,
            latitude=lat,
            longitude=lng,
            distance_from_origin=dist_orig,
            distance_to_destination=dist_dest,
            section_id=sec_id,
            source=source
        )

    @classmethod
    def normalize_journey(cls, raw_data: Dict[str, Any]) -> List[HistoricalTrainRun]:
        """Converts raw API response or wrapper dict into list of HistoricalTrainRun objects."""
        train_num = str(raw_data.get("train_number", "12951"))
        journey_date = str(raw_data.get("journey_date", datetime.now().strftime("%Y-%m-%d")))
        source = str(raw_data.get("source", "unknown"))
        train_name = raw_data.get("train_name")
        train_type = raw_data.get("train_type")

        payload = raw_data.get("payload", raw_data)
        
        # Real where_is_my_train_railradar API returns data wrapped in a {"data": {"route": [...]}} object
        if "data" in payload and isinstance(payload["data"], dict):
            stations = payload["data"].get("route", [])
        else:
            stations = payload.get("stations", payload.get("route", []))

        normalized_list = []
        for st in stations:
            record = cls.normalize_station_record(
                train_number=train_num,
                journey_date=journey_date,
                station_data=st,
                source=source,
                train_name=train_name,
                train_type=train_type
            )
            normalized_list.append(record)

        return normalized_list
