import requests
import json
import re

url = "https://www.confirmtkt.com/train-running-status/12302"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

res = requests.get(url, headers=headers)
if res.status_code == 200:
    pos = res.text.find("data = {")
    if pos != -1:
        decoder = json.JSONDecoder()
        data, _ = decoder.raw_decode(res.text[pos + 7:])
        print("Root Keys:", list(data.keys()))
        print("CurrentStationName:", data.get("CurrentStationName"))
        print("CurrentStationCode:", data.get("CurrentStationCode"))
        print("Delay:", data.get("Delay"))
        print("CurrentDelay:", data.get("CurrentDelay"))
        print("Status:", data.get("Status"))
        print("\nSchedule Sample (first 3 stations):")
        for st in data.get("Schedule", [])[:3]:
            print(" ", st.get("StationCode"), st.get("StationName"), "->", {
                "arr_del": st.get("DelayInArrival"),
                "dep_del": st.get("DelayInDeparture"),
                "sched_arr": st.get("ScheduleArrival"),
                "sched_dep": st.get("ScheduleDeparture"),
                "act_arr": st.get("ActualArrival"),
                "act_dep": st.get("ActualDeparture"),
                "has_dept": st.get("HasDeparted"),
                "is_cur": st.get("IsCurrentStation")
            })
