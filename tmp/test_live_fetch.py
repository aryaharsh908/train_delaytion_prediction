import requests
import json

def test_confirmtkt(train_no):
    url = f"https://www.confirmtkt.com/api/platform/trainrunningstatus/trainno/{train_no}?startDate=2026-08-23"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*"
    }
    try:
        r = requests.get(url, headers=headers, timeout=5)
        print(f"ConfirmTkt status code for {train_no}:", r.status_code)
        if r.status_code == 200:
            data = r.json()
            print("Current station:", data.get("CurrentStationName"))
            print("Delay minutes:", data.get("Delay"))
            print("Status msg:", data.get("Status"))
            return data
    except Exception as e:
        print("Confirmtkt error:", e)
    return None

def test_erail(train_no):
    url = f"https://erail.in/rail/getLiveTrainStatus.aspx?train={train_no}&date=23-08-2026"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    try:
        r = requests.get(url, headers=headers, timeout=5)
        print(f"eRail status code for {train_no}:", r.status_code)
        print("eRail response snippet:", r.text[:200])
    except Exception as e:
        print("eRail error:", e)

test_confirmtkt("12302")
test_erail("12302")
