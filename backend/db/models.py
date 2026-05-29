# backend/db/models.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Float, Text, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

Base = declarative_base()

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    PLAYER = "player"

class GameRole(str, enum.Enum):
    MAFIA = "mafia"
    DON = "don"
    SHERIFF = "sheriff"
    DOCTOR = "doctor"
    CIVILIAN = "civilian"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    email = Column(String(100), unique=True, nullable=True)
    role = Column(SQLEnum(UserRole), default=UserRole.PLAYER)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    game_stats = relationship("GameStats", back_populates="user", cascade="all, delete-orphan")
    player_actions = relationship("PlayerAction", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")

class GameSession(Base):
    __tablename__ = "game_sessions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    game_id = Column(String(20), unique=True, nullable=False, index=True)
    world = Column(String(50), nullable=False)  # cyberpunk, medieval
    start_time = Column(DateTime(timezone=True), server_default=func.now())
    end_time = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    winner = Column(String(20), nullable=True)  # "mafia" or "civilians"
    total_players = Column(Integer, nullable=False)
    is_completed = Column(Boolean, default=False)
    
    # Relationships
    game_stats = relationship("GameStats", back_populates="game_session", cascade="all, delete-orphan")
    player_actions = relationship("PlayerAction", back_populates="game_session", cascade="all, delete-orphan")
    game_events = relationship("GameEvent", back_populates="game_session", cascade="all, delete-orphan")

class GameStats(Base):
    __tablename__ = "game_stats"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    game_session_id = Column(Integer, ForeignKey("game_sessions.id", ondelete="CASCADE"), nullable=False)
    game_role = Column(SQLEnum(GameRole), nullable=False)
    is_winner = Column(Boolean, default=False)
    survived = Column(Boolean, default=False)
    
    # Role-specific stats
    killed_by_mafia = Column(Boolean, default=False)
    killed_by_lynching = Column(Boolean, default=False)
    sheriff_checks_count = Column(Integer, default=0)
    doctor_heals_count = Column(Integer, default=0)
    mafia_kills_count = Column(Integer, default=0)
    don_checks_count = Column(Integer, default=0)
    votes_cast = Column(Integer, default=0)
    correct_votes = Column(Integer, default=0)
    
    # Relationships
    user = relationship("User", back_populates="game_stats")
    game_session = relationship("GameSession", back_populates="game_stats")

class PlayerAction(Base):
    __tablename__ = "player_actions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    game_session_id = Column(Integer, ForeignKey("game_sessions.id", ondelete="CASCADE"), nullable=False)
    action_type = Column(String(50), nullable=False)  # vote, nominate, kill, check, heal
    target_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    day_number = Column(Integer, nullable=False)
    phase = Column(String(50), nullable=False)  # day, night, voting
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    was_successful = Column(Boolean, default=True)
    
    # Relationships
    user = relationship("User", back_populates="player_actions")
    game_session = relationship("GameSession", back_populates="player_actions")

class GameEvent(Base):
    __tablename__ = "game_events"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    game_session_id = Column(Integer, ForeignKey("game_sessions.id", ondelete="CASCADE"), nullable=False)
    event_type = Column(String(50), nullable=False)  # day_start, night_kill, player_lynched, etc.
    event_data = Column(Text, nullable=True)  # JSON string
    day_number = Column(Integer, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    game_session = relationship("GameSession", back_populates="game_events")

class UserSession(Base):
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token = Column(String(255), unique=True, nullable=False)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user = relationship("User", back_populates="sessions")