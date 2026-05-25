import pytest
from httpx import AsyncClient
from server.main import app

@pytest.fixture
async def async_client():
    # Используем ASGI-транспорт для тестирования без реального сервера
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client