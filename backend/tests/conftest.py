
import pytest
from backend.server.game.session import GameSession, FallbackNarrator

@pytest.fixture
def narrator():
    """Используем FallbackNarrator для тестов."""
    return FallbackNarrator()

@pytest.fixture
async def game_6_players(narrator):
    """Создаёт игру с 6 игроками и возвращает сессию."""
    session = GameSession("test-game-6", world="cyberpunk", test_mode=True, narrator=narrator)
    # Добавляем 6 игроков (user_id == username для простоты)
    for name in ["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank"]:
        session.add_player(name, name)
    session.assign_roles()
    return session

@pytest.fixture
async def game_6_players_started(game_6_players):
    """Запускает игру (дневной цикл) и дожидается первой фазы."""
    await game_6_players.start_game()
    return game_6_players