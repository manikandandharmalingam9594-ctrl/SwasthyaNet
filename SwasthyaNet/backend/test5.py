import sys
from database import SessionLocal
import models
import schemas
db = SessionLocal()
try:
    districts = db.query(models.District).all()
    print("Found districts:", len(districts))
    for d in districts:
        try:
            parsed = schemas.District.model_validate(d)
            print("Parsed:", parsed)
        except Exception as e:
            print("Validation error:", e)
except Exception as e:
    print("DB error:", e)
