from database import engine
from sqlalchemy import text

with engine.begin() as conn:
    conn.execute(text("SELECT setval(pg_get_serial_sequence('users', 'user_id'), coalesce(max(user_id), 0) + 1, false) FROM users;"))
    print("Fixed users sequence.")
