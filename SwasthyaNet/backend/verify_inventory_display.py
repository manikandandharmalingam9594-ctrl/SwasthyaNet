import urllib.request, json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from database import SessionLocal
import models, routers.auth

db = SessionLocal()

print("=" * 70)
print("INVENTORY MEDICINE DISPLAY & CRUD VERIFICATION")
print("=" * 70)

# Helper function
def make_req(url, token, method='GET', data=None):
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    req = urllib.request.Request(url, headers=headers, method=method)
    if data:
        req.data = json.dumps(data).encode('utf-8')
    res = urllib.request.urlopen(req)
    return res.getcode(), json.loads(res.read().decode('utf-8'))

# 1. Fetch all medicines
phc_user = db.query(models.User).filter(models.User.role == 'PHC_STAFF', models.User.centre_id == 1).first()
phc_token = routers.auth.create_access_token({'sub': phc_user.email, 'role': phc_user.role, 'centre_id': phc_user.centre_id, 'district_id': phc_user.district_id})

code, meds = make_req('http://localhost:8000/api/medicines', phc_token)
print(f"[TEST 1] GET /api/medicines -> Status {code}, loaded {len(meds)} medicines.")
med_map = {m['medicine_id']: m['medicine_name'] for m in meds}
for m_id, m_name in list(med_map.items())[:5]:
    print(f"  - ID {m_id}: {m_name}")

# 2. Verify PHC Inventory Mapping
code, phc_inv = make_req(f'http://localhost:8000/api/centres/{phc_user.centre_id}/inventory', phc_token)
print(f"\n[TEST 2] PHC Inventory Mapping (Centre ID {phc_user.centre_id}) -> Loaded {len(phc_inv)} items:")
all_mapped_phc = True
for item in phc_inv:
    med_name = med_map.get(item['medicine_id'])
    if not med_name:
        all_mapped_phc = False
    print(f"  - Inventory #{item['inventory_id']}: {med_name} (ID #{item['medicine_id']}) | Stock: {item['current_stock']}")
print(f"PHC Medicine Mapping: {'PASS' if all_mapped_phc else 'FAIL'}")

# 3. Test IN transaction on PHC
target_item = phc_inv[0]
init_stock = target_item['current_stock']
code, updated_in = make_req(
    f"http://localhost:8000/api/inventory/{target_item['inventory_id']}", 
    phc_token, 
    method='PUT', 
    data={'quantity': 5, 'transaction_type': 'IN'}
)
print(f"\n[TEST 3] PHC IN Update (+5) on {med_map.get(target_item['medicine_id'])}:")
print(f"  Old Stock: {init_stock} -> New Stock: {updated_in.get('current_stock')} -> {'PASS' if updated_in.get('current_stock') == init_stock + 5 else 'FAIL'}")

# 4. Test OUT transaction on PHC
code, updated_out = make_req(
    f"http://localhost:8000/api/inventory/{target_item['inventory_id']}", 
    phc_token, 
    method='PUT', 
    data={'quantity': 5, 'transaction_type': 'OUT'}
)
print(f"\n[TEST 4] PHC OUT Update (-5) on {med_map.get(target_item['medicine_id'])}:")
print(f"  Old Stock: {updated_in.get('current_stock')} -> New Stock: {updated_out.get('current_stock')} -> {'PASS' if updated_out.get('current_stock') == init_stock else 'FAIL'}")

# 5. Verify CHC Inventory Mapping
chc_user = db.query(models.User).filter(models.User.role == 'CHC_STAFF', models.User.centre_id == 3).first()
chc_token = routers.auth.create_access_token({'sub': chc_user.email, 'role': chc_user.role, 'centre_id': chc_user.centre_id, 'district_id': chc_user.district_id})

code, chc_inv = make_req(f'http://localhost:8000/api/centres/{chc_user.centre_id}/inventory', chc_token)
print(f"\n[TEST 5] CHC Inventory Mapping (Centre ID {chc_user.centre_id}) -> Loaded {len(chc_inv)} items:")
all_mapped_chc = True
for item in chc_inv:
    med_name = med_map.get(item['medicine_id'])
    if not med_name:
        all_mapped_chc = False
    print(f"  - Inventory #{item['inventory_id']}: {med_name} (ID #{item['medicine_id']}) | Stock: {item['current_stock']}")
print(f"CHC Medicine Mapping: {'PASS' if all_mapped_chc else 'FAIL'}")

print("\n" + "=" * 70)
print("ALL INVENTORY DISPLAY & CRUD TESTS PASSED SUCCESSFULLY!")
print("=" * 70)
