from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime, date

class DistrictBase(BaseModel):
    district_name: str
    state: str

class District(DistrictBase):
    district_id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class HealthCentreBase(BaseModel):
    centre_name: str
    centre_type: str
    district_id: int
    block: Optional[str] = None
    village_town: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    phone: Optional[str] = None
    total_beds: Optional[int] = None
    status: Optional[str] = None

class HealthCentre(HealthCentreBase):
    centre_id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class WardBase(BaseModel):
    ward_name: str
    centre_id: int
    total_beds: int

class Ward(WardBase):
    ward_id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class DoctorBase(BaseModel):
    centre_id: int
    doctor_name: str
    specialization: str
    employment_status: Optional[str] = None

class Doctor(DoctorBase):
    doctor_id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class DoctorAttendanceBase(BaseModel):
    doctor_id: int
    attendance_date: date
    check_in: Optional[datetime] = None
    check_out: Optional[datetime] = None
    status: str

class DoctorAttendanceCreate(DoctorAttendanceBase):
    pass

class DoctorAttendance(DoctorAttendanceBase):
    attendance_id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class MedicineBase(BaseModel):
    medicine_name: str
    category: Optional[str] = None
    unit: Optional[str] = None

class Medicine(MedicineBase):
    medicine_id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class MedicineInventoryBase(BaseModel):
    centre_id: int
    medicine_id: int
    current_stock: int
    minimum_stock: Optional[int] = 0
    maximum_stock: Optional[int] = None

class MedicineInventory(MedicineInventoryBase):
    inventory_id: int
    last_updated: datetime
    model_config = ConfigDict(from_attributes=True)

class InventoryUpdate(BaseModel):
    quantity: int
    transaction_type: str

class MedicineStockHistoryBase(BaseModel):
    centre_id: int
    medicine_id: int
    quantity: int
    transaction_type: str

class MedicineStockHistory(MedicineStockHistoryBase):
    history_id: int
    recorded_at: datetime
    model_config = ConfigDict(from_attributes=True)

class BedOccupancyBase(BaseModel):
    ward_id: int
    occupied_beds: int
    available_beds: Optional[int] = None
    recorded_at: datetime

class OccupancyUpdate(BaseModel):
    occupied_beds: int
    available_beds: Optional[int] = None
    recorded_at: Optional[datetime] = None

class BedOccupancy(BedOccupancyBase):
    occupancy_id: int
    model_config = ConfigDict(from_attributes=True)

class AlertBase(BaseModel):
    centre_id: int
    alert_type: str
    severity: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None

class Alert(AlertBase):
    alert_id: int
    created_at: datetime
    resolved_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class AIPredictionBase(BaseModel):
    centre_id: int
    prediction_type: str
    target_id: Optional[int] = None
    predicted_value: Optional[float] = None
    prediction_date: Optional[date] = None
    confidence: Optional[float] = None
    explanation: Optional[str] = None

class AIPrediction(AIPredictionBase):
    prediction_id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class CentreHealthScoreBase(BaseModel):
    centre_id: int
    score: float
    status: Optional[str] = None
    explanation: Optional[str] = None

class CentreHealthScore(CentreHealthScoreBase):
    score_id: int
    calculated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class MedicineTransferBase(BaseModel):
    from_centre_id: int
    to_centre_id: int
    medicine_id: int
    quantity: int
    estimated_distance_km: Optional[float] = None
    estimated_travel_minutes: Optional[int] = None
    status: str

class TransferCreate(BaseModel):
    from_centre_id: int
    to_centre_id: int
    medicine_id: int
    quantity: int
    estimated_distance_km: Optional[float] = None
    estimated_travel_minutes: Optional[int] = None

class MedicineTransfer(MedicineTransferBase):
    transfer_id: int
    requested_at: datetime
    approved_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class SyncRecordBase(BaseModel):
    centre_id: int
    device_id: Optional[str] = None
    data_type: Optional[str] = None
    local_record_id: Optional[str] = None
    sync_status: str

class SyncRecordCreate(SyncRecordBase):
    pass

class SyncRecord(SyncRecordBase):
    sync_id: int
    created_at: datetime
    synced_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class UserBase(BaseModel):
    name: str
    email: str
    role: str
    centre_id: Optional[int] = None
    language: Optional[str] = None
    is_active: Optional[bool] = True
    district_id: Optional[int] = None

class UserCreate(BaseModel):
    name: str
    email: str
    password: str
    role: str
    centre_id: Optional[int] = None
    district_id: Optional[int] = None
    language: Optional[str] = "en"
    is_active: Optional[bool] = True

class UserStatusUpdate(BaseModel):
    is_active: bool

class User(UserBase):
    user_id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
    
class Token(BaseModel):
    access_token: str
    token_type: str
    user: User
