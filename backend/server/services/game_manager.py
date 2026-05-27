# backend/server/services/game_manager.py
import uuid
from typing import Optional
from backend.server.game.session import GameSession

class GameManager:
    def __init__(self):
        self._games: dict[str, GameSession] = {}

    def create_game(self, owner_id: str) -> str:
        game_id = str(uuid.uuid4())[:8]
        self._games[game_id] = GameSession(game_id, owner_id)
        return game_id

    def get_game(self, game_id: str) -> Optional[GameSession]:
        return self._games.get(game_id)

    def remove_game(self, game_id: str):
        self._games.pop(game_id, None)

game_manager = GameManager()