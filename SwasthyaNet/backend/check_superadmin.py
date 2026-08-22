from database import SessionLocal
import models
db = SessionLocal()
users = db.query(models.User).filter(models.User.role == "SUPER_ADMIN").all()
for u in users:
    print(u.email, u.password_hash)
