import sys
from database import SessionLocal
import models
from email_service import generate_temporary_password, create_activation_token, verify_activation_token
from routers.auth import get_password_hash, verify_password

def run_activation_unit_tests():
    print("=== SWASTHYANET ACCOUNT ACTIVATION BACKEND TESTS ===")
    
    # 1. Test Password Generation
    pwd1 = generate_temporary_password(12)
    pwd2 = generate_temporary_password(14)
    print(f"Generated temp password 1: {pwd1} (len={len(pwd1)})")
    print(f"Generated temp password 2: {pwd2} (len={len(pwd2)})")
    assert len(pwd1) == 12, "Password length mismatch"
    assert any(c.isupper() for c in pwd1), "Missing uppercase"
    assert any(c.islower() for c in pwd1), "Missing lowercase"
    assert any(c.isdigit() for c in pwd1), "Missing digit"
    assert any(c in "@#$%&*!" for c in pwd1), "Missing special char"
    print("[PASS] 1. Temporary password generator passed")

    # 2. Test Token Generation & Verification
    token = create_activation_token(user_id=9999, email="test.doctor@swasthyanet.gov.in", role="PHC_STAFF")
    print(f"Generated token: {token[:25]}...")
    payload = verify_activation_token(token)
    assert payload["user_id"] == 9999
    assert payload["sub"] == "test.doctor@swasthyanet.gov.in"
    assert payload["role"] == "PHC_STAFF"
    assert payload["purpose"] == "account_activation"
    print("[PASS] 2. JWT Activation Token verification passed")

    # 3. Test Database User Creation & Activation Lifecycle
    db = SessionLocal()
    try:
        test_email = "test.newstaff.activate@swasthyanet.gov.in"
        # Cleanup if exists
        existing = db.query(models.User).filter(models.User.email == test_email).first()
        if existing:
            db.delete(existing)
            db.commit()

        # Create user with temp password and is_activated=False
        temp_pwd = generate_temporary_password(12)
        u = models.User(
            name="Dr. Testing Activation",
            email=test_email,
            password_hash=get_password_hash(temp_pwd),
            role="PHC_STAFF",
            district_id=1,
            centre_id=1,
            is_active=True,
            is_activated=False,
            must_change_password=True
        )
        db.add(u)
        db.commit()
        db.refresh(u)
        print(f"[PASS] 3. Created test user ID={u.user_id}, is_activated={u.is_activated}, must_change_password={u.must_change_password}")

        # Verify temp password works
        assert verify_password(temp_pwd, u.password_hash) is True
        print("[PASS] 4. Temporary password verification against password_hash passed")

        # Simulate user activation with new password
        new_perm_pwd = "MyNewSecurePassword!2026"
        u.password_hash = get_password_hash(new_perm_pwd)
        u.is_activated = True
        u.must_change_password = False
        db.commit()
        db.refresh(u)

        assert u.is_activated is True
        assert u.must_change_password is False
        assert verify_password(new_perm_pwd, u.password_hash) is True
        assert verify_password(temp_pwd, u.password_hash) is False
        print("[PASS] 5. Account activation & permanent password change lifecycle passed!")

        # Cleanup
        db.delete(u)
        db.commit()
        print("[PASS] 6. Cleanup completed successfully")

    finally:
        db.close()

    print("ALL ACTIVATION BACKEND TESTS PASSED!")

if __name__ == "__main__":
    run_activation_unit_tests()
