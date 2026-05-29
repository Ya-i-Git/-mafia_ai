import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from db import SessionLocal, User
from db.models.user import UserRole

def create_admin():
    db = SessionLocal()
    
    admin = db.query(User).filter(User.username == "admin").first()
    if not admin:
        admin = User(
            username="admin",
            email="admin@mafia-game.com",
            role=UserRole.ADMIN,
            is_verified=True
        )
        admin.set_password("admin123")
        db.add(admin)
        db.commit()
        print("Admin user created successfully!")
    else:
        print("Admin user already exists")
    
    db.close()

if __name__ == "__main__":
    create_admin()