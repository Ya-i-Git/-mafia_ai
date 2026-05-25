from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from server.services.game_manager import game_manager

router = APIRouter()

@router.websocket("/ws/{game_id}")
async def game_websocket(
    websocket: WebSocket,
    game_id: str,
    username: str = Query(...),  # передача имени в query-параметре
):
    game = game_manager.get_game(game_id)
    if not game:
        await websocket.close(code=4004, reason="Game not found")
        return

    # Ищем игрока по имени (временно; потом будет токен)
    player = game._find_player_by_username(username)
    if not player:
        # Если игрок не в лобби, запрещаем подключаться
        await websocket.close(code=4001, reason="Not in lobby")
        return

    await websocket.accept()
    player.websocket = websocket  # связываем сокет с игроком

    # Приветственное системное сообщение
    await game.send_personal({
        "type": "system",
        "text": f"Добро пожаловать, {username}. Игра {game_id}. Ваша роль: {player.role.value if game.phase != 'waiting' else 'не назначена'}."
    }, player.user_id)

    try:
        while True:
            data = await websocket.receive_json()
            await game.handle_message(player.user_id, data)
    except WebSocketDisconnect:
        # Игрок отключился – помечаем как выбывшего (простая реализация)
        game.handle_disconnect(player.user_id)
    finally:
        if game.phase == "waiting":
            # В лобби можно удалить игрока совсем
            game.players.pop(player.user_id, None)
        else:
            # В активной игре – помечаем мёртвым, чтобы не блокировать
            if player.is_alive:
                player.is_alive = False
                await game.broadcast({
                    "type": "system",
                    "text": f"{player.username} покинул игру (дисконнект)."
                })