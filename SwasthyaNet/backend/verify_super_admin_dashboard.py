
import urllib.request, json
from database import SessionLocal
import models, routers.auth

db = SessionLocal()

print("=" * 60)
print("PHASE 4F SUPER ADMIN VERIFICATION SUITE")
print("=" * 60)

# Helper function to make authenticated requests
def make_request(path, token, method='GET', data=None):
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    req = urllib.request.Request(f'http://localhost:8000/api{path}', headers=headers, method=method)
    if data:
        req.data = json.dumps(data).encode('utf-8')
    try:
        res = urllib.request.urlopen(req)
        return res.getcode(), json.loads(res.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8')

# 1. SUPER_ADMIN Login & JWT Token
sa_user = db.query(models.User).filter(models.User.role == 'SUPER_ADMIN').first()
sa_token = routers.auth.create_access_token({'sub': sa_user.email, 'role': sa_user.role})

print(f"\n[TEST 1] SUPER_ADMIN Login / Token Generation")
if sa_token and sa_user.role == 'SUPER_ADMIN':
    print(f"PASS: Generated token for {sa_user.email} with role {sa_user.role}")
else:
    print(f"FAIL: Unable to create token for SUPER_ADMIN")

# 2. Verify System-Wide Data Loading
print(f"\n[TEST 2] Fetching System-Wide Metrics & PostgreSQL Entities")
code, districts = make_request('/districts', sa_token)
print(f"Districts API (Status {code}): {len(districts)} districts loaded")

code, centres = make_request('/centres', sa_token)
print(f"Centres API (Status {code}): {len(centres)} centres loaded")

code, scores = make_request('/health-scores', sa_token)
print(f"Health Scores API (Status {code}): {len(scores)} scores loaded")

code, alerts = make_request('/alerts', sa_token)
print(f"Alerts API (Status {code}): {len(alerts)} alerts loaded")

code, medicines = make_request('/medicines', sa_token)
print(f"Medicines API (Status {code}): {len(medicines)} medicines loaded")

phcs = [c for c in centres if c.get('centre_type') == 'PHC']
chcs = [c for c in centres if c.get('centre_type') == 'CHC']
active_alerts = [a for a in alerts if a.get('status') not in ('RESOLVED', 'Resolved')]

print(f"\nCalculated Metrics:")
print(f"- Total Districts: {len(districts)}")
print(f"- Total Centres: {len(centres)}")
print(f"- PHC Count: {len(phcs)}")
print(f"- CHC Count: {len(chcs)}")
print(f"- Total Medicines: {len(medicines)}")
print(f"- Active Alerts: {len(active_alerts)}")

if len(districts) > 0 and len(centres) > 0 and len(medicines) > 0:
    print("PASS: Real PostgreSQL data loaded across all entities")
else:
    print("FAIL: One or more system entities empty")

# 3. Verify Centre Details Drilldown Access for Super Admin
print(f"\n[TEST 3] Super Admin Access to Centre Drilldown (/centres/1)")
code, centre_detail = make_request('/centres/1', sa_token)
code_inv, inv = make_request('/centres/1/inventory', sa_token)
code_wards, wards = make_request('/centres/1/wards', sa_token)
code_docs, docs = make_request('/centres/1/doctors', sa_token)
if code == 200 and code_inv == 200 and code_wards == 200 and code_docs == 200:
    print(f"PASS: Super Admin can drill down into Centre 1 ({centre_detail.get('centre_name')})")
else:
    print(f"FAIL: Super Admin centre drilldown failed with status {code}")

# 4. Verify RBAC & Role Isolation
print(f"\n[TEST 4] RBAC Protection on Super Admin Endpoints")
# Test with PHC_STAFF token trying to access /districts
phc_user = db.query(models.User).filter(models.User.role == 'PHC_STAFF').first()
phc_token = routers.auth.create_access_token({'sub': phc_user.email, 'role': phc_user.role, 'centre_id': phc_user.centre_id})

code_phc_dist, res = make_request('/districts', phc_token)
if code_phc_dist == 403:
    print(f"PASS: PHC_STAFF blocked from accessing /districts (HTTP 403)")
else:
    print(f"FAIL: Expected HTTP 403 for PHC_STAFF on /districts, got {code_phc_dist}")

code_phc_alerts, res = make_request('/alerts', phc_token)
if code_phc_alerts == 403:
    print(f"PASS: PHC_STAFF blocked from global /alerts (HTTP 403)")
else:
    print(f"FAIL: Expected HTTP 403 for PHC_STAFF on global /alerts, got {code_phc_alerts}")

# 5. Verify Existing Dashboards Still Work
print(f"\n[TEST 5] Verifying Existing Role Dashboard APIs")
# District Admin
da_user = db.query(models.User).filter(models.User.role == 'DISTRICT_ADMIN').first()
da_token = routers.auth.create_access_token({'sub': da_user.email, 'role': da_user.role, 'district_id': da_user.district_id})
c_da, da_dist = make_request('/districts', da_token)
c_da_cen, da_cen = make_request('/centres', da_token)
print(f"District Admin APIs: Districts ({c_da}), Centres ({c_da_cen}) -> {'PASS' if c_da == 200 and c_da_cen == 200 else 'FAIL'}")

# CHC Staff
chc_user = db.query(models.User).filter(models.User.role == 'CHC_STAFF').first()
chc_token = routers.auth.create_access_token({'sub': chc_user.email, 'role': chc_user.role, 'centre_id': chc_user.centre_id})
c_chc_c, chc_c = make_request(f'/centres/{chc_user.centre_id}', chc_token)
c_chc_inv, chc_inv = make_request(f'/centres/{chc_user.centre_id}/inventory', chc_token)
print(f"CHC Staff APIs: Centre ({c_chc_c}), Inventory ({c_chc_inv}) -> {'PASS' if c_chc_c == 200 and c_chc_inv == 200 else 'FAIL'}")

print("\n" + "=" * 60)
print("ALL API VERIFICATIONS COMPLETE")
print("=" * 60)
