from database import engine
from sqlalchemy import text

def migrate():
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_activated BOOLEAN DEFAULT TRUE;"))
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS must_change_password BOOLEAN DEFAULT FALSE;"))
        conn.commit()
        print("Columns is_activated and must_change_password migrated successfully!")

if __name__ == "__main__":
    migrate()
