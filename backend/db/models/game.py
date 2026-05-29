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
    
    # Связи
    creator = relationship("User", back_populates="created_games", foreign_keys=[created_by_id])
    players = relationship("GamePlayer", back_populates="game_session", cascade="all, delete-orphan")
    chat_messages = relationship("ChatMessage", back_populates="game_session", cascade="all, delete-orphan")
    rounds = relationship("Round", back_populates="game_session", cascade="all, delete-orphan")
    
    @staticmethod
    def generate_room_code():
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    
    def to_dict(self):
        return {
            "id": self.id,
            "room_code": self.room_code,
            "world_theme": self.world_theme,
            "max_players": self.max_players,
            "min_players": self.min_players,
            "current_players": self.current_players,
            "status": self.status.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "winner_team": self.winner_team,
            "duration_seconds": self.duration_seconds
        }

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
    
    # Связи
    user = relationship("User", back_populates="games_played", foreign_keys=[user_id])
    game_session = relationship("GameSession", back_populates="players", foreign_keys=[game_session_id])
    actions_as_player = relationship("PlayerAction", back_populates="player", foreign_keys="PlayerAction.player_id")
    actions_as_target = relationship("PlayerAction", back_populates="target_player", foreign_keys="PlayerAction.target_player_id")
    
    def eliminate(self, reason: str = "unknown"):
        self.is_alive = False
        self.eliminated_at = func.now()
        if reason == "night":
            self.was_killed_night = True
        elif reason == "voting":
            self.was_lynched = True
    
    def to_dict(self, reveal_role=False):
        data = {
            "id": self.id,
            "user_id": self.user_id,
            "username": self.user.username if self.user else None,
            "is_alive": self.is_alive,
            "player_index": self.player_index,
            "kills_count": self.kills_count,
            "votes_received": self.votes_received
        }
        if reveal_role or not self.is_alive:
            data["role"] = self.role
            data["team"] = self.team.value
        return data