from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
import random
import string

from ..base import Base

class GameStatus(str, enum.Enum):
    WAITING = "waiting"
    STARTING = "starting"
    NIGHT = "night"
    DAY = "day"
    VOTING = "voting"
    FINISHED = "finished"
    CANCELLED = "cancelled"

class TeamType(str, enum.Enum):
    MAFIA = "mafia"
    CIVILIAN = "civilian"
    NEUTRAL = "neutral"

class GameSession(Base):
    __tablename__ = "game_sessions"

    id = Column(Integer, primary_key=True, index=True)
    room_code = Column(String(6), unique=True, nullable=False, index=True)
    world_theme = Column(String(50), nullable=False, default="medieval")
    max_players = Column(Integer, default=10)
    min_players = Column(Integer, default=4)
    current_players = Column(Integer, default=0)
    status = Column(SQLEnum(GameStatus), default=GameStatus.WAITING)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    winner_team = Column(String(20), nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    night_duration = Column(Integer, default=30)
    day_duration = Column(Integer, default=60)
    voting_duration = Column(Integer, default=30)
    
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    @staticmethod
    def generate_room_code():
        chars = string.ascii_uppercase + string.digits
        return ''.join(random.choices(chars, k=6))

class GamePlayer(Base):
    __tablename__ = "game_players"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    game_session_id = Column(Integer, ForeignKey("game_sessions.id"), nullable=False)
    role = Column(String(50), nullable=False)
    team = Column(SQLEnum(TeamType), nullable=False)
    is_alive = Column(Boolean, default=True)
    player_index = Column(Integer, nullable=False)
    kills_count = Column(Integer, default=0)
    votes_received = Column(Integer, default=0)
    votes_given = Column(Integer, default=0)
    was_killed_night = Column(Boolean, default=False)
    was_lynched = Column(Boolean, default=False)
    survived = Column(Boolean, default=False)
    role_data = Column(JSON, default=dict)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    eliminated_at = Column(DateTime(timezone=True), nullable=True)
