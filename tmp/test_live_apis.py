import requests
import json
from datetime import datetime

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.google.com/"
}

# Date format choices
today_str = datetime.now().strftime("%Y%m%d")
today_hyphen = datetime.now().strftime("%Y-%m-%d")
today_ddmmyyyy = datetime.now().strftime("%d-%m-%Y")

endpoints = [
    f"https://www.confirmtkt.com/api/platform/trainrunningstatus/trainno/12302?startDate={today_str}",
    f"https://www.confirmtkt.com/api/platform/trainrunningstatus/trainno/12302?startDate={today_hyphen}",
    f"https://www.confirmtkt.com/api/platform/trainrunningstatus/trainno/12302?startDate={today_ddmmyyyy}",
    f"https://vt.confirmtkt.com/api/trains/runningstatus?trainNo=12302",
    f"https://railradar.in/api/v1/trains/12302/live",
    f"https://api.railyatri.in/api/live_train_status.json?train_number=12302",
    f"https://erail.in/rail/getLiveTrainStatus.aspx?train=12302"
]

for url in endpoints:
    try:
        r = requests.get(url, headers=headers, timeout=4)
        print(f"URL: {url} | Status: {r.status_code}")
        if r.status_code == 200:
            print("Response snippet:", r.text[:300])
            print("-" * 50)
    except Exception as e:
        print(f"URL: {url} | Error: {e}")
