from database import SessionLocal
import models
from routers.auth import verify_password

db = SessionLocal()
users = db.query(models.User).all()

common_passwords = ["password", "password123", "admin123", "testpassword123", "123456", "staff123", "phc123"]

for u in users:
    print(f"Checking {u.email} ({u.role})")
    found = False
    for p in common_passwords:
        if verify_password(p, u.password_hash):
            print(f"  -> Password is: {p}")
            found = True
            break
    if not found:
        print("  -> Password unknown among common list")
    
    # Just check a few
    if u.user_id > 10:
        break
