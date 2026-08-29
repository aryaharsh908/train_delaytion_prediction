import requests
import json

base_url = "http://localhost:8000/api/v1"

print("================ COMPREHENSIVE SYSTEM VERIFICATION ================")

# 1. Check Train Route & Exact Location Pointer
print("\n[1] Checking Train 12951 Route & Exact Location Pointer:")
res = requests.get(f"{base_url}/trains/12951/route")
print("    HTTP Status:", res.status_code)
if res.status_code == 200:
    data = res.json()
    print("    Train Name:", data.get("train_name"))
    print("    Current Station Name:", data.get("current_station_name"))
    print("    Total Delay:", data.get("total_delay_minutes"), "mins")
    print("    Status Message:", data.get("status_message"))
    for item in data.get("route_items", []):
        if item.get("is_current_position"):
            print(f"    📍 EXACT LOCATION POINTER AT: {item['station_code']} ({item['station_name']}) - is_current_position=True")

# 2. Test Chain Pulling Injection Near Station vs Mid-Route
print("\n[2] Testing Alarm Chain Pulling (CHAIN_PULLING) Injection:")
inject_res = requests.post(f"{base_url}/events/inject", json={
    "event_type": "CHAIN_PULLING",
    "section_id": "NDLS-MTJ",
    "train_id": "TRAIN_12951",
    "severity": "CRITICAL"
})
print("    Injection HTTP Status:", inject_res.status_code)

res_post_cp = requests.get(f"{base_url}/trains/12951/route")
if res_post_cp.status_code == 200:
    data_cp = res_post_cp.json()
    print("    Updated Status Message:", data_cp.get("status_message"))
    print("    Updated Delay:", data_cp.get("total_delay_minutes"), "mins")

# 3. Clear Incidents
requests.post(f"{base_url}/events/clear")
print("\n[3] Cleared all incidents successfully!")
print("===================================================================")
