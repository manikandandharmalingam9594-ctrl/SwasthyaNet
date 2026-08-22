from fastapi.testclient import TestClient
from main import app
from database import engine, SessionLocal
import models
from sqlalchemy import inspect
import jwt
import traceback

client = TestClient(app)

print("=== VERIFICATION REPORT ===")

# Test 1: Valid District Admin login
print("\nTest 1: Valid District Admin login -> 200 + JWT")
resp1 = client.post("/api/auth/login", data={"username": "admin.coimbatore@swasthyanet.com", "password": "testpassword123"})
if resp1.status_code == 200 and "access_token" in resp1.json():
    print("PASS")
    token = resp1.json()["access_token"]
    user_data = resp1.json()["user"]
else:
    print(f"FAIL (Status: {resp1.status_code}, Body: {resp1.text})")
    token = None
    user_data = {}

# Test 2: Invalid password
print("\nTest 2: Invalid password -> 401")
resp2 = client.post("/api/auth/login", data={"username": "admin.coimbatore@swasthyanet.com", "password": "wrong"})
if resp2.status_code == 401:
    print("PASS")
else:
    print(f"FAIL (Status: {resp2.status_code})")

# Test 3: Unknown email
print("\nTest 3: Unknown email -> 401")
resp3 = client.post("/api/auth/login", data={"username": "nobody@swasthyanet.com", "password": "wrong"})
if resp3.status_code == 401:
    print("PASS")
else:
    print(f"FAIL (Status: {resp3.status_code})")

# Test 4: JWT contains user_id, email and role
print("\nTest 4: JWT contains user_id, email and role")
if token:
    try:
        decoded = jwt.decode(token, options={"verify_signature": False})
        if "user_id" in decoded and "sub" in decoded and "role" in decoded:
            print("PASS")
        else:
            print(f"FAIL (Decoded: {decoded})")
    except Exception as e:
        print(f"FAIL (Decode error: {e})")
else:
    print("FAIL (No token from Test 1)")

# Test 5: password_hash is never returned
print("\nTest 5: password_hash is never returned")
if "password_hash" not in user_data and "password" not in user_data and resp1.status_code == 200:
    print("PASS")
else:
    print("FAIL")

# Test 6: Test existing PHC_STAFF user
print("\nTest 6: Test existing PHC_STAFF user")
db = SessionLocal()
phc_user = db.query(models.User).filter(models.User.role == "PHC_STAFF").first()
if phc_user:
    try:
        resp6 = client.post("/api/auth/login", data={"username": phc_user.email, "password": "any"})
        if resp6.status_code == 200:
            print("PASS (Logged in)")
        else:
            print(f"FAIL (Status {resp6.status_code}, Expected 200, Body: {resp6.text})")
    except Exception as e:
        print("FAIL (Exception thrown:", type(e).__name__, ")")
else:
    print("FAIL (No PHC_STAFF user found)")

# Test 7: Test existing SUPER_ADMIN user
print("\nTest 7: Test existing SUPER_ADMIN user")
super_admin = db.query(models.User).filter(models.User.role == "SUPER_ADMIN").first()
if super_admin:
    try:
        resp7 = client.post("/api/auth/login", data={"username": super_admin.email, "password": "any"})
        print(f"FAIL/PASS based on result (Status {resp7.status_code})")
    except Exception as e:
        print("FAIL (Exception thrown)")
else:
    print("FAIL (No SUPER_ADMIN user found in DB)")

# Test 8: Verify the database still has exactly 15 tables
print("\nTest 8: Verify the database still has exactly 15 tables")
inspector = inspect(engine)
tables = inspector.get_table_names()
if len(tables) == 15:
    print("PASS")
else:
    print(f"FAIL (Found {len(tables)} tables: {tables})")
