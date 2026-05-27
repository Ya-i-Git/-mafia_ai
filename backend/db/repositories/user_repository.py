# backend/db/repositories/user_repository_sync.py
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import hashlib
import secrets
from typing import Optional, Dict, Any

from backend.db.models import User, UserSession, GameStats

class UserRepository:
    def __init__(self, db: Session):
        self.db = db
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Хеширование пароля с солью"""
        salt = secrets.token_hex(16)
        hash_obj = hashlib.sha256(f"{password}{salt}".encode()).hexdigest()
        return f"{salt}:{hash_obj}"
    
    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Проверка пароля"""
        salt, stored_hash = hashed.split(":")
        computed_hash = hashlib.sha256(f"{password}{salt}".encode()).hexdigest()
        return computed_hash == stored_hash
    
    def create_user(self, username: str, password: str, email: Optional[str] = None) -> User:
        """Создание нового пользователя"""
        user = User(
            username=username,
            password_hash=self.hash_password(password),
            email=email,
            created_at=datetime.now()
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Получение пользователя по имени"""
        return self.db.query(User).filter(User.username == username).first()
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Получение пользователя по ID"""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Аутентификация пользователя"""
        user = self.get_user_by_username(username)
        if user and self.verify_password(password, user.password_hash):
            user.last_login = datetime.now()
            self.db.commit()
            return user
        return None
    
    def create_session(self, user_id: int, ip_address: Optional[str] = None, 
                      user_agent: Optional[str] = None) -> str:
        """Создание сессии пользователя"""
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(days=7)
        
        session = UserSession(
            user_id=user_id,
            token=token,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=expires_at
        )
        self.db.add(session)
        self.db.commit()
        return token
    
    def validate_session(self, token: str) -> Optional[User]:
        """Проверка валидности сессии"""
        session = self.db.query(UserSession).filter(
            UserSession.token == token,
            UserSession.expires_at > datetime.now(),
            UserSession.is_active == True
        ).first()
        
        if session and session.user.is_active:
            return session.user
        return None
    
    def logout(self, token: str):
        """Завершение сессии"""
        self.db.query(UserSession).filter(
            UserSession.token == token
        ).update({"is_active": False})
        self.db.commit()
    
    def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """Получение полной статистики пользователя"""
        stats = self.db.query(GameStats).filter(GameStats.user_id == user_id).all()
        
        total_games = len(stats)
        wins = sum(1 for s in stats if s.is_winner)
        
        # Статистика по ролям
        role_stats = {}
        from backend.db.models import GameRole
        for role in GameRole:
            role_games = [s for s in stats if s.game_role == role]
            role_wins = sum(1 for s in role_games if s.is_winner)
            role_stats[role.value] = {
                "games": len(role_games),
                "wins": role_wins,
                "winrate": (role_wins / len(role_games) * 100) if role_games else 0
            }
        
        # Самая успешная роль
        favorite_role = max(role_stats.items(), key=lambda x: x[1]["games"])[0] if role_stats else None
        
        return {
            "total_games": total_games,
            "wins": wins,
            "losses": total_games - wins,
            "winrate": (wins / total_games * 100) if total_games else 0,
            "role_stats": role_stats,
            "favorite_role": favorite_role,
            "survival_rate": (sum(1 for s in stats if s.survived) / total_games * 100) if total_games else 0
        }