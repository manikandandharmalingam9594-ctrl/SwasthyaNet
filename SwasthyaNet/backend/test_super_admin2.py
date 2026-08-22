from database import SessionLocal, engine
import models
from routers.auth import get_password_hash
from fastapi.testclient import TestClient
from main import app
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError

print("=== SETTING UP SUPER_ADMIN USER ===")
db = SessionLocal()
email = "superadmin@swasthyanet.com"
plain_password = "testpassword123"

# Check if SUPER_ADMIN exists
super_admin = db.query(models.User).filter(models.User.email == email).first()
setup_success = False

if not super_admin:
    super_admin = models.User(
        name="Super Admin",
        email=email,
        password_hash=get_password_hash(plain_password),
        role="SUPER_ADMIN",
        is_active=True
    )
    db.add(super_admin)
    try:
        db.commit()
        print("Created SUPER_ADMIN user.")
        setup_success = True
    except IntegrityError as e:
        print("FAIL (IntegrityError creating SUPER_ADMIN. Likely check constraint check_user_role)")
        db.rollback()
else:
    super_admin.password_hash = get_password_hash(plain_password)
    try:
        db.commit()
        print("Updated existing SUPER_ADMIN user.")
        setup_success = True
    except IntegrityError:
        print("FAIL (IntegrityError updating SUPER_ADMIN)")
        db.rollback()

print("\n=== TESTING SUPER_ADMIN LOGIN ===")
if setup_success:
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
else:
    print("FAIL (Could not test login because user creation failed)")
    print("FAIL (Could not test invalid password because user creation failed)")

# 3. Check table count
print("\n=== VERIFYING TABLE COUNT ===")
inspector = inspect(engine)
tables = inspector.get_table_names()
if len(tables) == 15:
    print("PASS (Database still has exactly 15 tables)")
else:
    print(f"FAIL (Found {len(tables)} tables: {tables})")
