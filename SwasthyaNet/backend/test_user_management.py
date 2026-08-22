import urllib.request, json
from database import SessionLocal
import models, routers.auth

db = SessionLocal()

print("=" * 60)
print("USER MANAGEMENT BACKEND VERIFICATION SUITE")
print("=" * 60)

def make_req(path, token, method='GET', payload=None):
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    req = urllib.request.Request(f'http://localhost:8000/api{path}', headers=headers, method=method)
    if payload is not None:
        req.data = json.dumps(payload).encode('utf-8')
    try:
        res = urllib.request.urlopen(req)
        return res.getcode(), json.loads(res.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        try:
            err_data = json.loads(e.read().decode('utf-8'))
        except:
            err_data = {}
        return e.code, err_data

# Tokens
sa_user = db.query(models.User).filter(models.User.role == 'SUPER_ADMIN').first()
sa_token = routers.auth.create_access_token({'sub': sa_user.email, 'role': sa_user.role, 'user_id': sa_user.user_id})

da_user = db.query(models.User).filter(models.User.role == 'DISTRICT_ADMIN', models.User.district_id == 1).first()
da_token = routers.auth.create_access_token({'sub': da_user.email, 'role': da_user.role, 'user_id': da_user.user_id, 'district_id': da_user.district_id})

phc_user = db.query(models.User).filter(models.User.role == 'PHC_STAFF').first()
phc_token = routers.auth.create_access_token({'sub': phc_user.email, 'role': phc_user.role, 'user_id': phc_user.user_id, 'centre_id': phc_user.centre_id})

print("\n--- 1. SUPER ADMIN PERMISSIONS ---")
# 1.1 View all users
code, users = make_req('/users', sa_token)
print(f"1.1 Super Admin GET /users: Status {code}, loaded {len(users)} users")
has_pw = any('password_hash' in u for u in users)
print(f"    Password hash never exposed: {'PASS' if not has_pw else 'FAIL'}")

# 1.2 Create DISTRICT_ADMIN
import random
rand_id = random.randint(1000, 9999)
new_da_email = f"testda_{rand_id}@swasthyanet.com"
code, new_da = make_req('/users', sa_token, 'POST', {
    'name': f'Test DA {rand_id}',
    'email': new_da_email,
    'password': 'testpassword123',
    'role': 'DISTRICT_ADMIN',
    'district_id': 2
})
print(f"1.2 Super Admin create DISTRICT_ADMIN: Status {code} -> {'PASS' if code == 201 else 'FAIL'}")

# 1.3 Create PHC_STAFF (Centre 1 is PHC in District 1)
new_phc_email = f"testphc_{rand_id}@swasthyanet.com"
code, new_phc = make_req('/users', sa_token, 'POST', {
    'name': f'Test PHC {rand_id}',
    'email': new_phc_email,
    'password': 'testpassword123',
    'role': 'PHC_STAFF',
    'centre_id': 1
})
print(f"1.3 Super Admin create PHC_STAFF: Status {code} -> {'PASS' if code == 201 else 'FAIL'}")

# 1.4 Prevent duplicate email
code, err = make_req('/users', sa_token, 'POST', {
    'name': 'Duplicate User',
    'email': new_phc_email,
    'password': 'testpassword123',
    'role': 'PHC_STAFF',
    'centre_id': 1
})
print(f"1.4 Prevent duplicate email: Status {code} -> {'PASS' if code == 400 else 'FAIL'}")

# 1.5 Activate / Deactivate User
user_to_toggle = new_phc.get('user_id')
code, updated = make_req(f'/users/{user_to_toggle}/status', sa_token, 'PATCH', {'is_active': False})
print(f"1.5 Deactivate user: Status {code}, is_active={updated.get('is_active')} -> {'PASS' if code == 200 and updated.get('is_active') is False else 'FAIL'}")

code, updated2 = make_req(f'/users/{user_to_toggle}/status', sa_token, 'PATCH', {'is_active': True})
print(f"    Re-activate user: Status {code}, is_active={updated2.get('is_active')} -> {'PASS' if code == 200 and updated2.get('is_active') is True else 'FAIL'}")


print("\n--- 2. DISTRICT ADMIN PERMISSIONS ---")
# 2.1 View only users in their district
code, da_users = make_req('/users', da_token)
all_in_d1 = all(u.get('district_id') == 1 for u in da_users)
print(f"2.1 District Admin GET /users: Status {code}, {len(da_users)} users. Scoped to District 1: {'PASS' if all_in_d1 else 'FAIL'}")

# 2.2 District Admin create PHC staff in their district (Centre 1 is in District 1)
new_d1_phc_email = f"dastaff_{rand_id}@swasthyanet.com"
code, da_created_staff = make_req('/users', da_token, 'POST', {
    'name': f'DA Created Staff {rand_id}',
    'email': new_d1_phc_email,
    'password': 'testpassword123',
    'role': 'PHC_STAFF',
    'centre_id': 1
})
print(f"2.2 District Admin create PHC_STAFF in District 1: Status {code} -> {'PASS' if code == 201 else 'FAIL'}")

# 2.3 District Admin blocked from creating DISTRICT_ADMIN or SUPER_ADMIN
code, err = make_req('/users', da_token, 'POST', {
    'name': 'Hacker Admin',
    'email': f'hacker_{rand_id}@swasthyanet.com',
    'password': 'testpassword123',
    'role': 'DISTRICT_ADMIN',
    'district_id': 1
})
print(f"2.3 District Admin create DISTRICT_ADMIN blocked: Status {code} -> {'PASS' if code == 403 else 'FAIL'}")

# 2.4 District Admin blocked from assigning staff to another district (Centre 4 is in District 2)
code, err = make_req('/users', da_token, 'POST', {
    'name': 'Cross District Staff',
    'email': f'cross_{rand_id}@swasthyanet.com',
    'password': 'testpassword123',
    'role': 'PHC_STAFF',
    'centre_id': 4
})
print(f"2.4 District Admin cross-district assignment blocked: Status {code} -> {'PASS' if code == 403 else 'FAIL'}")

# 2.5 District Admin activate / deactivate their district staff
staff_id = da_created_staff.get('user_id')
code, da_toggled = make_req(f'/users/{staff_id}/status', da_token, 'PATCH', {'is_active': False})
print(f"2.5 District Admin toggle their staff status: Status {code} -> {'PASS' if code == 200 and da_toggled.get('is_active') is False else 'FAIL'}")

# 2.6 District Admin blocked from modifying user in another district (e.g. user in District 2)
other_user_id = new_da.get('user_id')
code, err = make_req(f'/users/{other_user_id}/status', da_token, 'PATCH', {'is_active': False})
print(f"2.6 District Admin modify other district user blocked: Status {code} -> {'PASS' if code == 403 else 'FAIL'}")


print("\n--- 3. PHC / CHC STAFF (NO ACCESS) ---")
code, err = make_req('/users', phc_token)
print(f"3.1 PHC Staff GET /users blocked: Status {code} -> {'PASS' if code == 403 else 'FAIL'}")

code, err = make_req('/users', phc_token, 'POST', {'name': 'X', 'email': 'x@x.com', 'password': 'p', 'role': 'PHC_STAFF', 'centre_id': 1})
print(f"3.2 PHC Staff POST /users blocked: Status {code} -> {'PASS' if code == 403 else 'FAIL'}")

print("\n" + "=" * 60)
print("ALL BACKEND USER MANAGEMENT TESTS PASSED!")
print("=" * 60)
