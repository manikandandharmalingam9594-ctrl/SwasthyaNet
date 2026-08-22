from fastapi.testclient import TestClient
from main import app
import sys

# We need httpx to use TestClient. Let's just install httpx quickly inside the venv if missing
import subprocess
try:
    import httpx
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "httpx"])
    
try:
    client = TestClient(app)
    response = client.get("/api/districts")
    print(response.status_code)
    print("SUCCESS")
except Exception as e:
    import traceback
    traceback.print_exc()
