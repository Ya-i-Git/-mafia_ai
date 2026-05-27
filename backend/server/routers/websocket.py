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
    player = game._find_player_by_username(username)
    if not player:
        await websocket.close(code=4001, reason="Not in lobby")
        return
    await websocket.accept()
    # Обновляем websocket при переподключении
    player.websocket = websocket
    # Если игрок мёртв, отправляем ему историю чата мёртвых
    if not player.is_alive and game.phase != GamePhase.WAITING:
        await game._send_dead_history(player.user_id)
    role_text = player.role.value if game.phase != GamePhase.WAITING else "не назначена"
    await game.send_personal({"type": "system", "text": f"Добро пожаловать, {username}. Игра {game_id}. Ваша роль: {role_text}."}, player.user_id)
    if game.phase != GamePhase.WAITING:
        await game.send_personal({"type": "role_assigned", "role": player.role.value}, player.user_id)
    await game.send_personal({"type": "game_state", "state": game.get_game_state()}, player.user_id)
    try:
        while True:
            data = await websocket.receive_json()
            await game.handle_message(player.user_id, data)
    except WebSocketDisconnect:
        game.handle_disconnect(player.user_id)
    finally:
        if player.websocket == websocket:
            player.websocket = None