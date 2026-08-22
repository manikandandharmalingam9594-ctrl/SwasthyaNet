from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def get_token(email, pw):
    res = client.post("/api/auth/login", data={"username": email, "password": pw})
    if res.status_code == 200:
        return res.json()["access_token"]
    return None

def test_endpoint(token, method, url, expected_status):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    if method == "GET":
        res = client.get(url, headers=headers)
    elif method == "POST":
        res = client.post(url, headers=headers, json={})
    elif method == "PUT":
        res = client.put(url, headers=headers, json={})
        
    if res.status_code == expected_status:
        print(f"PASS [{expected_status}]: {method} {url}")
    else:
        print(f"FAIL: {method} {url} -> got {res.status_code}, expected {expected_status}. Body: {res.text}")

print("=== VERIFY RBAC ===")
sa_token = get_token("superadmin@swasthyanet.com", "superadmin123")
da_token = get_token("admin.coimbatore@swasthyanet.com", "testpassword123")
phc_token = get_token("staff01@swasthyanet.com", "testpassword123")
chc_token = get_token("staff03@swasthyanet.com", "testchc123")

print("\n--- 1. Unauthenticated ---")
test_endpoint(None, "GET", "/api/centres", 401)
test_endpoint(None, "GET", "/api/districts", 401)

print("\n--- 2. SUPER_ADMIN ---")
test_endpoint(sa_token, "GET", "/api/districts", 200)
test_endpoint(sa_token, "GET", "/api/districts/1", 200)
test_endpoint(sa_token, "GET", "/api/centres/1/inventory", 200)
test_endpoint(sa_token, "GET", "/api/centres/4/inventory", 200)

print("\n--- 3. DISTRICT_ADMIN (District 1) ---")
test_endpoint(da_token, "GET", "/api/districts", 200)
test_endpoint(da_token, "GET", "/api/districts/1", 200)
test_endpoint(da_token, "GET", "/api/districts/2", 403)
test_endpoint(da_token, "GET", "/api/centres/1/inventory", 200)  # Centre 1 is District 1
test_endpoint(da_token, "GET", "/api/centres/4/inventory", 403)  # Centre 4 is District 2

print("\n--- 4. PHC_STAFF (Centre 1) ---")
test_endpoint(phc_token, "GET", "/api/districts", 403)
test_endpoint(phc_token, "GET", "/api/centres/1/inventory", 200)
test_endpoint(phc_token, "GET", "/api/centres/2/inventory", 403)

print("\n--- 5. CHC_STAFF (Centre 3) ---")
test_endpoint(chc_token, "GET", "/api/districts", 403)
test_endpoint(chc_token, "GET", "/api/centres/3/inventory", 200)
test_endpoint(chc_token, "GET", "/api/centres/1/inventory", 403)
