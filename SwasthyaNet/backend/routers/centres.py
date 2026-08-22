from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
import models, schemas
from dependencies import get_current_user, RoleChecker, verify_centre_access, verify_district_access

router = APIRouter(prefix="/centres", tags=["centres"], dependencies=[Depends(get_current_user)])

@router.get("", response_model=List[schemas.HealthCentre])
def get_centres(db: Session = Depends(get_db)):
    return db.query(models.HealthCentre).all()

@router.get("/{centre_id}", response_model=schemas.HealthCentre)
def get_centre(centre_id: int, db: Session = Depends(get_db), user: dict = Depends(verify_centre_access)):
    centre = db.query(models.HealthCentre).filter(models.HealthCentre.centre_id == centre_id).first()
    if not centre:
        raise HTTPException(status_code=404, detail="Centre not found")
    return centre

@router.get("/{centre_id}/wards", response_model=List[schemas.Ward])
def get_centre_wards(centre_id: int, db: Session = Depends(get_db), user: dict = Depends(verify_centre_access)):
    return db.query(models.Ward).filter(models.Ward.centre_id == centre_id).all()

@router.get("/{centre_id}/beds", response_model=List[schemas.BedOccupancy])
def get_centre_beds(centre_id: int, db: Session = Depends(get_db), user: dict = Depends(verify_centre_access)):
    wards = db.query(models.Ward).filter(models.Ward.centre_id == centre_id).all()
    latest_beds = []
    for w in wards:
        latest = db.query(models.BedOccupancy).filter(
            models.BedOccupancy.ward_id == w.ward_id
        ).order_by(models.BedOccupancy.recorded_at.desc(), models.BedOccupancy.occupancy_id.desc()).first()
        if latest:
            latest_beds.append(latest)
    return latest_beds

@router.get("/{centre_id}/doctors", response_model=List[schemas.Doctor])
def get_centre_doctors(centre_id: int, db: Session = Depends(get_db), user: dict = Depends(verify_centre_access)):
    return db.query(models.Doctor).filter(models.Doctor.centre_id == centre_id).all()

@router.get("/{centre_id}/attendance", response_model=List[schemas.DoctorAttendance])
def get_centre_attendance(centre_id: int, db: Session = Depends(get_db), user: dict = Depends(verify_centre_access)):
    doctors = db.query(models.Doctor.doctor_id).filter(models.Doctor.centre_id == centre_id).subquery()
    return db.query(models.DoctorAttendance).filter(models.DoctorAttendance.doctor_id.in_(doctors)).all()

@router.get("/{centre_id}/inventory", response_model=List[schemas.MedicineInventory])
def get_centre_inventory(centre_id: int, db: Session = Depends(get_db), user: dict = Depends(verify_centre_access)):
    return db.query(models.MedicineInventory).filter(models.MedicineInventory.centre_id == centre_id).all()

@router.get("/{centre_id}/stock-history", response_model=List[schemas.MedicineStockHistory])
def get_centre_stock_history(centre_id: int, db: Session = Depends(get_db), user: dict = Depends(verify_centre_access)):
    return db.query(models.MedicineStockHistory).filter(models.MedicineStockHistory.centre_id == centre_id).all()

@router.get("/{centre_id}/alerts", response_model=List[schemas.Alert])
def get_centre_alerts(centre_id: int, db: Session = Depends(get_db), user: dict = Depends(verify_centre_access)):
    return db.query(models.Alert).filter(models.Alert.centre_id == centre_id).all()

@router.get("/{centre_id}/health-score", response_model=List[schemas.CentreHealthScore])
def get_centre_health_scores(centre_id: int, db: Session = Depends(get_db), user: dict = Depends(verify_centre_access)):
    return db.query(models.CentreHealthScore).filter(models.CentreHealthScore.centre_id == centre_id).all()

@router.get("/{centre_id}/predictions", response_model=List[schemas.AIPrediction])
def get_centre_predictions(centre_id: int, db: Session = Depends(get_db), user: dict = Depends(verify_centre_access)):
    return db.query(models.AIPrediction).filter(models.AIPrediction.centre_id == centre_id).all()

@router.get("/{centre_id}/sync-records", response_model=List[schemas.SyncRecord])
def get_centre_sync_records(centre_id: int, db: Session = Depends(get_db), user: dict = Depends(verify_centre_access)):
    return db.query(models.SyncRecord).filter(models.SyncRecord.centre_id == centre_id).all()
