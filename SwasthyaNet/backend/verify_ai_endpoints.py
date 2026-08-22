import os, sys, io
from fastapi.testclient import TestClient
import jwt

# Ensure UTF-8 stdout
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from main import app
from database import SessionLocal
import models
from routers.auth import JWT_SECRET, ALGORITHM

client = TestClient(app)
db = SessionLocal()

print("=" * 85)
print("PHASE 5F: FASTAPI AI INTEGRATION & RBAC SECURITY TEST SUITE")
print("=" * 85)

# Helper function to generate JWT token for any role
def create_test_token(username: str, role: str, centre_id: int = None, district_id: int = None):
    payload = {
        "sub": username,
        "role": role,
        "centre_id": centre_id,
        "district_id": district_id
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)

# 1. Generate Tokens for test roles
token_super = create_test_token("super_admin_test", "SUPER_ADMIN")
token_dist1 = create_test_token("dist1_admin_test", "DISTRICT_ADMIN", district_id=1)
token_dist2 = create_test_token("dist2_admin_test", "DISTRICT_ADMIN", district_id=2)
token_phc1 = create_test_token("phc1_staff_test", "PHC_STAFF", centre_id=1, district_id=1)
token_phc2 = create_test_token("phc2_staff_test", "PHC_STAFF", centre_id=2, district_id=1)
token_chc3 = create_test_token("chc3_staff_test", "CHC_STAFF", centre_id=3, district_id=1)
token_phc4 = create_test_token("phc4_staff_test", "PHC_STAFF", centre_id=4, district_id=2)

passed_checks = 0
total_checks = 0

def record_test(name, condition, details=""):
    global passed_checks, total_checks
    total_checks += 1
    status = "PASS" if condition else "FAIL"
    if condition:
        passed_checks += 1
    print(f"  [{total_checks:02d}] {name:<60} -> {status}")
    if details:
        print(f"       Details: {details}")

# -----------------------------------------------------------------------------
# TEST 1: ANONYMOUS REQUESTS (HTTP 401)
# -----------------------------------------------------------------------------
print("\n--- 1. ANONYMOUS REQUEST SECURITY (HTTP 401) ---")
res_anon_stock = client.get("/api/ai/stockout/1/1")
record_test("Anonymous request to stockout endpoint returns 401", res_anon_stock.status_code == 401, f"Status: {res_anon_stock.status_code}")

res_anon_bed = client.get("/api/ai/bed-forecast/1/1")
record_test("Anonymous request to bed forecast endpoint returns 401", res_anon_bed.status_code == 401, f"Status: {res_anon_bed.status_code}")

# -----------------------------------------------------------------------------
# TEST 2: PHC/CHC STAFF OWN CENTRE ACCESS & PREDICTIONS
# -----------------------------------------------------------------------------
print("\n--- 2. PHC/CHC STAFF PREDICTION INFERENCE ---")
headers_phc1 = {"Authorization": f"Bearer {token_phc1}"}
res_phc1_stock = client.get("/api/ai/stockout/1/1", headers=headers_phc1)
record_test(
    "PHC 1 Staff gets stockout prediction for Centre 1, Med 1",
    res_phc1_stock.status_code == 200 and "predicted_days_until_stockout" in res_phc1_stock.json(),
    f"Pred Days: {res_phc1_stock.json().get('predicted_days_until_stockout')}d, Risk: {res_phc1_stock.json().get('risk_level')}"
)

res_phc1_bed = client.get("/api/ai/bed-forecast/1/1", headers=headers_phc1)
record_test(
    "PHC 1 Staff gets bed forecasts (t+1, t+7, t+14) for Centre 1, Ward 1",
    res_phc1_bed.status_code == 200 and "t_plus_1" in res_phc1_bed.json().get("forecasts", {}),
    f"t+1: {res_phc1_bed.json().get('forecasts', {}).get('t_plus_1', {}).get('predicted_occupied_beds')} beds, "
    f"t+7: {res_phc1_bed.json().get('forecasts', {}).get('t_plus_7', {}).get('predicted_occupied_beds')} beds, "
    f"t+14: {res_phc1_bed.json().get('forecasts', {}).get('t_plus_14', {}).get('predicted_occupied_beds')} beds"
)

headers_chc3 = {"Authorization": f"Bearer {token_chc3}"}
res_chc3_bed = client.get("/api/ai/bed-forecast/3/7", headers=headers_chc3)
record_test(
    "CHC 3 Staff gets bed forecast for CHC 3 General Ward (30 beds)",
    res_chc3_bed.status_code == 200 and res_chc3_bed.json().get("total_beds") == 30,
    f"Capacity: 30 beds, t+7 forecast: {res_chc3_bed.json().get('forecasts', {}).get('t_plus_7', {}).get('predicted_occupied_beds')} beds ({res_chc3_bed.json().get('forecasts', {}).get('t_plus_7', {}).get('predicted_occupancy_rate_pct')}%)"
)

# -----------------------------------------------------------------------------
# TEST 3: CROSS-CENTRE RBAC ISOLATION (HTTP 403)
# -----------------------------------------------------------------------------
print("\n--- 3. CROSS-CENTRE RBAC ISOLATION (HTTP 403) ---")
# PHC 1 Staff tries accessing Centre 2
res_cross_phc = client.get("/api/ai/stockout/2/1", headers=headers_phc1)
record_test("PHC 1 Staff accessing Centre 2 stockout returns 403", res_cross_phc.status_code == 403, f"Status: {res_cross_phc.status_code}")

res_cross_bed = client.get("/api/ai/bed-forecast/2/4", headers=headers_phc1)
record_test("PHC 1 Staff accessing Centre 2 bed forecast returns 403", res_cross_bed.status_code == 403, f"Status: {res_cross_bed.status_code}")

# CHC 3 Staff tries accessing Centre 1
res_cross_chc = client.get("/api/ai/stockout/1/1", headers=headers_chc3)
record_test("CHC 3 Staff accessing Centre 1 stockout returns 403", res_cross_chc.status_code == 403, f"Status: {res_cross_chc.status_code}")

# -----------------------------------------------------------------------------
# TEST 4: DISTRICT ADMIN PERMISSIONS & CROSS-DISTRICT ISOLATION
# -----------------------------------------------------------------------------
print("\n--- 4. DISTRICT ADMIN PERMISSIONS & CROSS-DISTRICT ISOLATION ---")
headers_dist1 = {"Authorization": f"Bearer {token_dist1}"}

# District 1 Admin accesses Centre 1 (District 1) -> 200
res_dist1_c1 = client.get("/api/ai/stockout/1/1", headers=headers_dist1)
record_test("District 1 Admin accessing Centre 1 (in-district) returns 200", res_dist1_c1.status_code == 200)

# District 1 Admin accesses Centre 3 (CHC in District 1) -> 200
res_dist1_c3 = client.get("/api/ai/bed-forecast/3/7", headers=headers_dist1)
record_test("District 1 Admin accessing Centre 3 bed forecast returns 200", res_dist1_c3.status_code == 200)

# District 1 Admin tries accessing Centre 4 (in District 2) -> 403
res_dist1_c4 = client.get("/api/ai/stockout/4/1", headers=headers_dist1)
record_test("District 1 Admin accessing Centre 4 (cross-district) returns 403", res_dist1_c4.status_code == 403, f"Status: {res_dist1_c4.status_code}")

res_dist1_c4_bed = client.get("/api/ai/bed-forecast/4/10", headers=headers_dist1)
record_test("District 1 Admin accessing Centre 4 bed forecast returns 403", res_dist1_c4_bed.status_code == 403, f"Status: {res_dist1_c4_bed.status_code}")

# -----------------------------------------------------------------------------
# TEST 5: SUPER ADMIN STATE-WIDE ACCESS
# -----------------------------------------------------------------------------
print("\n--- 5. SUPER ADMIN GLOBAL ACCESS ---")
headers_super = {"Authorization": f"Bearer {token_super}"}

res_super_c1 = client.get("/api/ai/stockout/1/1", headers=headers_super)
record_test("Super Admin accesses Centre 1 stockout", res_super_c1.status_code == 200)

res_super_c4 = client.get("/api/ai/stockout/4/1", headers=headers_super)
record_test("Super Admin accesses Centre 4 stockout", res_super_c4.status_code == 200)

res_super_c18 = client.get("/api/ai/bed-forecast/18/52", headers=headers_super)
record_test("Super Admin accesses Centre 18 (District 7) bed forecast", res_super_c18.status_code == 200)

# -----------------------------------------------------------------------------
# TEST 6: INVALID IDS & NOT FOUND ERROR HANDLING
# -----------------------------------------------------------------------------
print("\n--- 6. ERROR HANDLING & VALIDATION ---")
# Non-existent centre
res_invalid_centre = client.get("/api/ai/stockout/999/1", headers=headers_super)
record_test("Non-existent centre returns 404", res_invalid_centre.status_code == 404)

# Non-existent medicine
res_invalid_med = client.get("/api/ai/stockout/1/999", headers=headers_super)
record_test("Non-existent medicine returns 404", res_invalid_med.status_code == 404)

# Mismatched ward (Ward 10 belongs to Centre 4, requested on Centre 1)
res_mismatch_ward = client.get("/api/ai/bed-forecast/1/10", headers=headers_super)
record_test("Mismatched Ward ID returns 404", res_mismatch_ward.status_code == 404)

# -----------------------------------------------------------------------------
# TEST 7: REGRESSION TEST FOR EXISTING PHASE 1-4 APIS
# -----------------------------------------------------------------------------
print("\n--- 7. REGRESSION TEST: PHASE 1-4 PRODUCTION APIS ---")
res_health = client.get("/health")
record_test("GET /health returns healthy", res_health.status_code == 200 and res_health.json().get("status") == "healthy")

res_districts = client.get("/api/districts", headers=headers_super)
record_test("GET /api/districts returns 7 districts", res_districts.status_code == 200 and len(res_districts.json()) == 7)

res_meds = client.get("/api/medicines", headers=headers_super)
record_test("GET /api/medicines returns 20 medicines", res_meds.status_code == 200 and len(res_meds.json()) == 20)

res_centres = client.get("/api/centres", headers=headers_super)
record_test("GET /api/centres returns 18 centres", res_centres.status_code == 200 and len(res_centres.json()) == 18)

# -----------------------------------------------------------------------------
# TEST 8: POSTGRESQL SCHEMA INTEGRITY (EXACTLY 15 TABLES)
# -----------------------------------------------------------------------------
print("\n--- 8. DATABASE SCHEMA AUDIT ---")
table_names = list(models.Base.metadata.tables.keys())
record_test(
    "PostgreSQL table count remains exactly 15 tables",
    len(table_names) == 15,
    f"Tables ({len(table_names)}): {', '.join(table_names)}"
)

print("\n" + "=" * 85)
print(f"VERIFICATION SUMMARY: {passed_checks} / {total_checks} CHECKS PASSED ({passed_checks/total_checks*100:.1f}%)")
print("=" * 85)
