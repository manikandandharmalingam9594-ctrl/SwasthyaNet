import json
import os
from database import SessionLocal
import models

def datetime_serializer(obj):
    if hasattr(obj, 'isoformat'):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

def export_database():
    db = SessionLocal()
    seed_data = {}

    models_to_export = [
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

    for table_name, model_cls in models_to_export:
        records = db.query(model_cls).all()
        rows = []
        for r in records:
            row = {}
            for column in model_cls.__table__.columns:
                val = getattr(r, column.name)
                if hasattr(val, 'isoformat'):
                    val = val.isoformat()
                row[column.name] = val
            rows.append(row)
        seed_data[table_name] = rows
        print(f"Exported {len(rows)} records for {table_name}")

    output_path = os.path.join(os.path.dirname(__file__), "database_seed.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(seed_data, f, indent=2)

    print(f"\n[SUCCESS] Seed data exported to: {output_path}")
    db.close()

if __name__ == "__main__":
    export_database()
