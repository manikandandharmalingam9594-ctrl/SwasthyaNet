from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from database import get_db
import models, schemas
from dependencies import get_current_user, RoleChecker, verify_centre_access, verify_district_access

router = APIRouter(prefix="/health-scores", tags=["health_scores"], dependencies=[Depends(RoleChecker(['SUPER_ADMIN', 'DISTRICT_ADMIN']))])

@router.get("", response_model=List[schemas.CentreHealthScore])
def get_health_scores(db: Session = Depends(get_db)):
    return db.query(models.CentreHealthScore).all()
