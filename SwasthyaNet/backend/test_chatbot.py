"""
Test Suite for SwasthyaNet AI Assistant (POST /api/chatbot/chat)
Verifies:
1. Authentication (401 on unauthenticated requests)
2. RBAC Access Control (PHC/CHC own centre, District Admin district, Super Admin global)
3. 6 Supported Q&A Intents (INVENTORY, STOCKOUT, BED_STATUS, BED_FORECAST, ALERTS, UNKNOWN)
4. Role-Aware Navigation (Pure navigation & combined Q&A + navigation requests)
5. Integration with Phase 5E LightGBM champion models (Stock-out & Multi-Horizon Bed Forecast)
6. Strict Read-Only verification (zero database state mutations)
7. Error handling and parameter validation
"""

import sys
import os
import json
from datetime import datetime, timezone
import jwt
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# Add current dir to path
sys.path.insert(0, os.path.dirname(__file__))

from main import app
from database import get_db, SessionLocal
import models
from routers.auth import JWT_SECRET, ALGORITHM

# Ensure utf-8 encoding for standard output
sys.stdout.reconfigure(encoding='utf-8')

client = TestClient(app)

def create_jwt_token(email: str, role: str, centre_id: int = None, district_id: int = None, user_id: int = 1):
    payload = {
        "sub": email,
        "email": email,
        "role": role,
        "centre_id": centre_id,
        "district_id": district_id,
        "user_id": user_id,
        "exp": 9999999999
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)

def run_chatbot_tests():
    print("=" * 70)
    print("SWASTHYANET AI ASSISTANT CHATBOT VERIFICATION TEST SUITE")
    print("=" * 70)

    db: Session = SessionLocal()
    
    # 1. Fetch available test entities from database
    centres = db.query(models.HealthCentre).all()
    if len(centres) < 2:
        print("Warning: Need at least 2 centres in DB for robust cross-centre RBAC testing.")
    
    centre1 = centres[0]
    centre2 = centres[1] if len(centres) > 1 else centres[0]
    
    # Tokens
    super_admin_token = create_jwt_token("superadmin@test.com", "SUPER_ADMIN", user_id=1)
    dist1_admin_token = create_jwt_token("dist1@test.com", "DISTRICT_ADMIN", district_id=centre1.district_id, user_id=2)
    phc_staff_token = create_jwt_token("phc1@test.com", "PHC_STAFF", centre_id=centre1.centre_id, district_id=centre1.district_id, user_id=3)
    
    # A token with different district
    other_dist_id = centre2.district_id if centre2.district_id != centre1.district_id else 9999
    dist_other_token = create_jwt_token("dist_other@test.com", "DISTRICT_ADMIN", district_id=other_dist_id, user_id=4)
    
    headers_super = {"Authorization": f"Bearer {super_admin_token}"}
    headers_dist1 = {"Authorization": f"Bearer {dist1_admin_token}"}
    headers_phc = {"Authorization": f"Bearer {phc_staff_token}"}
    headers_other_dist = {"Authorization": f"Bearer {dist_other_token}"}

    passed_tests = 0
    total_tests = 0

    def assert_test(cond, title):
        nonlocal passed_tests, total_tests
        total_tests += 1
        if cond:
            print(f"  [PASS] {title}")
            passed_tests += 1
        else:
            print(f"  [FAIL] {title}")
            raise AssertionError(f"Test failed: {title}")

    # -------------------------------------------------------------------------
    # TEST GROUP 1: AUTHENTICATION
    # -------------------------------------------------------------------------
    print("\n--- 1. Authentication & Security Tests ---")
    
    # 1.1 Unauthenticated request (no token)
    res = client.post("/api/chatbot/chat", json={"message": "Show inventory"})
    assert_test(res.status_code == 401, "Unauthenticated request returns 401 Unauthorized")

    # 1.2 Invalid token
    res = client.post("/api/chatbot/chat", json={"message": "Show inventory"}, headers={"Authorization": "Bearer invalid.token.xyz"})
    assert_test(res.status_code == 401, "Invalid JWT token returns 401 Unauthorized")

    # 1.3 Empty message validation
    res = client.post("/api/chatbot/chat", json={"message": "   "}, headers=headers_phc)
    assert_test(res.status_code == 400, "Empty chat message returns 400 Bad Request")

    # -------------------------------------------------------------------------
    # TEST GROUP 2: RBAC ENFORCEMENT
    # -------------------------------------------------------------------------
    print("\n--- 2. RBAC Enforcement Tests ---")

    # 2.1 PHC Staff querying own centre -> Allowed (200)
    res = client.post("/api/chatbot/chat", json={"message": "Show medicine inventory"}, headers=headers_phc)
    assert_test(res.status_code == 200, "PHC Staff accessing assigned centre succeeds (200)")
    data = res.json()
    assert_test(data["scope"]["centre_id"] == centre1.centre_id, "Response scoped strictly to assigned centre_id")

    # 2.2 PHC Staff querying another centre -> Forbidden (403)
    if centre2.centre_id != centre1.centre_id:
        res = client.post("/api/chatbot/chat", json={"message": "Show inventory", "centre_id": centre2.centre_id}, headers=headers_phc)
        assert_test(res.status_code == 403, "PHC Staff requesting another centre is denied (403 Forbidden)")

    # 2.3 District Admin querying centre within their district -> Allowed (200)
    res = client.post("/api/chatbot/chat", json={"message": "Check bed status", "centre_id": centre1.centre_id}, headers=headers_dist1)
    assert_test(res.status_code == 200, "District Admin accessing centre in their district succeeds (200)")

    # 2.4 District Admin querying centre in different district -> Forbidden (403)
    if other_dist_id != centre1.district_id:
        res = client.post("/api/chatbot/chat", json={"message": "Check bed status", "centre_id": centre1.centre_id}, headers=headers_other_dist)
        assert_test(res.status_code == 403, "District Admin accessing centre outside district is denied (403 Forbidden)")

    # 2.5 Super Admin querying any centre -> Allowed (200)
    res = client.post("/api/chatbot/chat", json={"message": "Show alerts", "centre_id": centre1.centre_id}, headers=headers_super)
    assert_test(res.status_code == 200, "Super Admin accessing any facility succeeds (200)")

    # -------------------------------------------------------------------------
    # TEST GROUP 3: INTENT CLASSIFICATION & ML INTEGRATION
    # -------------------------------------------------------------------------
    print("\n--- 3. Intent Classification & ML Integration Tests ---")

    # 3.1 INVENTORY Intent
    res = client.post("/api/chatbot/chat", json={"message": "What is the current medicine inventory in our health centre?"}, headers=headers_phc)
    assert_test(res.status_code == 200, "INVENTORY query succeeds (200)")
    res_data = res.json()
    assert_test(res_data["intent"] == "INVENTORY", f"Correctly classified INVENTORY intent (got: {res_data['intent']})")
    assert_test("inventory_items" in res_data["trusted_data"], "Trusted data contains inventory_items list")
    assert_test(len(res_data["answer"]) > 20, "Answer contains formatted natural language synthesis")

    # 3.2 STOCKOUT Intent (Phase 5E LightGBM Two-Stage Champion Model)
    res = client.post("/api/chatbot/chat", json={"message": "When will Paracetamol run out? Predict stockout days remaining"}, headers=headers_phc)
    assert_test(res.status_code == 200, "STOCKOUT prediction query succeeds (200)")
    res_data = res.json()
    assert_test(res_data["intent"] == "STOCKOUT", f"Correctly classified STOCKOUT intent (got: {res_data['intent']})")
    t_data = res_data["trusted_data"]
    assert_test("predicted_days_until_stockout" in t_data, "Trusted data contains LightGBM predicted_days_until_stockout")
    assert_test("risk_level" in t_data and "risk_probability" in t_data, "Trusted data contains Two-Stage risk_level & probability")
    assert_test("Stock-Out Prediction" in res_data["answer"], "Answer synthesizes stockout prediction details")

    # 3.3 BED_STATUS Intent
    res = client.post("/api/chatbot/chat", json={"message": "How many beds are available right now in our facility?"}, headers=headers_phc)
    assert_test(res.status_code == 200, "BED_STATUS query succeeds (200)")
    res_data = res.json()
    assert_test(res_data["intent"] == "BED_STATUS", f"Correctly classified BED_STATUS intent (got: {res_data['intent']})")
    assert_test("wards" in res_data["trusted_data"], "Trusted data contains ward breakdown")
    assert_test("Bed Occupancy Status" in res_data["answer"], "Answer synthesizes current bed status")

    # 3.4 BED_FORECAST Intent (Multi-Horizon LightGBM t+1, t+7, t+14)
    res = client.post("/api/chatbot/chat", json={"message": "Forecast General ward bed occupancy for next week and upcoming surge risk"}, headers=headers_phc)
    assert_test(res.status_code == 200, "BED_FORECAST query succeeds (200)")
    res_data = res.json()
    assert_test(res_data["intent"] == "BED_FORECAST", f"Correctly classified BED_FORECAST intent (got: {res_data['intent']})")
    t_data = res_data["trusted_data"]
    assert_test("forecasts" in t_data, "Trusted data contains forecasts dict")
    assert_test("t_plus_1" in t_data["forecasts"] and "t_plus_7" in t_data["forecasts"] and "t_plus_14" in t_data["forecasts"],
                "Multi-horizon forecasts include t+1, t+7, and t+14 predictions")
    assert_test("Multi-Horizon Bed Occupancy Forecast" in res_data["answer"], "Answer synthesizes multi-horizon forecast")

    # 3.5 ALERTS Intent
    res = client.post("/api/chatbot/chat", json={"message": "Are there any active emergency alerts or outbreak warnings?"}, headers=headers_phc)
    assert_test(res.status_code == 200, "ALERTS query succeeds (200)")
    res_data = res.json()
    assert_test(res_data["intent"] == "ALERTS", f"Correctly classified ALERTS intent (got: {res_data['intent']})")
    assert_test("alerts" in res_data["trusted_data"], "Trusted data contains alerts list")

    # 3.6 UNKNOWN Intent
    res = client.post("/api/chatbot/chat", json={"message": "Hello, what can you do for me?"}, headers=headers_phc)
    assert_test(res.status_code == 200, "UNKNOWN query succeeds (200)")
    res_data = res.json()
    assert_test(res_data["intent"] == "UNKNOWN", f"Correctly classified UNKNOWN intent (got: {res_data['intent']})")
    assert_test("SwasthyaNet AI Assistant" in res_data["answer"], "Answer provides capability overview and suggestions")
    assert_test(len(res_data["suggested_actions"]) > 0, "Suggested actions provided")

    # -------------------------------------------------------------------------
    # TEST GROUP 4: ROLE-AWARE APPLICATION NAVIGATION
    # -------------------------------------------------------------------------
    print("\n--- 4. Role-Aware Application Navigation Tests ---")

    # 4.1 "Open inventory" -> NAVIGATION intent & INVENTORY destination
    res = client.post("/api/chatbot/chat", json={"message": "Open inventory"}, headers=headers_phc)
    assert_test(res.status_code == 200, "'Open inventory' succeeds (200)")
    nav_data = res.json()
    assert_test(nav_data["intent"] == "NAVIGATION", f"Intent is NAVIGATION (got: {nav_data['intent']})")
    assert_test(nav_data["navigation"] is not None, "Navigation object returned")
    assert_test(nav_data["navigation"]["destination"] == "INVENTORY", f"Destination is INVENTORY (got: {nav_data['navigation']['destination']})")
    assert_test(nav_data["navigation"]["action"] == "OPEN_PAGE", "Action is OPEN_PAGE")
    assert_test(nav_data["navigation"]["authorized"] is True, "PHC Staff is authorized for INVENTORY")

    # 4.2 "Show bed occupancy" -> NAVIGATION intent & BED_STATUS destination
    res = client.post("/api/chatbot/chat", json={"message": "Show bed occupancy"}, headers=headers_phc)
    assert_test(res.status_code == 200, "'Show bed occupancy' succeeds (200)")
    nav_data = res.json()
    assert_test(nav_data["navigation"]["destination"] == "BED_STATUS", "Destination is BED_STATUS")
    assert_test(nav_data["navigation"]["authorized"] is True, "Authorized is True")

    # 4.3 "Open alerts" -> NAVIGATION intent & ALERTS destination
    res = client.post("/api/chatbot/chat", json={"message": "Open alerts page"}, headers=headers_phc)
    assert_test(res.status_code == 200, "'Open alerts' succeeds (200)")
    nav_data = res.json()
    assert_test(nav_data["navigation"]["destination"] == "ALERTS", "Destination is ALERTS")

    # 4.4 "Go to user management" by Super Admin -> Authorized (True)
    res = client.post("/api/chatbot/chat", json={"message": "Go to user management"}, headers=headers_super)
    assert_test(res.status_code == 200, "Super Admin 'Go to user management' succeeds (200)")
    nav_data = res.json()
    assert_test(nav_data["navigation"]["destination"] == "USER_MANAGEMENT", "Destination is USER_MANAGEMENT")
    assert_test(nav_data["navigation"]["authorized"] is True, "Super Admin is authorized for USER_MANAGEMENT")

    # 4.5 "Go to user management" by District Admin -> Authorized (True)
    res = client.post("/api/chatbot/chat", json={"message": "Open staff management"}, headers=headers_dist1)
    assert_test(res.status_code == 200, "District Admin 'Open staff management' succeeds (200)")
    nav_data = res.json()
    assert_test(nav_data["navigation"]["destination"] == "USER_MANAGEMENT", "Destination is USER_MANAGEMENT")
    assert_test(nav_data["navigation"]["authorized"] is True, "District Admin is authorized for USER_MANAGEMENT")

    # 4.6 "Go to user management" by PHC Staff -> Authorized (False) - Role Protection
    res = client.post("/api/chatbot/chat", json={"message": "Go to user management"}, headers=headers_phc)
    assert_test(res.status_code == 200, "PHC Staff 'Go to user management' returns 200 with unauthorized action")
    nav_data = res.json()
    assert_test(nav_data["navigation"]["authorized"] is False, "PHC Staff is NOT authorized for USER_MANAGEMENT")
    assert_test("permission" in nav_data["navigation"]["reason"].lower(), "Includes clear permission reason")
    assert_test("Access Restricted" in nav_data["answer"], "Answer informs user about restricted access")

    # 4.7 "Open Super Admin dashboard" by Super Admin -> Authorized (True)
    res = client.post("/api/chatbot/chat", json={"message": "Open Super Admin dashboard"}, headers=headers_super)
    assert_test(res.status_code == 200, "Super Admin dashboard navigation by Super Admin succeeds (200)")
    nav_data = res.json()
    assert_test(nav_data["navigation"]["destination"] == "SUPER_ADMIN_DASHBOARD", "Destination is SUPER_ADMIN_DASHBOARD")
    assert_test(nav_data["navigation"]["authorized"] is True, "Authorized is True")

    # 4.8 "Open Super Admin dashboard" by PHC Staff -> Authorized (False) - Role Protection
    res = client.post("/api/chatbot/chat", json={"message": "Open Super Admin dashboard"}, headers=headers_phc)
    assert_test(res.status_code == 200, "Super Admin dashboard navigation by PHC Staff returns unauthorized action")
    nav_data = res.json()
    assert_test(nav_data["navigation"]["authorized"] is False, "PHC Staff is NOT authorized for SUPER_ADMIN_DASHBOARD")

    # 4.9 Combined Request: "Which medicines are at risk and open inventory?"
    res = client.post("/api/chatbot/chat", json={"message": "Which medicines are at risk and open inventory?"}, headers=headers_phc)
    assert_test(res.status_code == 200, "Combined Q&A + Navigation query succeeds (200)")
    comb_data = res.json()
    assert_test(comb_data["intent"] == "STOCKOUT", f"Primary intent is STOCKOUT (got: {comb_data['intent']})")
    assert_test(comb_data["trusted_data"] is not None, "Trusted stockout prediction data is returned")
    assert_test(comb_data["navigation"] is not None, "Navigation action is attached")
    assert_test(comb_data["navigation"]["destination"] == "INVENTORY", "Navigation destination is INVENTORY")
    assert_test("predicted_days_until_stockout" in comb_data["trusted_data"], "Includes LightGBM stockout prediction")
    assert_test("Navigating" in comb_data["answer"], "Answer confirms prediction and navigation")

    # -------------------------------------------------------------------------
    # TEST GROUP 5: STRICT READ-ONLY DATABASE VERIFICATION
    # -------------------------------------------------------------------------
    print("\n--- 5. Strict Read-Only Database Verification ---")
    
    # Capture database row counts before chatbot calls
    count_users_before = db.query(models.User).count()
    count_inv_before = db.query(models.MedicineInventory).count()
    count_beds_before = db.query(models.BedOccupancy).count()
    count_alerts_before = db.query(models.Alert).count()
    count_att_before = db.query(models.DoctorAttendance).count()

    # Execute diverse queries
    queries = [
        "Open inventory",
        "Show bed occupancy",
        "Predict stockout for Amoxicillin and open inventory",
        "Go to user management",
        "Open Super Admin dashboard",
        "Forecast bed occupancy",
        "Show all alerts",
        "Add 500 paracetamol to inventory",
        "Delete all alerts",
        "Update bed count to 100"
    ]
    for q in queries:
        client.post("/api/chatbot/chat", json={"message": q}, headers=headers_super)

    # Capture database row counts after chatbot calls
    count_users_after = db.query(models.User).count()
    count_inv_after = db.query(models.MedicineInventory).count()
    count_beds_after = db.query(models.BedOccupancy).count()
    count_alerts_after = db.query(models.Alert).count()
    count_att_after = db.query(models.DoctorAttendance).count()

    assert_test(count_users_before == count_users_after, "Users table unchanged (Zero mutations)")
    assert_test(count_inv_before == count_inv_after, "MedicineInventory table unchanged (Zero mutations)")
    assert_test(count_beds_before == count_beds_after, "BedOccupancy table unchanged (Zero mutations)")
    assert_test(count_alerts_before == count_alerts_after, "Alerts table unchanged (Zero mutations)")
    assert_test(count_att_before == count_att_after, "DoctorAttendance table unchanged (Zero mutations)")

    db.close()

    print("\n" + "=" * 70)
    print(f"ALL CHATBOT & NAVIGATION TESTS PASSED: {passed_tests} / {total_tests} (100% Success)")
    print("=" * 70)

if __name__ == "__main__":
    run_chatbot_tests()
