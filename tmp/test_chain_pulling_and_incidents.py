import requests
import json

base_url = "http://localhost:8000/api/v1"

print("--- Testing Chain Pulling (CHAIN_PULLING) Injection ---")
# 1. Inject Chain Pulling
res = requests.post(f"{base_url}/events/inject", json={
    "event_type": "CHAIN_PULLING",
    "section_id": "NDLS-MTJ",
    "train_id": "TRAIN_12951",
    "severity": "CRITICAL"
})
print("Inject Response Status:", res.status_code)
print("Inject Payload:", json.dumps(res.json(), indent=2))

# 2. Check Route Timeline for Train 12951
route_res = requests.get(f"{base_url}/trains/12951/route")
print("\n--- Route Timeline Status Message & Live Location ---")
print("Status Code:", route_res.status_code)
if route_res.status_code == 200:
    data = route_res.json()
    print("Status Message:", data.get("status_message"))
    print("Total Delay:", data.get("total_delay_minutes"), "mins")
    print("Current Station Name:", data.get("current_station_name"))
    print("Route Items (first 4):")
    for item in data.get("route_items", [])[:4]:
        print(f"  - {item['station_code']} ({item['station_name']}): is_current={item.get('is_current_position')} | Live={item.get('live_telemetry_delay_minutes')}m | ML={item.get('ml_predicted_delay_minutes')}m")

# 3. Clear Incidents
clear_res = requests.post(f"{base_url}/events/clear")
print("\nClear Response:", clear_res.status_code, clear_res.json())
