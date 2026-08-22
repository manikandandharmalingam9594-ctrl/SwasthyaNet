from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from database import get_db
import models, schemas
from dependencies import get_current_user, RoleChecker, verify_centre_access, verify_district_access

router = APIRouter(prefix="/alerts", tags=["alerts"], dependencies=[Depends(RoleChecker(['SUPER_ADMIN', 'DISTRICT_ADMIN']))])

@router.get("", response_model=List[schemas.Alert])
def get_alerts(db: Session = Depends(get_db)):
    return db.query(models.Alert).all()
