from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Date, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class District(Base):
    __tablename__ = "districts"
    district_id = Column(Integer, primary_key=True, index=True)
    district_name = Column(String, index=True, nullable=False)
    state = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    health_centres = relationship("HealthCentre", back_populates="district")

class HealthCentre(Base):
    __tablename__ = "health_centres"
    centre_id = Column(Integer, primary_key=True, index=True)
    centre_name = Column(String, index=True, nullable=False)
    centre_type = Column(String, nullable=False)
    district_id = Column(Integer, ForeignKey("districts.district_id"), nullable=False)
    block = Column(String)
    village_town = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    phone = Column(String)
    total_beds = Column(Integer)
    status = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    district = relationship("District", back_populates="health_centres")
    wards = relationship("Ward", back_populates="centre")
    users = relationship("User", back_populates="centre")
    doctors = relationship("Doctor", back_populates="centre")
    inventory = relationship("MedicineInventory", back_populates="centre")
    alerts = relationship("Alert", back_populates="centre")
    ai_predictions = relationship("AIPrediction", back_populates="centre")
    health_scores = relationship("CentreHealthScore", back_populates="centre")

class Ward(Base):
    __tablename__ = "wards"
    ward_id = Column(Integer, primary_key=True, index=True)
    ward_name = Column(String, nullable=False)
    centre_id = Column(Integer, ForeignKey("health_centres.centre_id"), nullable=False)
    total_beds = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    centre = relationship("HealthCentre", back_populates="wards")
    bed_occupancies = relationship("BedOccupancy", back_populates="ward")

class Doctor(Base):
    __tablename__ = "doctors"
    doctor_id = Column(Integer, primary_key=True, index=True)
    centre_id = Column(Integer, ForeignKey("health_centres.centre_id"), nullable=False)
    doctor_name = Column(String, nullable=False)
    specialization = Column(String, nullable=False)
    employment_status = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    centre = relationship("HealthCentre", back_populates="doctors")
    attendance = relationship("DoctorAttendance", back_populates="doctor")

class DoctorAttendance(Base):
    __tablename__ = "doctor_attendance"
    attendance_id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.doctor_id"), nullable=False)
    attendance_date = Column(Date, nullable=False)
    check_in = Column(DateTime(timezone=True))
    check_out = Column(DateTime(timezone=True))
    status = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    doctor = relationship("Doctor", back_populates="attendance")

class Medicine(Base):
    __tablename__ = "medicines"
    medicine_id = Column(Integer, primary_key=True, index=True)
    medicine_name = Column(String, index=True, nullable=False)
    category = Column(String)
    unit = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    inventory = relationship("MedicineInventory", back_populates="medicine")

class MedicineInventory(Base):
    __tablename__ = "medicine_inventory"
    inventory_id = Column(Integer, primary_key=True, index=True)
    centre_id = Column(Integer, ForeignKey("health_centres.centre_id"), nullable=False)
    medicine_id = Column(Integer, ForeignKey("medicines.medicine_id"), nullable=False)
    current_stock = Column(Integer, default=0, nullable=False)
    minimum_stock = Column(Integer, default=0)
    maximum_stock = Column(Integer)
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    centre = relationship("HealthCentre", back_populates="inventory")
    medicine = relationship("Medicine", back_populates="inventory")

class MedicineStockHistory(Base):
    __tablename__ = "medicine_stock_history"
    history_id = Column(Integer, primary_key=True, index=True)
    centre_id = Column(Integer, ForeignKey("health_centres.centre_id"), nullable=False)
    medicine_id = Column(Integer, ForeignKey("medicines.medicine_id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    transaction_type = Column(String)
    recorded_at = Column(DateTime(timezone=True), server_default=func.now())

class BedOccupancy(Base):
    __tablename__ = "bed_occupancy"
    occupancy_id = Column(Integer, primary_key=True, index=True)
    ward_id = Column(Integer, ForeignKey("wards.ward_id"), nullable=False)
    occupied_beds = Column(Integer, nullable=False)
    available_beds = Column(Integer)
    recorded_at = Column(DateTime, nullable=False)
    
    ward = relationship("Ward", back_populates="bed_occupancies")

class Alert(Base):
    __tablename__ = "alerts"
    alert_id = Column(Integer, primary_key=True, index=True)
    centre_id = Column(Integer, ForeignKey("health_centres.centre_id"), nullable=False)
    alert_type = Column(String, nullable=False)
    severity = Column(String)
    title = Column(String)
    description = Column(Text)
    status = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True))
    
    centre = relationship("HealthCentre", back_populates="alerts")

class AIPrediction(Base):
    __tablename__ = "ai_predictions"
    prediction_id = Column(Integer, primary_key=True, index=True)
    centre_id = Column(Integer, ForeignKey("health_centres.centre_id"), nullable=False)
    prediction_type = Column(String, nullable=False)
    target_id = Column(Integer)
    predicted_value = Column(Float)
    prediction_date = Column(Date)
    confidence = Column(Float)
    explanation = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    centre = relationship("HealthCentre", back_populates="ai_predictions")

class CentreHealthScore(Base):
    __tablename__ = "centre_health_scores"
    score_id = Column(Integer, primary_key=True, index=True)
    centre_id = Column(Integer, ForeignKey("health_centres.centre_id"), nullable=False)
    score = Column(Float, nullable=False)
    status = Column(String)
    explanation = Column(Text)
    calculated_at = Column(DateTime(timezone=True), server_default=func.now())
    
    centre = relationship("HealthCentre", back_populates="health_scores")

class MedicineTransfer(Base):
    __tablename__ = "medicine_transfers"
    transfer_id = Column(Integer, primary_key=True, index=True)
    from_centre_id = Column(Integer, ForeignKey("health_centres.centre_id"), nullable=False)
    to_centre_id = Column(Integer, ForeignKey("health_centres.centre_id"), nullable=False)
    medicine_id = Column(Integer, ForeignKey("medicines.medicine_id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    estimated_distance_km = Column(Float)
    estimated_travel_minutes = Column(Integer)
    status = Column(String, nullable=False)
    requested_at = Column(DateTime(timezone=True), server_default=func.now())
    approved_at = Column(DateTime(timezone=True))

class SyncRecord(Base):
    __tablename__ = "sync_records"
    sync_id = Column(Integer, primary_key=True, index=True)
    centre_id = Column(Integer, ForeignKey("health_centres.centre_id"), nullable=False)
    device_id = Column(String)
    data_type = Column(String)
    local_record_id = Column(String)
    sync_status = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    synced_at = Column(DateTime(timezone=True))

class User(Base):
    __tablename__ = "users"
    user_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    password_hash = Column(Text, nullable=False)
    role = Column(String(30), nullable=False)
    centre_id = Column(Integer, ForeignKey("health_centres.centre_id"))
    language = Column(String(20))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    district_id = Column(Integer, ForeignKey("districts.district_id"))
    
    centre = relationship("HealthCentre", back_populates="users")
