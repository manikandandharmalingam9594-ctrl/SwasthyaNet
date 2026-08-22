from fastapi.testclient import TestClient
from main import app
import sys

client = TestClient(app, raise_server_exceptions=True)
try:
    client.post("/api/sync-records", json={"centre_id": 1, "sync_status": "Success"})
except Exception as e:
    print(f"Sync error: {type(e).__name__}: {str(e)}")

try:
    client.put("/api/inventory/1", json={"quantity": 10, "transaction_type": "Restock"})
except Exception as e:
    print(f"Inventory error: {type(e).__name__}: {str(e)}")
