import requests
import json

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

url = "https://www.confirmtkt.com/train-running-status/12302"
r = requests.get(url, headers=headers, timeout=8)
if r.status_code == 200:
    pos = r.text.find("data = {")
    if pos != -1:
        json_part = r.text[pos + 7:]
        decoder = json.JSONDecoder()
        data, _ = decoder.raw_decode(json_part)
        print("Data type:", type(data))
        for k, v in data.items():
            if k != "Schedule":
                print(f"  {k}: {repr(v)}")
        
        print("\nSchedule item sample:")
        if data.get("Schedule"):
            print(json.dumps(data["Schedule"][0], indent=2))
            print(json.dumps(data["Schedule"][1], indent=2))
