import requests
import time
import datetime
import sys

BASE_URL = "http://localhost:8000/api/v1"

def fetch(url):
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            return r.json()
        print(f"[!] Error fetching {url}: {r.status_code}")
    except Exception as e:
        print(f"[!] Exception calling {url}: {e}")
    return None

def verify_continuously(duration_minutes=2):
    start_time = time.time()
    end_time = start_time + (duration_minutes * 60)
    
    print(f"Starting Continuous Engine Verification for {duration_minutes} minutes...")
    print(f"Expected to match exact real-time IST. Any divergence is a failure.")
    
    cycle = 1
    while time.time() < end_time:
        sys.stdout.write(f"\n--- VERIFICATION CYCLE {cycle} ---\n")
        
        # 1. Fetch trains
        sys.stdout.write("Ping /trains... ")
        trains = fetch(f"{BASE_URL}/trains")
        if trains is None:
            sys.stdout.write("FAIL\n")
            time.sleep(2)
            continue
            
        sys.stdout.write(f"OK. Active Trains in Engine: {len(trains)}\n")
        
        if len(trains) > 0:
            # Check the first train's ETA
            t_id = trains[0].get("train_id")
            sys.stdout.write(f"Ping /trains/{t_id}/eta... ")
            eta = fetch(f"{BASE_URL}/trains/{t_id}/eta")
            if eta:
                sys.stdout.write("OK.\n")
                last_upd = eta.get("last_updated", "")
                print(f"    - Base Timetable ETA: {eta.get('timetable_baseline_eta')}")
                print(f"    - Target Dynamic ETA: {eta.get('dynamic_forecast_eta')}")
                print(f"    - Total Predicted Delay: {eta.get('total_predicted_delay_minutes')} mins")
                print(f"    - Engine Time (last_updated): {last_upd}")
                print(f"    - Confidence: {eta.get('confidence_score')}%")
                
                # Check for garbage values
                try:
                    delay_mins = float(eta.get('total_predicted_delay_minutes', 0))
                    if delay_mins < 0 or delay_mins > 2880:
                        print(f"[!] INSANE DELAY VALUE DETECTED: {delay_mins} minutes")
                except: pass
                
                # Check for crash strings
                if not eta.get('dynamic_forecast_eta'):
                    print(f"[!] ETA GENERATION FAILED (No ETA field string returned)")
                
                try:
                    now_ist = datetime.datetime.now()
                    time_part = last_upd.split(" ")[0]
                    engine_dt = datetime.datetime.strptime(time_part, "%H:%M:%S")
                    engine_dt = now_ist.replace(hour=engine_dt.hour, minute=engine_dt.minute, second=engine_dt.second, microsecond=0)
                    
                    diff_sec = abs((now_ist - engine_dt).total_seconds())
                    if diff_sec > 2:
                        print(f"[!] DIVERGENCE DETECTED: Engine Time {last_upd} vs System Time {now_ist.strftime('%H:%M:%S')} (Diff: {diff_sec}s)")
                        sys.exit(1)
                    else:
                        print(f"    [✓] Time Synchronization Verified (Drift: {diff_sec:.1f}s)")
                except Exception as e:
                    print(f"[!] Error parsing time: {e}")
            else:
                sys.stdout.write("FAIL\n")
                
        print(f"Sleeping 5 seconds before next cycle...\n")
        time.sleep(5)
        cycle += 1
        
    print("\nVerification Loop Complete. If no divergences or crashes reported, Engine runs flawlessly 1:1 with IST.")

if __name__ == "__main__":
    verify_continuously(duration_minutes=0.6)
