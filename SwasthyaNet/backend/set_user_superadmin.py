from database import SessionLocal
import models
from routers.auth import get_password_hash

def update_superadmin_user():
    db = SessionLocal()
    email = "manikandand9594@gmail.com"
    raw_pwd = "SwasthyaNet"
    hashed = get_password_hash(raw_pwd)

    # Check if this user already exists
    user = db.query(models.User).filter(models.User.email == email).first()
    if user:
        user.role = "SUPER_ADMIN"
        user.password_hash = hashed
        user.is_active = True
        user.is_activated = True
        user.must_change_password = False
        user.district_id = None
        user.centre_id = None
        db.commit()
        print(f"[UPDATED] User {email} is now SUPER_ADMIN with updated password.")
    else:
        # Check if old superadmin@swasthyanet.com exists and update it, or create new
        old_sa = db.query(models.User).filter(models.User.email == "superadmin@swasthyanet.com").first()
        if old_sa:
            old_sa.email = email
            old_sa.password_hash = hashed
            old_sa.name = "Manikandan D"
            old_sa.role = "SUPER_ADMIN"
            old_sa.is_active = True
            old_sa.is_activated = True
            old_sa.must_change_password = False
            db.commit()
            print(f"[TRANSFERRED] Updated superadmin@swasthyanet.com to {email} as SUPER_ADMIN.")
        else:
            new_sa = models.User(
                name="Manikandan D",
                email=email,
                password_hash=hashed,
                role="SUPER_ADMIN",
                is_active=True,
                is_activated=True,
                must_change_password=False
            )
            db.add(new_sa)
            db.commit()
            print(f"[CREATED] Created new SUPER_ADMIN user {email}.")

    db.close()

if __name__ == "__main__":
    update_superadmin_user()
