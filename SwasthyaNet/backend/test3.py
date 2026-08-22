from fastapi.testclient import TestClient
from main import app
try:
    client = TestClient(app)
    response = client.get("/api/districts")
    print(response.status_code)
    print(response.text)
except Exception as e:
    import traceback
    traceback.print_exc()
