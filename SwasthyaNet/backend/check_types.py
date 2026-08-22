from database import engine
from sqlalchemy import inspect
import json

inspector = inspect(engine)

for table in ["bed_occupancy", "ai_predictions"]:
    cols = inspector.get_columns(table)
    for c in cols:
        if c['name'] in ('recorded_at', 'predicted_value'):
            print(table, c['name'], c['type'])

