from fastapi.testclient import TestClient
from main import app
import sys

client = TestClient(app, raise_server_exceptions=True)
try:
    client.post("/api/attendance", json={"doctor_id": 1, "attendance_date": "2026-08-16", "status": "Present"})
except Exception as e:
    print(f"Attendance error: {type(e).__name__}: {str(e)}")
