# backend/db/config.py
import os
from dotenv import load_dotenv
from pathlib import Path
from typing import AsyncGenerator

env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

class DatabaseConfig:
    POSTGRES_USER = os.getenv("POSTGRES_USER", "mafia")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "mafia")
    POSTGRES_DB = os.getenv("POSTGRES_DB", "mafia")
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres")
    POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
    
    @classmethod
    def get_database_url(cls) -> str:
        return f"postgresql://{cls.POSTGRES_USER}:{cls.POSTGRES_PASSWORD}@{cls.POSTGRES_HOST}:{cls.POSTGRES_PORT}/{cls.POSTGRES_DB}"
    
    @classmethod
    def get_async_database_url(cls) -> str:
        return f"postgresql+asyncpg://{cls.POSTGRES_USER}:{cls.POSTGRES_PASSWORD}@{cls.POSTGRES_HOST}:{cls.POSTGRES_PORT}/{cls.POSTGRES_DB}"

# Синхронный движок для миграций и простых операций
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

sync_engine = create_engine(
    DatabaseConfig.get_database_url(),
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

SyncSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=sync_engine
)

def get_sync_db() -> Session:
    db = SyncSessionLocal()
    try:
        yield db
    finally:
        db.close()

# Асинхронный движок для FastAPI
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

async_engine = create_async_engine(
    DatabaseConfig.get_async_database_url(),
    echo=False,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()