import requests
import json
import re

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

def get_confirmtkt_live_v2(train_no):
    url = f"https://www.confirmtkt.com/train-running-status/{train_no}"
    try:
        r = requests.get(url, headers=headers, timeout=6)
        if r.status_code == 200:
            pos = r.text.find("data = {")
            if pos != -1:
                decoder = json.JSONDecoder()
                data, _ = decoder.raw_decode(r.text[pos + 7:])
                
                schedule = data.get("Schedule", [])
                max_delay = 0.0
                last_passed_st = None
                
                stoppages = []
                for st in schedule:
                    arr_del = st.get("arrivalDelay") or st.get("DelayInArrival") or st.get("departureDelay") or 0.0
                    if isinstance(arr_del, str):
                        nums = re.findall(r'\d+', arr_del)
                        arr_del = float(nums[0]) if nums else 0.0
                    else:
                        arr_del = float(arr_del)
                    
                    st_name = st.get("StationName")
                    st_code = st.get("StationCode")
                    
                    if arr_del > 0:
                        last_passed_st = st_name
                        if arr_del > max_delay:
                            max_delay = arr_del
                            
                    stoppages.append({
                        "station_code": st_code,
                        "station_name": st_name,
                        "sched_arr": st.get("ArrivalTime"),
                        "sched_dep": st.get("DepartureTime"),
                        "act_arr": st.get("ActualArrivalTime"),
                        "delay_minutes": arr_del
                    })
                
                raw_delay = data.get("Delay") or data.get("CurrentDelay")
                delay_mins = max_delay
                if raw_delay:
                    nums = re.findall(r'\d+', str(raw_delay))
                    if nums:
                        delay_mins = max(delay_mins, float(nums[0]))
                
                cur_st = data.get("CurrentStationName") or last_passed_st or (stoppages[0]["station_name"] if stoppages else "Unknown")
                
                return {
                    "train_number": train_no,
                    "train_name": data.get("TrainName"),
                    "current_station_name": cur_st,
                    "live_delay_minutes": delay_mins,
                    "status_message": f"Running {delay_mins:.0f} min late near {cur_st}",
                    "schedule": stoppages
                }
    except Exception as e:
        print(f"Error {train_no}: {e}")
    return None

for t in ["12302", "12951", "12626", "12002", "12424", "12622", "12724"]:
    res = get_confirmtkt_live_v2(t)
    if res:
        print(f"TRAIN {t} ({res['train_name']}): Delay={res['live_delay_minutes']}m | Near: {res['current_station_name']}")
