from database import SessionLocal
import models
from routers.auth import get_password_hash

db = SessionLocal()
users = db.query(models.User).all()
print(f"Total users: {len(users)}")
for u in users:
    print(u.user_id, u.email, u.role)

# Update the first user's password to a known one for testing
if users:
    test_user = users[0]
    test_user.password_hash = get_password_hash("testpassword123")
    db.commit()
    print(f"Updated password for user {test_user.email} to 'testpassword123'")
else:
    # create a user
    test_user = models.User(
        name="Test Admin",
        email="admin@swasthyanet.com",
        password_hash=get_password_hash("testpassword123"),
        role="DISTRICT_ADMIN",
        centre_id=1,
        language="EN",
        is_active=True,
        district_id=1
    )
    db.add(test_user)
    db.commit()
    print("Created test user admin@swasthyanet.com")
