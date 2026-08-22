from database import engine
from sqlalchemy import text
import json

with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT conname, pg_get_constraintdef(c.oid)
        FROM pg_constraint c
        JOIN pg_namespace n ON n.oid = c.connamespace
        WHERE contype = 'c'
    """))
    for row in result:
        print(row[0], ":", row[1])

