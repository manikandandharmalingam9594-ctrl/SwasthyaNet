from database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

# 1. Check ai_predictions table content
print('=== AI Predictions ===')
rows = db.execute(text('SELECT * FROM ai_predictions LIMIT 10')).fetchall()
if rows:
    for r in rows:
        print(dict(r._mapping))
else:
    print('(empty table)')

print()

# 2. Check all alerts
print('=== All Alerts ===')
rows = db.execute(text('SELECT alert_id, centre_id, alert_type, title, description, status, created_at FROM alerts LIMIT 20')).fetchall()
for r in rows:
    print(dict(r._mapping))

print()

# 3. Check medicine_stock_history
print('=== Recent Stock History (last 10) ===')
rows = db.execute(text('SELECT * FROM medicine_stock_history ORDER BY recorded_at DESC LIMIT 10')).fetchall()
for r in rows:
    print(dict(r._mapping))

print()

# 4. Is there any Python file that writes to ai_predictions?
print('=== Table row counts ===')
tables = ['ai_predictions', 'alerts', 'medicine_stock_history', 'medicine_inventory']
for t in tables:
    cnt = db.execute(text(f'SELECT COUNT(*) FROM {t}')).scalar()
    print(f'  {t}: {cnt} rows')
