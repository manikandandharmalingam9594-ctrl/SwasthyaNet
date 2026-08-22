from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from database import get_db
import models, schemas
from dependencies import get_current_user, RoleChecker, verify_centre_access, verify_district_access

router = APIRouter(prefix="/wards", tags=["wards"], dependencies=[Depends(get_current_user)])

@router.put("/{ward_id}/occupancy", response_model=schemas.BedOccupancy)
def update_ward_occupancy(ward_id: int, occupancy: schemas.OccupancyUpdate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    ward = db.query(models.Ward).filter(models.Ward.ward_id == ward_id).first()
    if not ward:
        raise HTTPException(status_code=404, detail="Ward not found")
    verify_centre_access(ward.centre_id, user, db)
    
    if occupancy.occupied_beds < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Occupied beds cannot be negative"
        )
        
    # Enforce capacity constraint for normal wards
    is_emergency = ward.ward_name.strip().lower() == "emergency"
    if not is_emergency and occupancy.occupied_beds > ward.total_beds:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Occupied beds ({occupancy.occupied_beds}) cannot exceed total capacity ({ward.total_beds}) for {ward.ward_name} Ward"
        )
        
    # For Emergency ward, cap at max surge limit (150% of total beds)
    if is_emergency and occupancy.occupied_beds > int(ward.total_beds * 1.5):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Occupied beds ({occupancy.occupied_beds}) exceeds maximum emergency overflow limit ({int(ward.total_beds * 1.5)})"
        )
        
    if occupancy.available_beds is None:
        occupancy.available_beds = max(0, ward.total_beds - occupancy.occupied_beds)
        
    recorded_time = occupancy.recorded_at or datetime.utcnow()
    
    new_occ = models.BedOccupancy(
        ward_id=ward_id,
        occupied_beds=occupancy.occupied_beds,
        available_beds=occupancy.available_beds,
        recorded_at=recorded_time
    )
    db.add(new_occ)
    db.commit()
    db.refresh(new_occ)
    return new_occ
