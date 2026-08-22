from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
import models, schemas
from dependencies import get_current_user, RoleChecker, verify_centre_access, verify_district_access

router = APIRouter(
    prefix="/districts", 
    tags=["districts"], 
    dependencies=[Depends(RoleChecker(["SUPER_ADMIN", "DISTRICT_ADMIN"]))]
)

@router.get("", response_model=List[schemas.District])
def get_districts(db: Session = Depends(get_db)):
    return db.query(models.District).all()

@router.get("/{district_id}", response_model=schemas.District)
def get_district(district_id: int, db: Session = Depends(get_db), user: dict = Depends(verify_district_access)):
    district = db.query(models.District).filter(models.District.district_id == district_id).first()
    if not district:
        raise HTTPException(status_code=404, detail="District not found")
    return district
