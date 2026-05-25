import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_websocket_echo(async_client: AsyncClient):
    # Устанавливаем WebSocket-соединение
    ws_url = "ws://test/ws/demo?token=Player1"
    async with async_client.websocket_connect(ws_url) as ws:
        # Читаем приветствие
        msg = await ws.receive_json()
        assert msg["type"] == "system"
        assert "Welcome" in msg["text"]
        
        # Отправляем сообщение и проверяем эхо
        await ws.send_json({"msg": "hello"})
        echo = await ws.receive_json()
        assert echo["type"] == "echo"
        assert echo["data"] == {"msg": "hello"}