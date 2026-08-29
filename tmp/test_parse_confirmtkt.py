import requests
import re
import json

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

url = "https://www.confirmtkt.com/train-running-status/12302"
r = requests.get(url, headers=headers, timeout=10)

if r.status_code == 200:
    m = re.search(r'data\s*=\s*(\{.*?\});\s*</script>', r.text, re.DOTALL)
    if m:
        raw_json_str = m.group(1)
        data = json.loads(raw_json_str)
        print("KEYS in data:", list(data.keys()))
        print("Train Name:", data.get("TrainName") or data.get("trainName"))
        print("Current Station Name:", data.get("CurrentStationName"))
        print("Delay:", data.get("Delay"))
        print("Status Message:", data.get("Status"))
        print("Current Delay:", data.get("CurrentDelay"))
        print("Stoppage / Schedule Stations count:", len(data.get("Schedule", [])))
        if data.get("Schedule"):
            print("First 3 Stations in Schedule:")
            for st in data.get("Schedule")[:3]:
                print(st)
    else:
        print("Regex match failed")
else:
    print("Status code:", r.status_code)
