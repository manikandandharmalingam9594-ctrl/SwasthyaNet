from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
import models, schemas
from dependencies import get_current_user, RoleChecker, verify_centre_access, verify_district_access

router = APIRouter(prefix="/transfers", tags=["transfers"], dependencies=[Depends(get_current_user)])

@router.get("", response_model=List[schemas.MedicineTransfer])
def get_transfers(db: Session = Depends(get_db), user: dict = Depends(RoleChecker(['SUPER_ADMIN', 'DISTRICT_ADMIN']))):
    return db.query(models.MedicineTransfer).all()

@router.post("", response_model=schemas.MedicineTransfer, status_code=201)
def create_transfer(transfer: schemas.TransferCreate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    verify_centre_access(transfer.from_centre_id, user, db)
    db_transfer = models.MedicineTransfer(
        from_centre_id=transfer.from_centre_id,
        to_centre_id=transfer.to_centre_id,
        medicine_id=transfer.medicine_id,
        quantity=transfer.quantity,
        estimated_distance_km=transfer.estimated_distance_km,
        estimated_travel_minutes=transfer.estimated_travel_minutes,
        status="RECOMMENDED"
    )
    db.add(db_transfer)
    db.commit()
    db.refresh(db_transfer)
    return db_transfer

@router.put("/{transfer_id}/approve", response_model=schemas.MedicineTransfer)
def approve_transfer(transfer_id: int, db: Session = Depends(get_db)):
    transfer = db.query(models.MedicineTransfer).filter(models.MedicineTransfer.transfer_id == transfer_id).first()
    if not transfer:
        raise HTTPException(status_code=404, detail="Transfer not found")
    
    transfer.status = "APPROVED"
    db.commit()
    db.refresh(transfer)
    return transfer

@router.put("/{transfer_id}/reject", response_model=schemas.MedicineTransfer)
def reject_transfer(transfer_id: int, db: Session = Depends(get_db)):
    transfer = db.query(models.MedicineTransfer).filter(models.MedicineTransfer.transfer_id == transfer_id).first()
    if not transfer:
        raise HTTPException(status_code=404, detail="Transfer not found")
    
    transfer.status = "CANCELLED"
    db.commit()
    db.refresh(transfer)
    return transfer
