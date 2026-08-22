from fastapi.testclient import TestClient
from main import app
import json
import traceback

client = TestClient(app, raise_server_exceptions=True)

endpoints = [
    ("GET", "/api/centres/1/beds", None),
    ("GET", "/api/centres/1/predictions", None),
    ("POST", "/api/attendance", {"doctor_id": 1, "attendance_date": "2026-08-16", "status": "Present"}),
    ("PUT", "/api/inventory/1", {"quantity": 10, "transaction_type": "Restock"}),
    ("PUT", "/api/wards/1/occupancy", {"occupied_beds": 5, "recorded_at": "2026-08-16"}),
    ("POST", "/api/transfers", {"from_centre_id": 1, "to_centre_id": 2, "medicine_id": 1, "quantity": 50, "status": "Pending"}),
    ("PUT", "/api/transfers/1/approve", None),
    ("PUT", "/api/transfers/1/reject", None),
    ("POST", "/api/sync-records", {"centre_id": 1, "sync_status": "Success"})
]

for method, path, data in endpoints:
    print(f"\n--- Testing {method} {path} ---")
    try:
        if method == "GET":
            res = client.get(path)
        elif method == "POST":
            res = client.post(path, json=data)
        elif method == "PUT":
            res = client.put(path, json=data)
        print("Status:", res.status_code)
        print("Response:", res.text)
    except Exception as e:
        print(f"Exception caught for {path}:")
        traceback.print_exc()

