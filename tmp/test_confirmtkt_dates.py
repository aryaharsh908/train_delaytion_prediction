import requests
import json
from datetime import datetime, timedelta

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

today = datetime.now()
yesterday = today - timedelta(days=1)
day_before = today - timedelta(days=2)

date_params = [
    "Today",
    "Yesterday",
    today.strftime("%d-%b-%Y"),
    yesterday.strftime("%d-%b-%Y"),
    day_before.strftime("%d-%b-%Y"),
    today.strftime("%d-%m-%Y"),
    yesterday.strftime("%d-%m-%Y")
]

for dp in date_params:
    url = f"https://www.confirmtkt.com/train-running-status/12302?Date={dp}"
    try:
        r = requests.get(url, headers=headers, timeout=6)
        if r.status_code == 200:
            pos = r.text.find("data = {")
            if pos != -1:
                json_part = r.text[pos + 7:]
                decoder = json.JSONDecoder()
                data, _ = decoder.raw_decode(json_part)
                cur_st = data.get("CurrentStationName")
                delay = data.get("Delay")
                status = data.get("Status")
                print(f"Date param '{dp}': Current Station: '{cur_st}' | Delay: '{delay}' | Status: '{status}'")
    except Exception as e:
        print(f"Error {dp}:", e)
