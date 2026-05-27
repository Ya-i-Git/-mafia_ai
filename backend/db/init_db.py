# backend/db/init_db.py
import asyncio
from backend.db.config import async_engine, DatabaseConfig
from backend.db.models import Base
from backend.db.repositories.user_repository import UserRepository
from sqlalchemy.ext.asyncio import AsyncSession

async def init_database():
    """Инициализация базы данных"""
    print("Creating database tables...")
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables created successfully!")

async def create_admin_user():
    """Создание администратора (опционально)"""
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.orm import sessionmaker
    
    async_session = sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        repo = UserRepository(session)
        existing_admin = await repo.get_user_by_username("admin")
        
        if not existing_admin:
            admin = await repo.create_user("admin", "admin123", "admin@mafia.com")
            print(f"Admin user created: {admin.username}")
        else:
            print("Admin user already exists")

if __name__ == "__main__":
    asyncio.run(init_database())
    asyncio.run(create_admin_user())
    print("Database initialization complete!")