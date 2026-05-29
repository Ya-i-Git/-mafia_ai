from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from ..base import Base

class ActionType(str, enum.Enum):
    VOTE = "vote"
    KILL = "kill"
    INVESTIGATE = "investigate"
    HEAL = "heal"
    PROTECT = "protect"
    FRAME = "frame"
    CHAT = "chat"

class PlayerAction(Base):
    __tablename__ = "player_actions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    player_id = Column(Integer, ForeignKey("game_players.id"), nullable=False)
    game_session_id = Column(Integer, ForeignKey("game_sessions.id"), nullable=False)
    action_type = Column(SQLEnum(ActionType), nullable=False)
    target_player_id = Column(Integer, ForeignKey("game_players.id"), nullable=True)
    round_number = Column(Integer, nullable=False)
    success = Column(Boolean, default=True)
    result_data = Column(JSON, default=dict)
    performed_at = Column(DateTime(timezone=True), server_default=func.now())

class Round(Base):
    __tablename__ = "rounds"
    
    id = Column(Integer, primary_key=True, index=True)
    game_session_id = Column(Integer, ForeignKey("game_sessions.id"), nullable=False)
    round_number = Column(Integer, nullable=False)
    phase = Column(String(20), nullable=False)
    killed_player_id = Column(Integer, ForeignKey("game_players.id"), nullable=True)
    killed_by = Column(String(20), nullable=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True), nullable=True)

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    game_session_id = Column(Integer, ForeignKey("game_sessions.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message = Column(String(1000), nullable=False)
    is_public = Column(Boolean, default=True)
    recipient_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
