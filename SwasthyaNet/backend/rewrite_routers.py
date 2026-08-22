import os

routers_dir = r"e:\swaai\SwasthyaNet\backend\routers"
os.makedirs(routers_dir, exist_ok=True)

files = {
    "districts.py": """from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
import models, schemas

router = APIRouter(prefix="/districts", tags=["districts"])

@router.get("", response_model=List[schemas.District])
def get_districts(db: Session = Depends(get_db)):
    return db.query(models.District).all()

@router.get("/{district_id}", response_model=schemas.District)
def get_district(district_id: int, db: Session = Depends(get_db)):
    district = db.query(models.District).filter(models.District.district_id == district_id).first()
    if not district:
        raise HTTPException(status_code=404, detail="District not found")
    return district
""",

    "centres.py": """from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
import models, schemas

router = APIRouter(prefix="/centres", tags=["centres"])

@router.get("", response_model=List[schemas.HealthCentre])
def get_centres(db: Session = Depends(get_db)):
    return db.query(models.HealthCentre).all()

@router.get("/{centre_id}", response_model=schemas.HealthCentre)
def get_centre(centre_id: int, db: Session = Depends(get_db)):
    centre = db.query(models.HealthCentre).filter(models.HealthCentre.centre_id == centre_id).first()
    if not centre:
        raise HTTPException(status_code=404, detail="Centre not found")
    return centre

@router.get("/{centre_id}/wards", response_model=List[schemas.Ward])
def get_centre_wards(centre_id: int, db: Session = Depends(get_db)):
    return db.query(models.Ward).filter(models.Ward.centre_id == centre_id).all()

@router.get("/{centre_id}/beds", response_model=List[schemas.BedOccupancy])
def get_centre_beds(centre_id: int, db: Session = Depends(get_db)):
    wards = db.query(models.Ward.ward_id).filter(models.Ward.centre_id == centre_id).subquery()
    return db.query(models.BedOccupancy).filter(models.BedOccupancy.ward_id.in_(wards)).all()

@router.get("/{centre_id}/doctors", response_model=List[schemas.Doctor])
def get_centre_doctors(centre_id: int, db: Session = Depends(get_db)):
    return db.query(models.Doctor).filter(models.Doctor.centre_id == centre_id).all()

@router.get("/{centre_id}/attendance", response_model=List[schemas.DoctorAttendance])
def get_centre_attendance(centre_id: int, db: Session = Depends(get_db)):
    doctors = db.query(models.Doctor.doctor_id).filter(models.Doctor.centre_id == centre_id).subquery()
    return db.query(models.DoctorAttendance).filter(models.DoctorAttendance.doctor_id.in_(doctors)).all()

@router.get("/{centre_id}/inventory", response_model=List[schemas.MedicineInventory])
def get_centre_inventory(centre_id: int, db: Session = Depends(get_db)):
    return db.query(models.MedicineInventory).filter(models.MedicineInventory.centre_id == centre_id).all()

@router.get("/{centre_id}/stock-history", response_model=List[schemas.MedicineStockHistory])
def get_centre_stock_history(centre_id: int, db: Session = Depends(get_db)):
    return db.query(models.MedicineStockHistory).filter(models.MedicineStockHistory.centre_id == centre_id).all()

@router.get("/{centre_id}/alerts", response_model=List[schemas.Alert])
def get_centre_alerts(centre_id: int, db: Session = Depends(get_db)):
    return db.query(models.Alert).filter(models.Alert.centre_id == centre_id).all()

@router.get("/{centre_id}/health-score", response_model=List[schemas.CentreHealthScore])
def get_centre_health_scores(centre_id: int, db: Session = Depends(get_db)):
    return db.query(models.CentreHealthScore).filter(models.CentreHealthScore.centre_id == centre_id).all()

@router.get("/{centre_id}/predictions", response_model=List[schemas.AIPrediction])
def get_centre_predictions(centre_id: int, db: Session = Depends(get_db)):
    return db.query(models.AIPrediction).filter(models.AIPrediction.centre_id == centre_id).all()

@router.get("/{centre_id}/sync-records", response_model=List[schemas.SyncRecord])
def get_centre_sync_records(centre_id: int, db: Session = Depends(get_db)):
    return db.query(models.SyncRecord).filter(models.SyncRecord.centre_id == centre_id).all()
""",

    "wards.py": """from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models, schemas

router = APIRouter(prefix="/wards", tags=["wards"])

@router.put("/{ward_id}/occupancy", response_model=schemas.BedOccupancy)
def update_ward_occupancy(ward_id: int, occupancy: schemas.OccupancyUpdate, db: Session = Depends(get_db)):
    ward = db.query(models.Ward).filter(models.Ward.ward_id == ward_id).first()
    if not ward:
        raise HTTPException(status_code=404, detail="Ward not found")
        
    existing = db.query(models.BedOccupancy).filter(
        models.BedOccupancy.ward_id == ward_id,
        models.BedOccupancy.recorded_at == occupancy.recorded_at
    ).first()
    
    if existing:
        existing.occupied_beds = occupancy.occupied_beds
        if occupancy.available_beds is not None:
            existing.available_beds = occupancy.available_beds
        db.commit()
        db.refresh(existing)
        return existing
    else:
        new_occ = models.BedOccupancy(
            ward_id=ward_id,
            occupied_beds=occupancy.occupied_beds,
            available_beds=occupancy.available_beds,
            recorded_at=occupancy.recorded_at
        )
        db.add(new_occ)
        db.commit()
        db.refresh(new_occ)
        return new_occ
""",

    "doctors.py": """from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models, schemas

router = APIRouter(prefix="/doctors", tags=["doctors"])

@router.get("/{doctor_id}", response_model=schemas.Doctor)
def get_doctor(doctor_id: int, db: Session = Depends(get_db)):
    doctor = db.query(models.Doctor).filter(models.Doctor.doctor_id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return doctor
""",

    "attendance.py": """from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
import models, schemas

router = APIRouter(prefix="/attendance", tags=["attendance"])

@router.post("", response_model=schemas.DoctorAttendance, status_code=201)
def create_attendance(attendance: schemas.DoctorAttendanceCreate, db: Session = Depends(get_db)):
    db_attendance = models.DoctorAttendance(**attendance.model_dump())
    db.add(db_attendance)
    db.commit()
    db.refresh(db_attendance)
    return db_attendance
""",

    "medicines.py": """from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
import models, schemas

router = APIRouter(prefix="/medicines", tags=["medicines"])

@router.get("", response_model=List[schemas.Medicine])
def get_medicines(db: Session = Depends(get_db)):
    return db.query(models.Medicine).all()

@router.get("/{medicine_id}", response_model=schemas.Medicine)
def get_medicine(medicine_id: int, db: Session = Depends(get_db)):
    medicine = db.query(models.Medicine).filter(models.Medicine.medicine_id == medicine_id).first()
    if not medicine:
        raise HTTPException(status_code=404, detail="Medicine not found")
    return medicine
""",

    "inventory.py": """from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models, schemas

router = APIRouter(prefix="/inventory", tags=["inventory"])

@router.put("/{inventory_id}", response_model=schemas.MedicineInventory)
def update_inventory(inventory_id: int, update_data: schemas.InventoryUpdate, db: Session = Depends(get_db)):
    inventory = db.query(models.MedicineInventory).filter(models.MedicineInventory.inventory_id == inventory_id).first()
    if not inventory:
        raise HTTPException(status_code=404, detail="Inventory not found")
    
    try:
        inventory.current_stock += update_data.quantity
        
        history = models.MedicineStockHistory(
            centre_id=inventory.centre_id,
            medicine_id=inventory.medicine_id,
            quantity=update_data.quantity,
            transaction_type=update_data.transaction_type
        )
        db.add(history)
        
        db.commit()
        db.refresh(inventory)
        return inventory
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail="Database transaction failed")
""",

    "alerts.py": """from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from database import get_db
import models, schemas

router = APIRouter(prefix="/alerts", tags=["alerts"])

@router.get("", response_model=List[schemas.Alert])
def get_alerts(db: Session = Depends(get_db)):
    return db.query(models.Alert).all()
""",

    "health_scores.py": """from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from database import get_db
import models, schemas

router = APIRouter(prefix="/health-scores", tags=["health_scores"])

@router.get("", response_model=List[schemas.CentreHealthScore])
def get_health_scores(db: Session = Depends(get_db)):
    return db.query(models.CentreHealthScore).all()
""",

    "transfers.py": """from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
import models, schemas

router = APIRouter(prefix="/transfers", tags=["transfers"])

@router.get("", response_model=List[schemas.MedicineTransfer])
def get_transfers(db: Session = Depends(get_db)):
    return db.query(models.MedicineTransfer).all()

@router.post("", response_model=schemas.MedicineTransfer, status_code=201)
def create_transfer(transfer: schemas.TransferCreate, db: Session = Depends(get_db)):
    db_transfer = models.MedicineTransfer(
        from_centre_id=transfer.from_centre_id,
        to_centre_id=transfer.to_centre_id,
        medicine_id=transfer.medicine_id,
        quantity=transfer.quantity,
        estimated_distance_km=transfer.estimated_distance_km,
        estimated_travel_minutes=transfer.estimated_travel_minutes,
        status="Pending"
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
    
    transfer.status = "Approved"
    db.commit()
    db.refresh(transfer)
    return transfer

@router.put("/{transfer_id}/reject", response_model=schemas.MedicineTransfer)
def reject_transfer(transfer_id: int, db: Session = Depends(get_db)):
    transfer = db.query(models.MedicineTransfer).filter(models.MedicineTransfer.transfer_id == transfer_id).first()
    if not transfer:
        raise HTTPException(status_code=404, detail="Transfer not found")
    
    transfer.status = "Rejected"
    db.commit()
    db.refresh(transfer)
    return transfer
""",

    "sync.py": """from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
import models, schemas

router = APIRouter(prefix="/sync-records", tags=["sync"])

@router.post("", response_model=schemas.SyncRecord, status_code=201)
def create_sync_record(sync_record: schemas.SyncRecordCreate, db: Session = Depends(get_db)):
    db_sync = models.SyncRecord(**sync_record.model_dump())
    db.add(db_sync)
    db.commit()
    db.refresh(db_sync)
    return db_sync
"""
}

for filename, content in files.items():
    with open(os.path.join(routers_dir, filename), "w") as f:
        f.write(content)

print("All routers rewritten.")
