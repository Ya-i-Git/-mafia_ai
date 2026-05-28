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
    player.websocket = websocket

    await game.send_personal({"type": "system", "text": f"Добро пожаловать, {username}."}, player.user_id)

    if game.phase != GamePhase.WAITING:
        await game.send_personal({"type": "role_assigned", "role": player.role.value}, player.user_id)
        if not player.is_alive:
            await game._send_dead_history(player.user_id)
        await game.broadcast_game_state()   # Убрали for_user_id
    else:
        await game.broadcast_game_state()   # Убрали for_user_id

    try:
        while True:
            data = await websocket.receive_json()
            await game.handle_message(player.user_id, data)
    except WebSocketDisconnect:
        game.handle_disconnect(player.user_id)
    finally:
        if player.websocket == websocket:
            player.websocket = None