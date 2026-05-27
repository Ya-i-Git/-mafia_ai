from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from backend.server.services.game_manager import game_manager
from backend.server.game.session import GamePhase

router = APIRouter()

@router.websocket("/ws/{game_id}")
async def game_websocket(websocket: WebSocket, game_id: str, username: str = Query(...)):
    game = game_manager.get_game(game_id)
    if not game:
        await websocket.close(code=4004, reason="Game not found")
        return
    
    # Ищем игрока по username (не user_id, т.к. у нас в сессии user_id = username)
    player = None
    for p in game.players.values():
        if p.username == username:
            player = p
            break
    if not player:
        await websocket.close(code=4001, reason="Not in lobby")
        return

    # Если у игрока уже есть открытый сокет, закрываем старый
    if player.websocket is not None:
        try:
            await player.websocket.close(code=4003, reason="Duplicate connection")
        except:
            pass

    await websocket.accept()
    player.websocket = websocket

    # Отправляем приветствие и роль
    role_text = player.role.value if game.phase != GamePhase.WAITING else "не назначена"
    await game.send_personal({"type": "system", "text": f"Добро пожаловать, {username}. Игра {game_id}. Ваша роль: {role_text}."}, player.user_id)
    await game.send_personal({"type": "game_state", "state": game.get_game_state()}, player.user_id)

    try:
        while True:
            data = await websocket.receive_json()
            await game.handle_message(player.user_id, data)
    except WebSocketDisconnect:
        game.handle_disconnect(player.user_id)
    finally:
        if game.phase == GamePhase.WAITING:
            game.players.pop(player.user_id, None)
        else:
            if player.is_alive:
                player.is_alive = False
                await game.broadcast({"type": "system", "text": f"{player.username} покинул игру (дисконнект)."})