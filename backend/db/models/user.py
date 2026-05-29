from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import hashlib
import secrets
import enum
import uuid

from ..base import Base

class UserRole(str, enum.Enum):
    PLAYER = "player"
    MODERATOR = "moderator"
    ADMIN = "admin"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()), nullable=False)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=True, index=True)
    hashed_password = Column(String(255), nullable=False)
    salt = Column(String(64), nullable=True)
    
    avatar_url = Column(String(500), nullable=True)
    role = Column(SQLEnum(UserRole), default=UserRole.PLAYER)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    total_games = Column(Integer, default=0)
    total_wins = Column(Integer, default=0)
    total_losses = Column(Integer, default=0)
    total_kills = Column(Integer, default=0)
    total_deaths = Column(Integer, default=0)
    
    rating = Column(Float, default=1000.0)
    rank = Column(String(50), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    last_active = Column(DateTime(timezone=True), nullable=True)
    
    preferences = Column(JSON, default=dict)
    
    def set_password(self, password: str):
        """Хеширование пароля с солью"""
        self.salt = secrets.token_hex(32)
        # Обрезаем пароль до 100 символов
        password = password[:100] if len(password) > 100 else password
        self.hashed_password = hashlib.pbkdf2_hmac(
            sha256,
            password.encode(utf-8),
            self.salt.encode(utf-8),
            100000
        ).hex()
    
    def verify_password(self, password: str) -> bool:
        """Проверка пароля"""
        if not self.salt:
            return False
        test_hash = hashlib.pbkdf2_hmac(
            sha256,
            password.encode(utf-8),
            self.salt.encode(utf-8),
            100000
        ).hex()
        return secrets.compare_digest(self.hashed_password, test_hash)
    
    def to_dict(self, include_sensitive=False):
        data = {
            "id": self.id,
            "username": self.username,
            "email": self.email if include_sensitive else None,
            "role": self.role.value,
            "total_games": self.total_games,
            "total_wins": self.total_wins,
            "rating": round(self.rating, 0),
            "rank": self.rank,
        }
        if not include_sensitive:
            data.pop("email", None)
        return data
