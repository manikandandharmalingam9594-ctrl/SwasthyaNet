from database import engine
from sqlalchemy import inspect

inspector = inspect(engine)
cols = inspector.get_columns("users")
print("PostgreSQL 'users' table columns:")
for c in cols:
    print(c['name'], c['type'])
