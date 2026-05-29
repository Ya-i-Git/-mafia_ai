# backend/server/routers/websocket.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from backend.server.services.game_manager import game_manager, audio_recognizers
from backend.server.game.session import GamePhase
from backend.audio.recognizer import AudioRecognizer
from backend.narrator.intent_parser import IntentParser
import base64
import logging
import asyncio

router = APIRouter()
logger = logging.getLogger(__name__)

_intent_parser: IntentParser | None = None

def get_intent_parser() -> IntentParser | None:
    global _intent_parser
    if _intent_parser is None:
        try:
            _intent_parser = IntentParser()
        except ValueError as e:
            logger.warning(f"IntentParser недоступен: {e}")
    return _intent_parser

@router.websocket("/ws/{game_id}")
async def game_websocket(websocket: WebSocket, game_id: str, username: str = Query(...)):
    logger.info(f"🔌 Game WS connection attempt: game={game_id}, user={username}")
    game = game_manager.get_game(game_id)
    if not game:
        logger.warning(f"Game {game_id} not found")
        await websocket.close(code=4004, reason="Game not found")
        return

    player = game._find_player_by_username(username)
    if not player:
        logger.warning(f"Player {username} not in game {game_id}")
        await websocket.close(code=4001, reason="Not in lobby")
        return

    # Закрываем старый сокет, если есть
    if player.websocket and player.websocket != websocket:
        try:
            await player.websocket.close()
        except:
            pass

    await websocket.accept()
    player.websocket = websocket
    logger.info(f"✅ Game WS accepted for {username}")

    # Отправляем приветствие и состояние
    try:
        await game.send_personal({"type": "system", "text": f"Добро пожаловать, {username}."}, player.user_id)
        await game.send_personal({"type": "game_state", "state": game.get_game_state()}, player.user_id)
        await game.broadcast_game_state()
        logger.info(f"Initial data sent to {username}")
    except Exception as e:
        logger.error(f"Failed to send initial data: {e}", exc_info=True)
        await websocket.close(code=1011, reason="Internal server error")
        return

    # Основной цикл обработки сообщений
    try:
        while True:
            data = await websocket.receive_json()
            logger.debug(f"Received from {username}: {data}")
            await game.handle_message(player.user_id, data)
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for {username}")
    except Exception as e:
        logger.error(f"Error in message loop: {e}", exc_info=True)
    finally:
        if player.websocket == websocket:
            player.websocket = None
            logger.info(f"Cleared websocket for {username}")

@router.websocket("/ws/{game_id}/voice")
async def voice_websocket(websocket: WebSocket, game_id: str, username: str = Query(...)):
    logger.info(f"🎙️ Voice WS connection attempt: game={game_id}, user={username}")
    game = game_manager.get_game(game_id)
    if not game:
        await websocket.close(code=4004, reason="Game not found")
        return

    player = game._find_player_by_username(username)
    if not player:
        logger.warning(f"Voice: player {username} not in game {game_id}")
        await websocket.close(code=4001, reason="Not in lobby")
        return

    # Создаём или получаем распознаватель для этой игры
    if game_id not in audio_recognizers:
        logger.info(f"Creating AudioRecognizer for game {game_id}")
        loop = asyncio.get_event_loop()
        audio_recognizers[game_id] = await loop.run_in_executor(
            None,
            lambda: AudioRecognizer(model_size="base", device="cpu")
        )

    recognizer = audio_recognizers[game_id]

    await websocket.accept()
    logger.info(f"✅ Voice WS accepted for {username}")

    try:
        while True:
            data = await websocket.receive_json()
            audio_b64 = data.get("audio")
            if not audio_b64:
                continue

            try:
                audio_bytes = base64.b64decode(audio_b64)
            except Exception:
                await websocket.send_json({"error": "Неверный формат audio"})
                continue

            transcribed_text = await recognizer.transcribe(audio_bytes)
            if transcribed_text:
                parser = get_intent_parser()
                alive_players = [p.username for p in game.players.values() if p.is_alive]
                if parser is None:
                    await game.handle_message(player.user_id, {"type": "chat", "text": transcribed_text})
                    await websocket.send_json({"text": transcribed_text})
                    continue
                intent = await parser.parse(
                    transcribed_text,
                    game.phase.value,
                    player.role.value if player.role else "civilian",
                    alive_players
                )
                action = intent.get("action")
                if action == "nominate" and "target" in intent:
                    await game.handle_message(player.user_id, {"type": "nominate", "target": intent["target"]})
                    await websocket.send_json({"text": transcribed_text, "interpreted_as": "nominate"})
                elif action == "vote" and "target" in intent:
                    await game.handle_message(player.user_id, {"type": "vote", "target": intent["target"]})
                    await websocket.send_json({"text": transcribed_text, "interpreted_as": "vote"})
                elif action == "action" and "target" in intent and "action_type" in intent:
                    await game.handle_message(player.user_id, {"type": "action", "action": intent["action_type"], "target": intent["target"]})
                    await websocket.send_json({"text": transcribed_text, "interpreted_as": "action"})
                else:
                    await game.handle_message(player.user_id, {"type": "chat", "text": transcribed_text})
                    await websocket.send_json({"text": transcribed_text})
            else:
                await websocket.send_json({"error": "Не удалось распознать речь"})
    except WebSocketDisconnect:
        logger.info(f"⚠️ Voice WS disconnected for {username}")
    except Exception as e:
        logger.error(f"🔥 Voice WS error: {e}", exc_info=True)