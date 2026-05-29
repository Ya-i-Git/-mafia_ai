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
    salt = Column(String(64), nullable=True)  # Соль для пароля
    
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
    
    # Связи
    games_played = relationship("GamePlayer", back_populates="user", cascade="all, delete-orphan", foreign_keys="GamePlayer.user_id")
    created_games = relationship("GameSession", back_populates="creator", foreign_keys="GameSession.created_by_id")
    chat_messages = relationship("ChatMessage", back_populates="user", foreign_keys="ChatMessage.user_id")
    sent_actions = relationship("PlayerAction", back_populates="user", foreign_keys="PlayerAction.user_id")
    
    def set_password(self, password: str):
        """Хеширование пароля с солью"""
        self.salt = secrets.token_hex(32)
        self.hashed_password = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            self.salt.encode('utf-8'),
            100000
        ).hex()
    
    def verify_password(self, password: str) -> bool:
        """Проверка пароля"""
        if not self.salt:
            return False
        test_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            self.salt.encode('utf-8'),
            100000
        ).hex()
        return secrets.compare_digest(self.hashed_password, test_hash)
    
    def update_stats(self, won: bool = None, kills: int = 0, died: bool = False):
        if won is not None:
            self.total_games += 1
            if won:
                self.total_wins += 1
            else:
                self.total_losses += 1
        
        self.total_kills += kills
        if died:
            self.total_deaths += 1
    
    def update_rating(self, delta: float):
        self.rating += delta
        self.rating = max(0, min(3000, self.rating))
        self._update_rank()
    
    def _update_rank(self):
        if self.rating >= 2400:
            self.rank = "Legend"
        elif self.rating >= 2200:
            self.rank = "Grandmaster"
        elif self.rating >= 2000:
            self.rank = "Master"
        elif self.rating >= 1800:
            self.rank = "Diamond"
        elif self.rating >= 1600:
            self.rank = "Platinum"
        elif self.rating >= 1400:
            self.rank = "Gold"
        elif self.rating >= 1200:
            self.rank = "Silver"
        else:
            self.rank = "Bronze"
    
    def to_dict(self, include_sensitive=False):
        data = {
            "id": self.id,
            "uuid": self.uuid,
            "username": self.username,
            "email": self.email if include_sensitive else None,
            "avatar_url": self.avatar_url,
            "role": self.role.value,
            "total_games": self.total_games,
            "total_wins": self.total_wins,
            "total_losses": self.total_losses,
            "total_kills": self.total_kills,
            "total_deaths": self.total_deaths,
            "win_rate": round(self.total_wins / self.total_games * 100, 2) if self.total_games > 0 else 0,
            "kda": round(self.total_kills / max(1, self.total_deaths), 2),
            "rating": round(self.rating, 0),
            "rank": self.rank,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "preferences": self.preferences
        }
        if not include_sensitive:
            data.pop("email", None)
        return data