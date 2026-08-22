from database import SessionLocal
import models

db = SessionLocal()
users = db.query(models.User).all()
for u in users[:5]:
    print(f"{u.email}: {u.password_hash}")
