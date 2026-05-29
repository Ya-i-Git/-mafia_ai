from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from typing import Generator
import os

# Загрузка переменных окружения
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://mafia:mafia@postgres:5432/mafia")

# Создание engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=10,
    echo=os.getenv("SQL_ECHO", "False").lower() == "true"
)

# Создание фабрики сессий
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator:
    """Зависимость FastAPI для получения сессии БД"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()