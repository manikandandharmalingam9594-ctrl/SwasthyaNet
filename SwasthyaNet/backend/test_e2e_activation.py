from database import SessionLocal
import models
from email_service import create_activation_token, verify_activation_token, generate_temporary_password
from routers.auth import get_password_hash, verify_password, create_access_token

def test_full_lifecycle():
    db = SessionLocal()
    try:
        print("=== TEST 1: User Creation with Automatic Password & Activation Flag ===")
        test_email = "test.auto.doctor@swasthyanet.gov.in"
        existing = db.query(models.User).filter(models.User.email == test_email).first()
        if existing:
            db.delete(existing)
            db.commit()

        # Step 1: Auto-generate temporary password
        temp_pwd = generate_temporary_password(12)
        new_user = models.User(
            name="Dr. Automated Test",
            email=test_email,
            password_hash=get_password_hash(temp_pwd),
            role="PHC_STAFF",
            district_id=1,
            centre_id=1,
            is_active=True,
            is_activated=False,
            must_change_password=True
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        print(f"[PASS] User created with ID {new_user.user_id}")
        assert new_user.is_activated is False
        assert new_user.must_change_password is True
        assert verify_password(temp_pwd, new_user.password_hash) is True

        print("\n=== TEST 2: Verify Activation Token ===")
        token = create_activation_token(user_id=new_user.user_id, email=new_user.email, role=new_user.role)
        payload = verify_activation_token(token)
        assert payload["user_id"] == new_user.user_id
        print(f"[PASS] Activation Token valid for user {payload['sub']}")

        print("\n=== TEST 3: Account Activation & Password Setup ===")
        new_permanent_password = "DoctorPermanentPass#2026"
        new_user.password_hash = get_password_hash(new_permanent_password)
        new_user.is_activated = True
        new_user.must_change_password = False
        db.commit()
        db.refresh(new_user)

        assert new_user.is_activated is True
        assert new_user.must_change_password is False
        assert verify_password(new_permanent_password, new_user.password_hash) is True
        assert verify_password(temp_pwd, new_user.password_hash) is False
        print("[PASS] User account activated and permanent password stored")

        print("\n=== TEST 4: Resend Activation Invite Flow ===")
        # Simulate resending invite
        new_temp_pwd = generate_temporary_password(12)
        new_user.password_hash = get_password_hash(new_temp_pwd)
        new_user.is_activated = False
        new_user.must_change_password = True
        db.commit()
        db.refresh(new_user)

        assert new_user.is_activated is False
        assert verify_password(new_temp_pwd, new_user.password_hash) is True
        print("[PASS] Resend invite generated new temporary password and reset activation status")

        # Cleanup
        db.delete(new_user)
        db.commit()
        print("\n[PASS] All lifecycle stages verified and cleaned up successfully!")

    finally:
        db.close()

if __name__ == "__main__":
    test_full_lifecycle()
