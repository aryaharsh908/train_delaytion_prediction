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
        print(f"Error for {train_no}:", e)
    return None

trains = ["12951", "12626", "12302", "12002", "12424", "12622", "12724"]
for t in trains:
    d = fetch_confirmtkt_live_status(t)
    if d:
        print(f"=== TRAIN {t} ({d.get('TrainName')}) ===")
        print("  Current Station:", d.get("CurrentStationName"), f"({d.get('CurrentStationCode')})")
        print("  Delay:", d.get("Delay"), "mins | Status:", d.get("Status"))
        sched = d.get("Schedule", [])
        print("  Stoppages count:", len(sched))
        # Print a few stations that have non-zero delays or actual arrival times
        for st in sched:
            if st.get("DelayInArrival") or st.get("ActualArrivalTime"):
                print(f"   -> {st.get('StationCode')} ({st.get('StationName')}): Sched {st.get('ArrivalTime')} vs Act {st.get('ActualArrivalTime')} | Delay: {st.get('DelayInArrival')} min")
    print("\n" + "="*50)
