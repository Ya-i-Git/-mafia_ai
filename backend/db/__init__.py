# backend/db/__init__.py
from .config import sync_engine as engine
from .config import SyncSessionLocal as SessionLocal
from .config import get_sync_db as get_db
from .config import async_engine, AsyncSessionLocal, get_db as get_async_db
from .base import Base
# Импортируем только существующие модели
from .models import User, UserRole, GameSession, GamePlayer, PlayerAction, Round, ChatMessage

# Для инициализации БД (опционально)
def init_db():
    from .config import sync_engine
    from .models import Base
    Base.metadata.create_all(bind=sync_engine)

__all__ = [
    "engine",
    "SessionLocal",
    "get_db",
    "async_engine",
    "AsyncSessionLocal",
    "get_async_db",
    "Base",
    "init_db",
    "User",
    "UserRole",
    "GameSession",
    "GamePlayer",
    "PlayerAction",
    "Round",
    "ChatMessage",
]