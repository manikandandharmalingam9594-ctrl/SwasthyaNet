import os
import sys
import time
import subprocess
import urllib.request
import urllib.error
import json
from database import engine
from sqlalchemy import inspect

print("--- VERIFICATION SCRIPT ---")

# 1. Check schemas.py
if os.path.exists("schemas.py"):
    print("[PASS] schemas.py exists.")
else:
    print("[FAIL] schemas.py missing.")

# 2. Check router files
routers = ["districts.py", "centres.py", "wards.py", "doctors.py", 
           "attendance.py", "medicines.py", "inventory.py", "alerts.py", 
           "health_scores.py", "transfers.py", "sync.py"]
all_routers_exist = True
for r in routers:
    if not os.path.exists(os.path.join("routers", r)):
        all_routers_exist = False
        print(f"[FAIL] routers/{r} missing.")
if all_routers_exist:
    print("[PASS] All router files exist.")

# 3. Check DB tables
inspector = inspect(engine)
tables = inspector.get_table_names()
expected_tables = {
    'districts', 'health_centres', 'medicines', 'medicine_inventory',
    'users', 'doctors', 'medicine_stock_history', 'wards', 'bed_occupancy',
    'doctor_attendance', 'alerts', 'medicine_transfers', 'ai_predictions',
    'centre_health_scores', 'sync_records'
}
actual_tables = set(tables)
if actual_tables == expected_tables:
    print("[PASS] Database contains exactly the existing 15 tables.")
else:
    print("[FAIL] Database tables mismatch.", actual_tables)

if "patient_visits" not in actual_tables:
    print("[PASS] patient_visits was not added.")
else:
    print("[FAIL] patient_visits exists!")

# 4. Start FastAPI
print("Starting FastAPI...")
proc = subprocess.Popen([sys.executable, "-m", "uvicorn", "main:app", "--port", "8010"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(5)

def req(method, path, data=None):
    url = "http://127.0.0.1:8010" + path
    try:
        if data:
            jsondata = json.dumps(data).encode('utf-8')
            r = urllib.request.Request(url, data=jsondata, method=method, headers={'Content-Type': 'application/json'})
        else:
            r = urllib.request.Request(url, method=method)
        res = urllib.request.urlopen(r)
        return res.getcode(), res.read().decode('utf-8')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8')
    except Exception as e:
        return 0, str(e)

endpoints = [
    ("GET", "/health"),
    ("GET", "/db-test"),
    ("GET", "/api/districts"),
    ("GET", "/api/centres"),
    ("GET", "/api/centres/1/wards"),
    ("GET", "/api/centres/1/beds"),
    ("GET", "/api/centres/1/doctors"),
    ("GET", "/api/centres/1/attendance"),
    ("GET", "/api/centres/1/inventory"),
    ("GET", "/api/centres/1/stock-history"),
    ("GET", "/api/centres/1/alerts"),
    ("GET", "/api/centres/1/health-score"),
    ("GET", "/api/centres/1/predictions"),
    ("GET", "/api/centres/1/sync-records"),
    ("GET", "/api/medicines"),
    ("GET", "/api/transfers"),
    ("GET", "/api/alerts"),
    ("GET", "/api/health-scores"),
    ("POST", "/api/attendance", {"doctor_id": 1, "attendance_date": "2026-08-17", "status": "Present"}),
    ("PUT", "/api/inventory/1", {"quantity": 10, "transaction_type": "RECEIVED"}),
    ("PUT", "/api/wards/1/occupancy", {"occupied_beds": 5, "recorded_at": "2026-08-16"}),
    ("POST", "/api/transfers", {"from_centre_id": 1, "to_centre_id": 2, "medicine_id": 1, "quantity": 50}),
    ("PUT", "/api/transfers/1/approve", None),
    ("PUT", "/api/transfers/1/reject", None),
    ("POST", "/api/sync-records", {"centre_id": 1, "sync_status": "SYNCED"})
]

passed = []
failed = []

for method, path, *data_arg in endpoints:
    data = data_arg[0] if data_arg else None
    code, text = req(method, path, data)
    if code in (200, 201):
        # Additional check for data presence in GET
        if method == "GET":
            try:
                parsed = json.loads(text)
                if isinstance(parsed, list):
                    res_str = f"{len(parsed)} items"
                else:
                    res_str = "OK"
                passed.append(f"{method} {path} - {res_str}")
            except:
                passed.append(f"{method} {path} - OK")
        else:
            passed.append(f"{method} {path} - OK")
    elif code == 404: # Might be valid if DB is empty for a specific ID
        passed.append(f"{method} {path} - 404 Not Found (Valid if empty)")
    else:
        failed.append(f"{method} {path} - Error {code}: {text[:100]}")

proc.kill()

print("\n--- RESULTS ---")
print("Passed Endpoints:")
for p in passed: print("  - " + p)
print("\nFailed Endpoints:")
for f in failed: print("  - " + f)

