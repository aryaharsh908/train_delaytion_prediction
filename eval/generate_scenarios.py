"""
Generate 30 evaluation benchmark scenarios in eval/scenarios/
Covering:
- single_junction_conflict (1-8)
- multi_train_cascade (9-15)
- platform_congestion (16-21)
- weather_fog_restriction (22-26)
- sensor_dropout (27-30)
"""

import json
from pathlib import Path

SCENARIOS_DIR = Path(__file__).resolve().parent / "scenarios"
SCENARIOS_DIR.mkdir(parents=True, exist_ok=True)

JUNCTIONS = ["MTJ", "KOTA", "RTM", "BRC", "BSR"]
TRAIN_POOLS = [
    ("12951", "Mumbai Rajdhani", 1),
    ("12952", "Delhi Rajdhani", 1),
    ("12002", "Bhopal Shatabdi", 1),
    ("22436", "Vande Bharat Express", 1),
    ("12953", "August Kranti Rajdhani", 1),
    ("12414", "Pooja Superfast", 2),
    ("12909", "Garib Rath Express", 2),
    ("12925", "Paschim Express", 2),
    ("09001", "Bandra Special", 3),
    ("09002", "Surat Container Goods", 4)
]

def generate_all_30():
    scenarios = []

    # 1. Single junction conflicts (1 to 8)
    for i in range(1, 9):
        junc = JUNCTIONS[(i - 1) % len(JUNCTIONS)]
        t1 = TRAIN_POOLS[(i - 1) % len(TRAIN_POOLS)]
        t2 = TRAIN_POOLS[(i + 3) % len(TRAIN_POOLS)]
        scenarios.append({
            "id": f"scenario_{i:02d}",
            "category": "single_junction_conflict",
            "title": f"Converging Precedence at {junc} ({t1[0]} vs {t2[0]})",
            "junction": junc,
            "trains": [
                {"id": t1[0], "name": t1[1], "priority": t1[2], "distance_km": 12.0 + i, "delay_min": 10.0, "speed_kmh": 110},
                {"id": t2[0], "name": t2[1], "priority": t2[2], "distance_km": 15.0 + i, "delay_min": 5.0, "speed_kmh": 90}
            ],
            "weather": "CLEAR",
            "active_block": f"{junc}_DN_MAIN",
            "description": f"Converging approach at {junc}: high priority {t1[1]} ({t1[0]}) trailing behind {t2[1]} ({t2[0]})."
        })

    # 2. Multi-train cascades (9 to 15)
    for i in range(9, 16):
        junc = JUNCTIONS[(i - 9) % len(JUNCTIONS)]
        t1 = TRAIN_POOLS[(i) % len(TRAIN_POOLS)]
        t2 = TRAIN_POOLS[(i + 1) % len(TRAIN_POOLS)]
        t3 = TRAIN_POOLS[(i + 2) % len(TRAIN_POOLS)]
        scenarios.append({
            "id": f"scenario_{i:02d}",
            "category": "multi_train_cascade",
            "title": f"Three-Train Cascading Bottleneck near {junc}",
            "junction": junc,
            "trains": [
                {"id": t1[0], "name": t1[1], "priority": t1[2], "distance_km": 8.0, "delay_min": 25.0, "speed_kmh": 60},
                {"id": t2[0], "name": t2[1], "priority": t2[2], "distance_km": 16.0, "delay_min": 12.0, "speed_kmh": 85},
                {"id": t3[0], "name": t3[1], "priority": t3[2], "distance_km": 24.0, "delay_min": 4.0, "speed_kmh": 110}
            ],
            "weather": "CLEAR",
            "active_block": f"{junc}_UP_THROUGH",
            "description": f"Delay cascade at {junc}: leading delayed train causes compounding headway penalties on two following expresses."
        })

    # 3. Platform congestion (16 to 21)
    for i in range(16, 22):
        junc = JUNCTIONS[(i - 16) % len(JUNCTIONS)]
        t1 = TRAIN_POOLS[(i) % len(TRAIN_POOLS)]
        t2 = TRAIN_POOLS[(i + 2) % len(TRAIN_POOLS)]
        t3 = TRAIN_POOLS[(i + 4) % len(TRAIN_POOLS)]
        scenarios.append({
            "id": f"scenario_{i:02d}",
            "category": "platform_congestion",
            "title": f"Platform Occupancy Deficit at {junc}",
            "junction": junc,
            "available_platforms": 2,
            "trains": [
                {"id": t1[0], "name": t1[1], "priority": t1[2], "platform_assigned": "1", "dwell_remaining_min": 8.0},
                {"id": t2[0], "name": t2[1], "priority": t2[2], "platform_assigned": "2", "dwell_remaining_min": 6.0},
                {"id": t3[0], "name": t3[1], "priority": t3[2], "approaching_distance_km": 5.0, "speed_kmh": 50}
            ],
            "weather": "CLEAR",
            "active_block": f"{junc}_STATION_YARD",
            "description": f"All station platforms occupied at {junc} with incoming express requiring regulation or holding at home signal."
        })

    # 4. Weather fog delay (22 to 26)
    for i in range(22, 27):
        junc = JUNCTIONS[(i - 22) % len(JUNCTIONS)]
        t1 = TRAIN_POOLS[(i) % len(TRAIN_POOLS)]
        t2 = TRAIN_POOLS[(i + 1) % len(TRAIN_POOLS)]
        scenarios.append({
            "id": f"scenario_{i:02d}",
            "category": "weather_fog_restriction",
            "title": f"Dense Fog Caution Working at {junc}",
            "junction": junc,
            "weather": "DENSE_FOG",
            "visibility_meters": 120,
            "max_fog_speed_kmh": 60.0,
            "trains": [
                {"id": t1[0], "name": t1[1], "priority": t1[2], "speed_kmh": 60, "delay_min": 35.0},
                {"id": t2[0], "name": t2[1], "priority": t2[2], "speed_kmh": 60, "delay_min": 28.0}
            ],
            "active_block": f"{junc}_FOG_ZONE",
            "description": f"Severe visibility reduction (120m) near {junc}. Headway margin expanded to 12 minutes under rule HEAD-04."
        })

    # 5. Missing data / sensor dropouts (27 to 30)
    for i in range(27, 31):
        junc = JUNCTIONS[(i - 27) % len(JUNCTIONS)]
        t1 = TRAIN_POOLS[(i) % len(TRAIN_POOLS)]
        scenarios.append({
            "id": f"scenario_{i:02d}",
            "category": "sensor_dropout",
            "title": f"Track Circuit Intermittent Dropout near {junc}",
            "junction": junc,
            "sensor_status": "INTERMITTENT_DROPOUT",
            "trains": [
                {"id": t1[0], "name": t1[1], "priority": t1[2], "last_known_station": junc, "telemetry_delay_seconds": 180}
            ],
            "active_block": f"{junc}_AXLE_COUNTER_FAULT",
            "description": f"Axle counter failure on approach to {junc}. Dispatcher must verify block clearance before granting line clear."
        })

    for s in scenarios:
        fpath = SCENARIOS_DIR / f"{s['id']}.json"
        fpath.write_text(json.dumps(s, indent=2), encoding="utf-8")

    print(f"Generated {len(scenarios)} benchmark scenario files in {SCENARIOS_DIR}")

if __name__ == "__main__":
    generate_all_30()
