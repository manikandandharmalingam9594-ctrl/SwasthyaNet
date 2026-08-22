import urllib.request, json
from database import SessionLocal
import models, routers.auth

db = SessionLocal()
u = db.query(models.User).filter(models.User.email == 'staff06@swasthyanet.com').first()
token = routers.auth.create_access_token({'sub': u.email, 'role': u.role, 'centre_id': u.centre_id})
headers = {'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'}

def api_get(path):
    req = urllib.request.Request('http://localhost:8000/api' + path, headers=headers)
    return json.loads(urllib.request.urlopen(req).read())

def api_put(path, payload):
    req = urllib.request.Request('http://localhost:8000/api' + path, method='PUT', headers=headers)
    try:
        res = urllib.request.urlopen(req, json.dumps(payload).encode())
        return res.getcode(), json.loads(res.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())

def api_post(path, payload):
    req = urllib.request.Request('http://localhost:8000/api' + path, method='POST', headers=headers)
    try:
        res = urllib.request.urlopen(req, json.dumps(payload).encode())
        return res.getcode(), json.loads(res.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())

cid = u.centre_id
c = api_get('/centres/' + str(cid))
print('TEST 1 Centre:', c['centre_name'], c['centre_type'])

sc = api_get('/centres/' + str(cid) + '/health-score')
print('TEST 2 Health Score:', sc[0]['score'] if sc else 'N/A')

inv = api_get('/centres/' + str(cid) + '/inventory')
print('TEST 3 Inventory items:', len(inv))
if inv:
    i = inv[0]; before = i['current_stock']
    code, r = api_put('/inventory/' + str(i['inventory_id']), {'quantity': 15, 'transaction_type': 'IN'})
    print('TEST 4 IN: HTTP', code, 'stock', before, '->', r.get('current_stock'))

wards = api_get('/centres/' + str(cid) + '/wards')
print('TEST 5 Wards:', len(wards))
if wards:
    code, r = api_put('/wards/' + str(wards[0]['ward_id']) + '/occupancy', {'occupied_beds': 5, 'recorded_at': '2026-08-16T13:05:00'})
    print('TEST 6 Beds: HTTP', code)

docs = api_get('/centres/' + str(cid) + '/doctors')
print('TEST 7 Doctors:', len(docs))
if docs:
    code, r = api_post('/attendance', {'doctor_id': docs[0]['doctor_id'], 'attendance_date': '2026-08-16', 'status': 'PRESENT'})
    print('TEST 8 Attendance: HTTP', code, r.get('status'))

alerts = api_get('/centres/' + str(cid) + '/alerts')
print('TEST 9 Alerts:', len(alerts))

req2 = urllib.request.Request('http://localhost:8000/api/centres/1', headers=headers)
try:
    urllib.request.urlopen(req2)
    print('TEST 10 FAIL cross-centre NOT blocked')
except urllib.error.HTTPError as e:
    print('TEST 10 PASS cross-centre blocked HTTP', e.code)
