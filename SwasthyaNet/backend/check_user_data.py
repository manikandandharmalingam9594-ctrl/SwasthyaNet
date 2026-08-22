from database import SessionLocal
import models
db = SessionLocal()
users = db.query(models.User).all()
for u in users:
    if u.role in ["DISTRICT_ADMIN", "PHC_STAFF", "CHC_STAFF"]:
        print(f"{u.email} ({u.role}): centre={u.centre_id}, district={u.district_id}")
