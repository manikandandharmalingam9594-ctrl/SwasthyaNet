from database import SessionLocal, engine
import models
from routers.auth import get_password_hash
from fastapi.testclient import TestClient
from main import app
from sqlalchemy import inspect

print("=== SETTING UP SUPER_ADMIN USER ===")
db = SessionLocal()
email = "superadmin@swasthyanet.com"
plain_password = "testpassword123"

# Check if SUPER_ADMIN exists
super_admin = db.query(models.User).filter(models.User.email == email).first()

if not super_admin:
    super_admin = models.User(
        name="Super Admin",
        email=email,
        password_hash=get_password_hash(plain_password),
        role="SUPER_ADMIN",
        is_active=True
    )
    db.add(super_admin)
    db.commit()
    print("Created SUPER_ADMIN user.")
else:
    super_admin.password_hash = get_password_hash(plain_password)
    db.commit()
    print("Updated existing SUPER_ADMIN user.")

print("\n=== TESTING SUPER_ADMIN LOGIN ===")
client = TestClient(app)

# 1. Valid login
resp1 = client.post("/api/auth/login", data={"username": email, "password": plain_password})
if resp1.status_code == 200:
    data = resp1.json()
    token = data.get("access_token")
    role = data.get("user", {}).get("role")
    if token and role == "SUPER_ADMIN":
        print("PASS (Valid login: 200 + JWT with role SUPER_ADMIN)")
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

# 3. Check table count
inspector = inspect(engine)
tables = inspector.get_table_names()
if len(tables) == 15:
    print("PASS (Database still has exactly 15 tables)")
else:
    print(f"FAIL (Found {len(tables)} tables: {tables})")
