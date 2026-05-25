# server/services/game_manager.py
import uuid
from typing import Optional

from server.game.session import GameSession

class GameManager:
    """Простой контейнер для активных игровых сессий."""
    def __init__(self):
        self._games: dict[str, GameSession] = {}

    def create_game(self) -> str:
        game_id = str(uuid.uuid4())[:8]  # короткий ID для удобства
        self._games[game_id] = GameSession(game_id)
        return game_id

    def get_game(self, game_id: str) -> Optional[GameSession]:
        return self._games.get(game_id)

    def remove_game(self, game_id: str):
        self._games.pop(game_id, None)

# Синглтон, доступный для импорта
game_manager = GameManager()