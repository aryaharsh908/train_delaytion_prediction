import os
import glob
import json
from collections import Counter

raw_dir = os.path.abspath(os.path.join(__file__, "../../../data/raw/where_is_my_train"))
files = glob.glob(os.path.join(raw_dir, "**", "*.json"), recursive=True)

dates_by_train = {}
for f in files:
    try:
        with open(f, "r", encoding="utf-8", errors="ignore") as file_obj:
            d = json.load(file_obj)
    except:
        continue
    p = d.get('payload', d)
    dt = p.get('journey_date') or d.get('journey_date')
    tr = p.get('train_number') or d.get('train_number')
    if not dt or not p.get('stations'):
        continue
    k = f"{tr}_{dt}"
    dates_by_train[k] = dates_by_train.get(k, 0) + 1

print(f"Distinct valid train_date keys: {len(dates_by_train)}")
print(list(dates_by_train.items())[:5])
