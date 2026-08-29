import sys
import os

sys.path.insert(0, r"c:\Users\aryah\train_schedule\backend")

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

try:
    response = client.get("/api/v1/trains/TRAIN_12626/route")
    print("STATUS CODE:", response.status_code)
    if response.status_code == 200:
        print("SUCCESS! Route items count:", len(response.json()["route_items"]))
    else:
        print("RESPONSE ERROR:", response.text)
except Exception as e:
    import traceback
    traceback.print_exc()
