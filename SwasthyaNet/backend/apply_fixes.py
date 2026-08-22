import os

# 1. Update schemas.py
with open("schemas.py", "r") as f:
    schema_code = f.read()
schema_code = schema_code.replace("recorded_at: date", "recorded_at: datetime")
schema_code = schema_code.replace("predicted_value: Optional[str] = None", "predicted_value: Optional[float] = None")
with open("schemas.py", "w") as f:
    f.write(schema_code)

# 2. Update routers/attendance.py
attendance_file = os.path.join("routers", "attendance.py")
with open(attendance_file, "r") as f:
    attendance_code = f.read()
if "attendance.status.upper()" not in attendance_code:
    attendance_code = attendance_code.replace(
        "db_attendance = models.DoctorAttendance(**attendance.model_dump())",
        "attendance.status = attendance.status.upper()\n    db_attendance = models.DoctorAttendance(**attendance.model_dump())"
    )
with open(attendance_file, "w") as f:
    f.write(attendance_code)

# 3. Update routers/inventory.py
inventory_file = os.path.join("routers", "inventory.py")
with open(inventory_file, "r") as f:
    inventory_code = f.read()
if "update_data.transaction_type.upper()" not in inventory_code:
    inventory_code = inventory_code.replace(
        "transaction_type=update_data.transaction_type",
        "transaction_type=update_data.transaction_type.upper()"
    )
with open(inventory_file, "w") as f:
    f.write(inventory_code)

# 4. Update routers/sync.py
sync_file = os.path.join("routers", "sync.py")
with open(sync_file, "r") as f:
    sync_code = f.read()
if "sync_record.sync_status.upper()" not in sync_code:
    sync_code = sync_code.replace(
        "db_sync = models.SyncRecord(**sync_record.model_dump())",
        "sync_record.sync_status = sync_record.sync_status.upper()\n    db_sync = models.SyncRecord(**sync_record.model_dump())"
    )
with open(sync_file, "w") as f:
    f.write(sync_code)

# 5. Update routers/transfers.py
transfers_file = os.path.join("routers", "transfers.py")
with open(transfers_file, "r") as f:
    transfers_code = f.read()
transfers_code = transfers_code.replace('status="Pending"', 'status="RECOMMENDED"')
transfers_code = transfers_code.replace('transfer.status = "Approved"', 'transfer.status = "APPROVED"')
transfers_code = transfers_code.replace('transfer.status = "Rejected"', 'transfer.status = "CANCELLED"')
with open(transfers_file, "w") as f:
    f.write(transfers_code)

# 6. Update routers/wards.py
wards_file = os.path.join("routers", "wards.py")
with open(wards_file, "r") as f:
    wards_code = f.read()
if "occupancy.available_beds = ward.total_beds - occupancy.occupied_beds" not in wards_code:
    wards_code = wards_code.replace(
        "existing = db.query(models.BedOccupancy).filter(",
        "if occupancy.available_beds is None:\n        occupancy.available_beds = ward.total_beds - occupancy.occupied_beds\n        \n    existing = db.query(models.BedOccupancy).filter("
    )
with open(wards_file, "w") as f:
    f.write(wards_code)

print("All fixes applied successfully.")
