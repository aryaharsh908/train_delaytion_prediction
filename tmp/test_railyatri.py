import requests
import json

url = "https://api.railyatri.in/api/live_train_status.json?train_number=12302"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*"
}

try:
    r = requests.get(url, headers=headers, timeout=5)
    print("STATUS:", r.status_code)
    data = r.json()
    print("KEYS:", list(data.keys()))
    print("Train Name:", data.get("train_name"))
    print("Current Station Name:", data.get("current_station_name"))
    print("Delay Minutes:", data.get("delay") or data.get("delay_minutes") or data.get("late_minutes"))
    print("Status Message:", data.get("status_message") or data.get("status"))
    print("Full Json:", json.dumps(data, indent=2)[:1000])
except Exception as e:
    import traceback
    traceback.print_exc()
