from database import SessionLocal
import models
from collections import Counter, defaultdict
import statistics
from datetime import datetime

db = SessionLocal()

records = db.query(models.MedicineStockHistory).order_by(models.MedicineStockHistory.history_id).all()
medicines = {m.medicine_id: m for m in db.query(models.Medicine).all()}
centres = {c.centre_id: c for c in db.query(models.HealthCentre).all()}

print("=" * 80)
print("DEEP STATISTICAL ANALYSIS OF MEDICINE_STOCK_HISTORY")
print("=" * 80)

total_records = len(records)
print(f"Total Records: {total_records}")

# 1. DATE & TIMESTAMP DISTRIBUTION
print("\n" + "=" * 40)
print("1. DATE & TIMESTAMP DISTRIBUTION")
print("=" * 40)

timestamps = [r.recorded_at for r in records if r.recorded_at]
date_counts = Counter([t.date() for t in timestamps])
exact_ts_counts = Counter(timestamps)

min_date = min(timestamps) if timestamps else None
max_date = max(timestamps) if timestamps else None

print(f"Min Timestamp: {min_date}")
print(f"Max Timestamp: {max_date}")
print(f"Unique Dates: {len(date_counts)}")
print(f"Unique Exact Timestamps: {len(exact_ts_counts)}")
print("\nRecords per Calendar Date:")
for d, cnt in date_counts.most_common(10):
    print(f"  {d}: {cnt} records ({cnt/total_records*100:.2f}%)")

print("\nTop 5 Exact Microsecond Timestamps:")
for ts, cnt in exact_ts_counts.most_common(5):
    print(f"  {ts}: {cnt} records")

# 2. TRANSACTION TYPE & IN/OUT RATIOS
print("\n" + "=" * 40)
print("2. TRANSACTION TYPE BREAKDOWN & IN/OUT RATIOS")
print("=" * 40)

tx_types = Counter([r.transaction_type for r in records])
for t_type, cnt in tx_types.items():
    qtys = [r.quantity for r in records if r.transaction_type == t_type]
    print(f"  {t_type}: {cnt} transactions ({cnt/total_records*100:.2f}%), Total Quantity: {sum(qtys):,}, Mean: {statistics.mean(qtys):.2f}, Median: {statistics.median(qtys)}, Min: {min(qtys)}, Max: {max(qtys)}")

received_qty = sum(r.quantity for r in records if r.transaction_type in ('RECEIVED', 'TRANSFER_IN'))
dispensed_qty = sum(r.quantity for r in records if r.transaction_type in ('DISPENSED', 'TRANSFER_OUT'))
print(f"\nNet Inflow vs Outflow Ratio:")
print(f"  Total Inflow: {received_qty:,} units")
print(f"  Total Outflow: {dispensed_qty:,} units")
print(f"  Outflow / Inflow Ratio: {dispensed_qty / received_qty if received_qty else 0:.4f}")

# 3. REPEATED VALUES & DISCRETENESS
print("\n" + "=" * 40)
print("3. QUANTITY DISTRIBUTION & VALUE REPETITION")
print("=" * 40)

qty_counts = Counter([r.quantity for r in records])
print("Top 15 Most Frequent Quantity Values:")
for q, count in qty_counts.most_common(15):
    print(f"  Qty = {q}: {count} occurrences ({count/total_records*100:.2f}%)")

# Check round numbers (multiples of 5, 10, 50, 100)
multiples_of_10 = sum(count for q, count in qty_counts.items() if q % 10 == 0)
multiples_of_5 = sum(count for q, count in qty_counts.items() if q % 5 == 0)
print(f"\nMultiples of 10: {multiples_of_10} / {total_records} ({multiples_of_10/total_records*100:.1f}%)")
print(f"Multiples of 5: {multiples_of_5} / {total_records} ({multiples_of_5/total_records*100:.1f}%)")

# 4. MEDICINE-WISE PATTERNS
print("\n" + "=" * 40)
print("4. MEDICINE-WISE DISPENSING PATTERNS")
print("=" * 40)

med_dispensed = defaultdict(list)
for r in records:
    if r.transaction_type == 'DISPENSED':
        med_dispensed[r.medicine_id].append(r.quantity)

print(f"{'Med ID':<8} {'Medicine Name':<28} {'Tx Count':<10} {'Total Qty':<12} {'Mean':<8} {'StdDev':<8} {'Min':<6} {'Max':<6}")
print("-" * 86)
for med_id, qtys in sorted(med_dispensed.items()):
    med_name = medicines[med_id].medicine_name if med_id in medicines else 'Unknown'
    stdev_val = statistics.stdev(qtys) if len(qtys) > 1 else 0
    print(f"{med_id:<8} {med_name:<28} {len(qtys):<10} {sum(qtys):<12} {statistics.mean(qtys):<8.1f} {stdev_val:<8.1f} {min(qtys):<6} {max(qtys):<6}")

# 5. CENTRE-WISE & FACILITY TYPE PATTERNS
print("\n" + "=" * 40)
print("5. CENTRE-WISE & FACILITY TYPE (PHC vs CHC)")
print("=" * 40)

phc_qtys = []
chc_qtys = []
centre_tx = defaultdict(lambda: {'count': 0, 'total_dispensed': 0, 'qtys': []})

for r in records:
    if r.transaction_type == 'DISPENSED':
        c_type = centres[r.centre_id].centre_type if r.centre_id in centres else 'Unknown'
        if c_type == 'PHC':
            phc_qtys.append(r.quantity)
        elif c_type == 'CHC':
            chc_qtys.append(r.quantity)
        centre_tx[r.centre_id]['count'] += 1
        centre_tx[r.centre_id]['total_dispensed'] += r.quantity
        centre_tx[r.centre_id]['qtys'].append(r.quantity)

print(f"PHC Dispensing (n={len(phc_qtys)}): Mean={statistics.mean(phc_qtys):.2f}, Median={statistics.median(phc_qtys)}, StdDev={statistics.stdev(phc_qtys):.2f}")
print(f"CHC Dispensing (n={len(chc_qtys)}): Mean={statistics.mean(chc_qtys):.2f}, Median={statistics.median(chc_qtys)}, StdDev={statistics.stdev(chc_qtys):.2f}")

print("\nPer-Centre Dispensing Summary (first 10 centres):")
print(f"{'ID':<4} {'Centre Name':<30} {'Type':<6} {'Tx Count':<10} {'Total Qty':<12} {'Mean Qty':<10}")
print("-" * 75)
for cid in sorted(centre_tx.keys())[:10]:
    c = centres.get(cid)
    cname = c.centre_name if c else 'Unknown'
    ctype = c.centre_type if c else 'Unknown'
    data = centre_tx[cid]
    mean_q = statistics.mean(data['qtys']) if data['qtys'] else 0
    print(f"{cid:<4} {cname:<30} {ctype:<6} {data['count']:<10} {data['total_dispensed']:<12} {mean_q:<10.1f}")

# 6. TIME-SERIES CONTINUITY & TEMPORAL SIGNATURE
print("\n" + "=" * 40)
print("6. TIME-SERIES CONTINUITY & TEMPORAL SIGNATURE")
print("=" * 40)

# Check intervals between records for a specific centre & medicine
c1_m1 = [r for r in records if r.centre_id == 1 and r.medicine_id == 1]
print(f"Centre 1, Medicine 1 total transactions: {len(c1_m1)}")
print("First 10 transactions for Centre 1, Medicine 1:")
for r in c1_m1[:10]:
    print(f"  history_id={r.history_id:<5} type={r.transaction_type:<10} qty={r.quantity:<5} recorded_at={r.recorded_at}")

# Batch vs Live audit
batch_seeded = [r for r in records if r.history_id <= 2717]
live_user = [r for r in records if r.history_id > 2717]
print(f"\nHistorical Seeded Records (history_id <= 2717): {len(batch_seeded)}")
if batch_seeded:
    seed_ts = set(r.recorded_at for r in batch_seeded)
    print(f"  Distinct timestamps among 2,717 seed records: {len(seed_ts)}")
    print(f"  Exact timestamp for seed records: {list(seed_ts)[:3]}")

print(f"\nLive User-Generated Records (history_id > 2717): {len(live_user)}")
for r in live_user:
    print(f"  history_id={r.history_id:<5} centre={r.centre_id} med={r.medicine_id} type={r.transaction_type:<10} qty={r.quantity:<5} at {r.recorded_at}")
