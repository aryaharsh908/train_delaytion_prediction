import requests
import json

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

def fetch_confirmtkt_live_status(train_no):
    url = f"https://www.confirmtkt.com/train-running-status/{train_no}"
    try:
        r = requests.get(url, headers=headers, timeout=8)
        if r.status_code == 200:
            pos = r.text.find("data = {")
            if pos != -1:
                json_part = r.text[pos + 7:]
                decoder = json.JSONDecoder()
                data, _ = decoder.raw_decode(json_part)
                return data
    except Exception as e:
        print("Error fetching live status:", e)
    return None

data = fetch_confirmtkt_live_status("12302")
if data:
    print("SUCCESSFULLY PARSED CONFIRMTKT REAL LIVE STATUS!")
    print("Train Name:", data.get("TrainName"))
    print("Train No:", data.get("TrainNo"))
    print("Current Station Name:", data.get("CurrentStationName"))
    print("Current Station Code:", data.get("CurrentStationCode"))
    print("Delay (minutes):", data.get("Delay"))
    print("Status Text:", data.get("Status"))
    print("Current Delay:", data.get("CurrentDelay"))

    print("\nSTATIONS IN LIVE ROUTE TIMELINE:")
    schedule = data.get("Schedule", [])
    for idx, st in enumerate(schedule[:10]):
        print(f"{st.get('StationCode')} ({st.get('StationName')}) | Sched Arr: {st.get('ArrivalTime')} | Act/Exp Arr: {st.get('ActualArrivalTime')} | Delay: {st.get('DelayInArrival')} min | Status: {st.get('Status')}")
