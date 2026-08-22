from database import SessionLocal
import models
from routers.auth import get_password_hash
from fastapi.testclient import TestClient
from main import app

print("=== FIXING PHC_STAFF PASSWORD ===")
db = SessionLocal()
phc_user = db.query(models.User).filter(models.User.role == "PHC_STAFF").first()

if not phc_user:
    print("No PHC_STAFF user found in database!")
    exit(1)

email = phc_user.email
plain_password = "testpassword123"

# Update password
phc_user.password_hash = get_password_hash(plain_password)
db.commit()
print(f"Updated password hash for {email}")

print("\n=== TESTING PHC_STAFF LOGIN ===")
client = TestClient(app)

# 1. Valid login
resp1 = client.post("/api/auth/login", data={"username": email, "password": plain_password})
if resp1.status_code == 200:
    data = resp1.json()
    token = data.get("access_token")
    role = data.get("user", {}).get("role")
    if token and role == "PHC_STAFF":
        print("PASS (Valid login: 200 + JWT with role PHC_STAFF)")
    else:
        print(f"FAIL (Valid login response structure unexpected: {data})")
else:
    print(f"FAIL (Valid login status {resp1.status_code}: {resp1.text})")

# 2. Invalid password
resp2 = client.post("/api/auth/login", data={"username": email, "password": "wrongpassword"})
if resp2.status_code == 401:
    print("PASS (Invalid password: 401)")
else:
    print(f"FAIL (Invalid password status {resp2.status_code}: {resp2.text})")
