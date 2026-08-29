import requests

trains = ["12951", "12302", "12626", "12002", "12424", "12622", "12724", "12260"]
for t in trains:
    url = f"http://localhost:8000/api/v1/trains/{t}/route"
    try:
        r = requests.get(url, timeout=5)
        print(f"Train {t}: Status {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            print(f"  Name: {data.get('train_name')} | Status: {data.get('status_message')} | Items: {len(data.get('route_items', []))}")
        else:
            print("  Error response:", r.text[:200])
    except Exception as e:
        print(f"  Exception {t}: {e}")
