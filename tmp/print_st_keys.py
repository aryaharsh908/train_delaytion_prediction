import requests
import json

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
        sch = data.get("Schedule", [])
        if sch:
            print("Station Item Keys:", list(sch[0].keys()))
            print("\nStation 0 sample:", json.dumps(sch[0], indent=2))
            print("\nStation 1 sample:", json.dumps(sch[1], indent=2))
