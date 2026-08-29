import requests
import json
import re
from datetime import datetime

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

def get_confirmtkt_live(train_no):
    url = f"https://www.confirmtkt.com/train-running-status/{train_no}"
    try:
        r = requests.get(url, headers=headers, timeout=6)
        if r.status_code == 200:
            pos = r.text.find("data = {")
            if pos != -1:
                decoder = json.JSONDecoder()
                data, _ = decoder.raw_decode(r.text[pos + 7:])
                
                # Extract main delay
                current_st_name = data.get("CurrentStationName") or data.get("StationName")
                current_st_code = data.get("CurrentStationCode") or data.get("StationCode")
                raw_delay = data.get("Delay") or data.get("arrivalDelay") or data.get("departureDelay") or data.get("CurrentDelay")
                status_text = data.get("Status")
                
                # Parse numeric delay in minutes
                delay_mins = 0.0
                if raw_delay:
                    nums = re.findall(r'\d+', str(raw_delay))
                    if nums:
                        delay_mins = float(nums[0])
                
                # Extract station-wise schedules and delays
                schedule = data.get("Schedule", [])
                stoppages = []
                for st in schedule:
                    arr_del = st.get("DelayInArrival") or st.get("arrivalDelay") or 0.0
                    if isinstance(arr_del, str):
                        nums = re.findall(r'\d+', arr_del)
                        arr_del = float(nums[0]) if nums else 0.0
                    else:
                        arr_del = float(arr_del)
                    
                    stoppages.append({
                        "station_code": st.get("StationCode"),
                        "station_name": st.get("StationName"),
                        "sched_arr": st.get("ArrivalTime"),
                        "sched_dep": st.get("DepartureTime"),
                        "act_arr": st.get("ActualArrivalTime"),
                        "act_dep": st.get("ActualDepartureTime"),
                        "delay_minutes": arr_del,
                        "distance_km": st.get("Distance")
                    })
                
                return {
                    "train_number": train_no,
                    "train_name": data.get("TrainName"),
                    "current_station_name": current_st_name,
                    "current_station_code": current_st_code,
                    "live_delay_minutes": delay_mins,
                    "status_message": status_text or f"Running {delay_mins:.0f} min late near {current_st_name}",
                    "schedule": stoppages,
                    "source": "confirmtkt_live_ntes"
                }
    except Exception as e:
        print(f"Error fetching live for {train_no}: {e}")
    return None

trains = ["12302", "12951", "12626", "12002", "12424", "12622", "12724"]
for t in trains:
    res = get_confirmtkt_live(t)
    if res:
        print(f"=== TRAIN {res['train_number']} ({res['train_name']}) ===")
        print(f"  Live Delay: {res['live_delay_minutes']} mins")
        print(f"  Current Station: {res['current_station_name']} ({res['current_station_code']})")
        print(f"  Status Msg: {res['status_message']}")
        print(f"  Total Stoppages: {len(res['schedule'])}")
        print("  Sample Stoppage Delays:")
        for st in res['schedule'][:5]:
            print(f"    - {st['station_code']} ({st['station_name']}): Sched {st['sched_arr']} | Delay {st['delay_minutes']}m")
        print("="*60)
