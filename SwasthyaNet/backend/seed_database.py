import json
import os
from datetime import datetime, date
from sqlalchemy import text
from database import engine, SessionLocal
import models

def parse_val(val, type_cls):
    if val is None:
        return None
    if type_cls == "date" and isinstance(val, str):
        return date.fromisoformat(val)
    if type_cls == "datetime" and isinstance(val, str):
        return datetime.fromisoformat(val)
    return val

def seed_database():
    print("=" * 60)
    print("SWASTHYANET AUTOMATED DATABASE SEEDER")
    print("=" * 60)

    # 1. Create all database tables
    models.Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    seed_file = os.path.join(os.path.dirname(__file__), "database_seed.json")
    if not os.path.exists(seed_file):
        print(f"[ERROR] Seed file '{seed_file}' not found.")
        return

    with open(seed_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    tables_in_order = [
        ("districts", models.District),
        ("health_centres", models.HealthCentre),
        ("wards", models.Ward),
        ("doctors", models.Doctor),
        ("medicines", models.Medicine),
        ("medicine_inventory", models.MedicineInventory),
        ("bed_occupancy", models.BedOccupancy),
        ("alerts", models.Alert),
        ("ai_predictions", models.AIPrediction),
        ("centre_health_scores", models.CentreHealthScore),
        ("users", models.User)
    ]

    for table_name, model_cls in tables_in_order:
        existing_count = db.query(model_cls).count()
        rows = data.get(table_name, [])
        if existing_count > 0:
            print(f"[READY]   {table_name:<22} | {existing_count} records already exist.")
            continue

        inserted = 0
        for row in rows:
            obj_data = {}
            for col in model_cls.__table__.columns:
                val = row.get(col.name)
                col_type = str(col.type).lower()
                if "date" in col_type and not "datetime" in col_type:
                    val = parse_val(val, "date")
                elif "date" in col_type or "time" in col_type:
                    val = parse_val(val, "datetime")
                obj_data[col.name] = val

            obj = model_cls(**obj_data)
            db.add(obj)
            inserted += 1

        db.commit()
        print(f"[SEEDED]  {table_name:<22} | Inserted {inserted} records.")

    # Fix PostgreSQL sequence primary key sequences if postgres engine
    if "postgresql" in str(engine.url):
        print("-" * 60)
        print("Synchronizing PostgreSQL Primary Key Sequences...")
        sequences = [
            ("districts", "district_id"),
            ("health_centres", "centre_id"),
            ("wards", "ward_id"),
            ("doctors", "doctor_id"),
            ("medicines", "medicine_id"),
            ("medicine_inventory", "inventory_id"),
            ("bed_occupancy", "occupancy_id"),
            ("alerts", "alert_id"),
            ("ai_predictions", "prediction_id"),
            ("centre_health_scores", "score_id"),
            ("users", "user_id")
        ]
        for tbl, pkey in sequences:
            try:
                sql = text(f"SELECT setval(pg_get_serial_sequence('{tbl}', '{pkey}'), COALESCE(MAX({pkey}), 1)) FROM {tbl};")
                db.execute(sql)
            except Exception as e:
                pass
        db.commit()

    print("=" * 60)
    print("Database seeding completed successfully!")
    print("=" * 60)
    db.close()

if __name__ == "__main__":
    seed_database()
