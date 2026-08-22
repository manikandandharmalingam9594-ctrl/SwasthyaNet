from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
import models, schemas
from dependencies import get_current_user, RoleChecker, verify_centre_access, verify_district_access

router = APIRouter(prefix="/medicines", tags=["medicines"], dependencies=[Depends(get_current_user)])

@router.get("", response_model=List[schemas.Medicine])
def get_medicines(db: Session = Depends(get_db)):
    return db.query(models.Medicine).all()

@router.get("/{medicine_id}", response_model=schemas.Medicine)
def get_medicine(medicine_id: int, db: Session = Depends(get_db)):
    medicine = db.query(models.Medicine).filter(models.Medicine.medicine_id == medicine_id).first()
    if not medicine:
        raise HTTPException(status_code=404, detail="Medicine not found")
    return medicine
