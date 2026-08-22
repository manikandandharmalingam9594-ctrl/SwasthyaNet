from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
import models, schemas
from dependencies import get_current_user, RoleChecker, verify_centre_access, verify_district_access

router = APIRouter(prefix="/sync-records", tags=["sync"])

@router.post("", response_model=schemas.SyncRecord, status_code=201)
def create_sync_record(sync_record: schemas.SyncRecordCreate, db: Session = Depends(get_db)):
    sync_record.sync_status = sync_record.sync_status.upper()
    db_sync = models.SyncRecord(**sync_record.model_dump())
    db.add(db_sync)
    db.commit()
    db.refresh(db_sync)
    return db_sync
