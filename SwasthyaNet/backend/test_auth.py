from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

print("--- Testing Valid Credentials ---")
resp = client.post("/api/auth/login", data={"username": "admin.coimbatore@swasthyanet.com", "password": "testpassword123"})
print(f"Status: {resp.status_code}")
if resp.status_code == 200:
    data = resp.json()
    print("Token received:", data.get("access_token")[:20] + "...")
    print("User returned:", data.get("user")['email'], data.get("user")['role'])
else:
    print(resp.text)

print("\n--- Testing Invalid Credentials ---")
resp2 = client.post("/api/auth/login", data={"username": "admin.coimbatore@swasthyanet.com", "password": "wrongpassword"})
print(f"Status: {resp2.status_code}")
print("Response:", resp2.text)
