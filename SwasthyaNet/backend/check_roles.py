from database import SessionLocal
import models
db = SessionLocal()
users = db.query(models.User).all()
roles = set([u.role for u in users])
print("Distinct roles in DB:", roles)
