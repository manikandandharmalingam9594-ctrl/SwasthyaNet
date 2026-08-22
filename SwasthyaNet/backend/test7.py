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
            print("Parsed district:", parsed.district_id)
        except Exception as e:
            print("Validation error:", e)
except Exception as e:
    print("DB error:", e)

try:
    centres = db.query(models.HealthCentre).all()
    print("Found centres:", len(centres))
    for c in centres:
        try:
            parsed = schemas.HealthCentre.model_validate(c)
            print("Parsed centre:", parsed.centre_id)
        except Exception as e:
            print("Validation error:", e)
except Exception as e:
    print("DB error:", e)

