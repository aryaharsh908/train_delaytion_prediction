import requests
import json
from datetime import datetime

today_hyphen_ddmmyyyy = datetime.now().strftime("%d-%m-%Y")
today_hyphen_yyyymmdd = datetime.now().strftime("%Y-%m-%d")
today_nodash = datetime.now().strftime("%d%m%Y")
today_shortmon = datetime.now().strftime("%d-%b-%Y")

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://www.confirmtkt.com",
    "Referer": "https://www.confirmtkt.com/train-running-status/12302"
}

test_urls = [
    f"https://www.confirmtkt.com/api/platform/trainrunningstatus/trainno/12302?startDate={today_hyphen_ddmmyyyy}",
    f"https://www.confirmtkt.com/api/platform/trainrunningstatus/trainno/12302?startDate={today_nodash}",
    f"https://www.confirmtkt.com/api/platform/trainrunningstatus/trainno/12302?startDate={today_shortmon}",
    f"https://www.trainman.in/services/train/live-status?trainNo=12302&date={today_hyphen_ddmmyyyy}",
    f"https://www.trainman.in/services/train/live-status?trainNo=12302&date={today_hyphen_yyyymmdd}",
    f"https://api.railradar.in/api/v1/trains/12302/live",
    f"https://ntes.co.in/api/live-status/12302",
    f"https://www.ixigo.com/api/v1/trains/live/12302"
]

for u in test_urls:
    try:
        r = requests.get(u, headers=headers, timeout=5)
        print(f"URL: {u} | Status: {r.status_code}")
        if r.status_code == 200:
            print("Response:", r.text[:400])
            print("="*60)
    except Exception as e:
        print(f"Error {u}: {e}")
