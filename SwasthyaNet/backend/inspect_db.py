from database import engine
from sqlalchemy import inspect
import json

inspector = inspect(engine)
schema_info = {}
for table in inspector.get_table_names():
    cols = inspector.get_columns(table)
    schema_info[table] = [c['name'] for c in cols]

print(json.dumps(schema_info, indent=2))
