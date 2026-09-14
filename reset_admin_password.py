from app.database.connection import SessionLocal
from app.models.user import User
from app.services.auth import hash_password


NEW_PASSWORD = "Admin@12345"
ADMIN_EMAIL = "test@example.com"


db = SessionLocal()

try:
    user = db.query(User).filter(
        User.email == ADMIN_EMAIL
    ).first()

    if user is None:
        print("User not found.")
    else:
        new_hash = hash_password(NEW_PASSWORD)

        print("Generated hash type:", new_hash[:4])
        print("Generated hash length:", len(new_hash))

        user.password_hash = new_hash
        user.role = "admin"
        user.is_active = True

        db.commit()
        db.refresh(user)

        print("Password reset successfully.")
        print("Email:", user.email)
        print("Role:", user.role)
        print("Hash stored:", user.password_hash[:4])
        print("Stored hash length:", len(user.password_hash))

finally:
    db.close()