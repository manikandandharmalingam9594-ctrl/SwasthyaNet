from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
import models, schemas
from dependencies import get_current_user, RoleChecker, verify_centre_access, verify_district_access

router = APIRouter(prefix="/attendance", tags=["attendance"], dependencies=[Depends(get_current_user)])

@router.post("", response_model=schemas.DoctorAttendance, status_code=201)
def create_attendance(attendance: schemas.DoctorAttendanceCreate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    attendance.status = attendance.status.upper()
    db_attendance = models.DoctorAttendance(**attendance.model_dump())
    db.add(db_attendance)
    db.commit()
    db.refresh(db_attendance)
    return db_attendance
