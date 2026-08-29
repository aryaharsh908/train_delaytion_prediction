import requests
import re
import json

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

url = "https://www.confirmtkt.com/train-running-status/12302"
r = requests.get(url, headers=headers, timeout=10)

pos = r.text.find("data = {")
if pos != -1:
    end_pos = r.text.find("</script>", pos)
    script_str = r.text[pos + 7 : end_pos].strip()
    # Remove trailing semicolon if present
    if script_str.endswith(";"):
        script_str = script_str[:-1]
    
    try:
        data = json.loads(script_str)
        print("KEYS:", list(data.keys()))
        print("TrainName:", data.get("TrainName"))
        print("CurrentStationName:", data.get("CurrentStationName"))
        print("Delay:", data.get("Delay"))
        print("Status:", data.get("Status"))
        print("CurrentDelay:", data.get("CurrentDelay"))
        print("Schedule length:", len(data.get("Schedule", [])))
        if data.get("Schedule"):
            print("First station:", data.get("Schedule")[0])
            print("Current / Last passed station:", data.get("CurrentStationCode"))
    except Exception as e:
        print("JSON parse error:", e)
        print("String snippet:", script_str[:500])
else:
    print("data = { not found")
