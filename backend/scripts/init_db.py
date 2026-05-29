#!/usr/bin/env python
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from db import engine, SessionLocal, Base
from db.models import User

def init_database():
    """Создание всех таблиц"""
    print("📦 Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created successfully!")

def create_admin():
    """Создание администратора"""
    db = SessionLocal()
    
    admin = db.query(User).filter(User.username == "admin").first()
    if not admin:
        admin = User(
            username="admin",
            email="admin@mafia-game.com",
            role="admin",
            is_verified=True
        )
        admin.set_password("admin123")
        db.add(admin)
        db.commit()
        print("✅ Admin user created: username='admin', password='admin123'")
    else:
        print("ℹ️ Admin user already exists")
    
    db.close()

if __name__ == "__main__":
    init_database()
    create_admin()