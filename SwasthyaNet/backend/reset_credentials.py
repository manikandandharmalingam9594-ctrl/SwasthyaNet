from database import SessionLocal
import models
from routers.auth import get_password_hash

def setup_all_default_users():
    db = SessionLocal()
    default_password = "testpassword123"
    hashed = get_password_hash(default_password)
    
    users_to_ensure = [
        {
            "email": "superadmin@swasthyanet.com",
            "name": "Super Administrator",
            "role": "SUPER_ADMIN",
            "district_id": None,
            "centre_id": None
        },
        {
            "email": "admin.coimbatore@swasthyanet.com",
            "name": "Coimbatore District Admin",
            "role": "DISTRICT_ADMIN",
            "district_id": 1,
            "centre_id": None
        },
        {
            "email": "admin.chennai@swasthyanet.com",
            "name": "Chennai District Admin",
            "role": "DISTRICT_ADMIN",
            "district_id": 2,
            "centre_id": None
        },
        {
            "email": "staff01@swasthyanet.com",
            "name": "Staff PHC Anaimalai",
            "role": "PHC_STAFF",
            "district_id": 1,
            "centre_id": 1
        },
        {
            "email": "staff03@swasthyanet.com",
            "name": "Staff CHC Pollachi",
            "role": "CHC_STAFF",
            "district_id": 1,
            "centre_id": 3
        }
    ]

    print("=" * 60)
    print("SWASTHYANET DEFAULT USER CREDENTIALS")
    print("=" * 60)

    for item in users_to_ensure:
        u = db.query(models.User).filter(models.User.email == item["email"]).first()
        if not u:
            u = models.User(
                name=item["name"],
                email=item["email"],
                password_hash=hashed,
                role=item["role"],
                district_id=item["district_id"],
                centre_id=item["centre_id"],
                is_active=True,
                is_activated=True,
                must_change_password=False
            )
            db.add(u)
            db.commit()
            print(f"[CREATED] {item['role']:<15} | Email: {item['email']:<32} | Password: {default_password}")
        else:
            u.password_hash = hashed
            u.is_active = True
            u.is_activated = True
            u.must_change_password = False
            db.commit()
            print(f"[READY]   {item['role']:<15} | Email: {item['email']:<32} | Password: {default_password}")

    print("=" * 60)
    db.close()

if __name__ == "__main__":
    setup_all_default_users()
