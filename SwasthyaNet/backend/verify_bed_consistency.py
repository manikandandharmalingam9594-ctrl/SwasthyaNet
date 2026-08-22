from fastapi.testclient import TestClient
from main import app
from routers.auth import create_access_token
from database import SessionLocal
import models

client = TestClient(app)
db = SessionLocal()

print('=== 1. VERIFYING BED OCCUPANCY CONSISTENCY (CENTRE 6 & CENTRE 3 & CENTRE 1) ===')
for centre_id in [6, 3, 1]:
    c = db.query(models.HealthCentre).filter(models.HealthCentre.centre_id == centre_id).first()
    token = create_access_token({'sub': 'superadmin@swasthyanet.com', 'role': 'SUPER_ADMIN'})
    headers = {'Authorization': f'Bearer {token}'}
    
    # 1. Fetch beds endpoint
    beds_res = client.get(f'/api/centres/{centre_id}/beds', headers=headers)
    assert beds_res.status_code == 200, f'Failed to get beds: {beds_res.text}'
    beds_data = beds_res.json()
    
    # 2. Fetch wards endpoint
    wards_res = client.get(f'/api/centres/{centre_id}/wards', headers=headers)
    assert wards_res.status_code == 200
    wards_data = wards_res.json()
    
    print(f'\nHealth Centre: {c.centre_name} (ID: {centre_id})')
    for w in wards_data:
        w_id = w['ward_id']
        w_name = w['ward_name']
        t_beds = w['total_beds']
        
        bed_entry = next((b for b in beds_data if b['ward_id'] == w_id), None)
        assert bed_entry is not None, f'Missing bed entry for ward {w_id}'
        api_occupied = bed_entry['occupied_beds']
        
        ai_res = client.get(f'/api/ai/bed-forecast/{centre_id}/{w_id}', headers=headers)
        assert ai_res.status_code == 200, f'AI forecast failed: {ai_res.text}'
        ai_data = ai_res.json()
        ai_occupied = ai_data['current_occupied_beds']
        
        match = api_occupied == ai_occupied
        print(f'  Ward {w_id} ({w_name}): Total={t_beds} | API Occupied={api_occupied} | AI Occupied={ai_occupied} -> MATCH: {match}')
        assert match, f'MISMATCH for Ward {w_id}: API={api_occupied} vs AI={ai_occupied}'
        assert api_occupied <= t_beds or w_name == 'Emergency', f'Over capacity in non-emergency: {api_occupied} > {t_beds}'

print('\n=== 2. VERIFYING CAPACITY ENFORCEMENT ON UPDATE ===')
ward7 = db.query(models.Ward).filter(models.Ward.ward_id == 7).first()
fail_res = client.put(f'/api/wards/7/occupancy', json={'occupied_beds': 92}, headers=headers)
print(f'Update General Ward (30 beds) with 92 beds -> Status {fail_res.status_code}: {fail_res.json()}')
assert fail_res.status_code == 400

fail_neg = client.put(f'/api/wards/7/occupancy', json={'occupied_beds': -5}, headers=headers)
print(f'Update General Ward with -5 beds -> Status {fail_neg.status_code}: {fail_neg.json()}')
assert fail_neg.status_code == 400

ok_res = client.put(f'/api/wards/7/occupancy', json={'occupied_beds': 20}, headers=headers)
print(f'Update General Ward with 20 beds -> Status {ok_res.status_code}: {ok_res.json()}')
assert ok_res.status_code == 200

beds_check = client.get('/api/centres/3/beds', headers=headers).json()
ai_check = client.get('/api/ai/bed-forecast/3/7', headers=headers).json()
b7 = next(b for b in beds_check if b['ward_id'] == 7)
print(f'Post-Update Verify: API = {b7["occupied_beds"]} | AI = {ai_check["current_occupied_beds"]}')
assert b7['occupied_beds'] == 20
assert ai_check['current_occupied_beds'] == 20

print('\nALL BED CONSISTENCY & CAPACITY TESTS PASSED SUCCESSFULLY!')
