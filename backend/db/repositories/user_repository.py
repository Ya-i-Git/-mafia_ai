# backend/db/repositories/user_repository.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
import hashlib
import secrets
from typing import Optional, Dict, Any

from backend.db.models import User, UserSession, GameStats

class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def hash_password(password: str) -> str:
        salt = secrets.token_hex(16)
        hash_obj = hashlib.sha256(f"{password}{salt}".encode()).hexdigest()
        return f"{salt}:{hash_obj}"

    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        salt, stored_hash = hashed.split(":")
        computed_hash = hashlib.sha256(f"{password}{salt}".encode()).hexdigest()
        return computed_hash == stored_hash

    async def create_user(self, username: str, password: str, email: Optional[str] = None) -> User:
        user = User(
            username=username,
            hashed_password=self.hash_password(password),
            email=email,
            created_at=datetime.now()
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def get_user_by_username(self, username: str) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        user = await self.get_user_by_username(username)
        if user and self.verify_password(password, user.hashed_password):
            user.last_login = datetime.now()
            await self.db.commit()
            return user
        return None

    async def create_session(self, user_id: int, ip_address: Optional[str] = None,
                             user_agent: Optional[str] = None) -> str:
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
        await self.db.commit()
        return token

    async def validate_session(self, token: str) -> Optional[User]:
        result = await self.db.execute(
            select(UserSession).where(
                UserSession.token == token,
                UserSession.expires_at > datetime.now(),
                UserSession.is_active == True
            )
        )
        session = result.scalar_one_or_none()
        if session and session.user.is_active:
            return session.user
        return None

    async def logout(self, token: str):
        await self.db.execute(
            UserSession.__table__.update()
            .where(UserSession.token == token)
            .values(is_active=False)
        )
        await self.db.commit()

    async def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        result = await self.db.execute(select(GameStats).where(GameStats.user_id == user_id))
        stats = result.scalars().all()

        total_games = len(stats)
        wins = sum(1 for s in stats if s.is_winner)

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