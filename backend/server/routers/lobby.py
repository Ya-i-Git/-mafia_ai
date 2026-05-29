import uuid
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.server.services.game_manager import game_manager
from backend.audio.synthesizer import TextToSpeech
from fastapi.responses import Response
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

class CreateGameRequest(BaseModel):
    username: str
    world: str = "cyberpunk"

class CreateGameResponse(BaseModel):
    game_id: str

class JoinGameRequest(BaseModel):
    game_id: str
    username: str

class JoinGameResponse(BaseModel):
    status: str
    game_id: str
    players: list = []

class StartGameRequest(BaseModel):
    game_id: str
    username: str

class StartGameResponse(BaseModel):
    status: str

tts_engine = TextToSpeech()

@router.post("/create_game", response_model=CreateGameResponse)
async def create_game(body: CreateGameRequest):
    logger.info(f"Creating game for {body.username}, world={body.world}")
    from backend.server.routers.auth import users_db
    user_entry = users_db.get(body.username)
    user_id = user_entry["user_id"] if user_entry else body.username
    game_id = game_manager.create_game(user_id, world=body.world)
    game = game_manager.get_game(game_id)
    game.add_player(user_id, body.username)
    logger.info(f"Game created: {game_id}, players: {[p.username for p in game.players.values()]}")
    return CreateGameResponse(game_id=game_id)

@router.post("/join_game", response_model=JoinGameResponse)
async def join_game(body: JoinGameRequest):
    logger.info(f"Join request: game={body.game_id}, username={body.username}")
    game = game_manager.get_game(body.game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    from backend.server.routers.auth import users_db
    user_entry = users_db.get(body.username)
    user_id = user_entry["user_id"] if user_entry else body.username
    try:
        game.add_player(user_id, body.username)
        players_list = [p.username for p in game.players.values()]
        logger.info(f"Player {body.username} joined. Current players: {players_list}")
        # Оповещаем всех игроков об изменении состава
        await game.broadcast_game_state()
        return JoinGameResponse(status="joined", game_id=body.game_id, players=players_list)
    except ValueError as e:
        logger.error(f"Join error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/start_game", response_model=StartGameResponse)
async def start_game(body: StartGameRequest):
    game = game_manager.get_game(body.game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    if game.owner_id != body.username:
        raise HTTPException(status_code=403, detail="Only owner can start")
    try:
        await game.start_game()
        return StartGameResponse(status="started")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/tts")
async def text_to_speech(request: dict):
    text = request.get("text")
    if not text:
        return {"error": "No text"}
    audio_data = await tts_engine.synthesize(text)
    if audio_data:
        return Response(content=audio_data, media_type="audio/mpeg")
    else:
        return {"error": "TTS failed"}