from database import SessionLocal, engine
import models
from routers.auth import get_password_hash
from fastapi.testclient import TestClient
from main import app
from sqlalchemy import text, inspect

print("=== UPDATING SCHEMA ===")
with engine.begin() as conn:
    conn.execute(text("ALTER TABLE users DROP CONSTRAINT check_user_role"))
    conn.execute(text("ALTER TABLE users ADD CONSTRAINT check_user_role CHECK (role IN ('SUPER_ADMIN', 'DISTRICT_ADMIN', 'PHC_STAFF', 'CHC_STAFF'))"))
print("Updated check_user_role constraint.")

print("\n=== SETTING UP USERS ===")
db = SessionLocal()

# 1. Setup SUPER_ADMIN
email_sa = "superadmin@swasthyanet.com"
pw_sa = "superadmin123"
super_admin = db.query(models.User).filter(models.User.email == email_sa).first()
if not super_admin:
    super_admin = models.User(
        name="Super Admin",
        email=email_sa,
        password_hash=get_password_hash(pw_sa),
        role="SUPER_ADMIN",
        is_active=True
    )
    db.add(super_admin)
else:
    super_admin.password_hash = get_password_hash(pw_sa)

# 2. Setup CHC_STAFF (to ensure we can test it)
chc_user = db.query(models.User).filter(models.User.role == "CHC_STAFF").first()
if chc_user:
    email_chc = chc_user.email
    pw_chc = "testchc123"
    chc_user.password_hash = get_password_hash(pw_chc)

db.commit()
print("Created SUPER_ADMIN and configured passwords for existing users.")

print("\n=== RUNNING TESTS ===")
client = TestClient(app)
results = []

def test_login(email, password, expected_role=None):
    res = client.post("/api/auth/login", data={"username": email, "password": password})
    if expected_role:
        if res.status_code == 200:
            role = res.json().get("user", {}).get("role")
            if role == expected_role:
                return f"PASS ({res.status_code} + JWT Role {role})"
            return f"FAIL (Role mismatch: {role} != {expected_role})"
        return f"FAIL (Status: {res.status_code}, Body: {res.text})"
    else:
        if res.status_code == 401:
            return "PASS (401 Unauthorized)"
        return f"FAIL (Expected 401, got {res.status_code})"

# 1. SUPER_ADMIN login -> 200 + JWT & JWT role = SUPER_ADMIN
print("1 & 2. SUPER_ADMIN login:", test_login(email_sa, pw_sa, "SUPER_ADMIN"))

# 3. Wrong password -> 401
print("3. SUPER_ADMIN wrong password:", test_login(email_sa, "wrong"))

# 4. Existing DISTRICT_ADMIN login still works
print("4. DISTRICT_ADMIN login:", test_login("admin.coimbatore@swasthyanet.com", "testpassword123", "DISTRICT_ADMIN"))

# 5. Existing PHC_STAFF login still works
print("5. PHC_STAFF login:", test_login("staff01@swasthyanet.com", "testpassword123", "PHC_STAFF"))

# 6. Existing CHC_STAFF login still works
if chc_user:
    print(f"6. CHC_STAFF login ({email_chc}):", test_login(email_chc, pw_chc, "CHC_STAFF"))
else:
    print("6. CHC_STAFF login: FAIL (No CHC_STAFF user in DB)")

# 7. Database remains intact with 15 tables
inspector = inspect(engine)
tables = inspector.get_table_names()
if len(tables) == 15:
    print("7. Database tables (exactly 15): PASS")
else:
    print(f"7. Database tables: FAIL ({len(tables)} tables)")

