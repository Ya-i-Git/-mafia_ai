# backend/server/routers/lobby.py
import uuid
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.server.services.game_manager import game_manager

router = APIRouter()

class CreateGameRequest(BaseModel):
    username: str

class CreateGameResponse(BaseModel):
    game_id: str

class JoinGameRequest(BaseModel):
    game_id: str
    username: str

class JoinGameResponse(BaseModel):
    status: str
    game_id: str   # возвращаем game_id для удобства

class StartGameRequest(BaseModel):
    game_id: str
    username: str

class StartGameResponse(BaseModel):
    status: str

@router.post("/create_game", response_model=CreateGameResponse)
async def create_game(body: CreateGameRequest):
    game_id = game_manager.create_game(body.username)   # owner_id = username
    game = game_manager.get_game(game_id)
    game.add_player(body.username, body.username)      # добавляем создателя
    return CreateGameResponse(game_id=game_id)

@router.post("/join_game", response_model=JoinGameResponse)
async def join_game(body: JoinGameRequest):
    game = game_manager.get_game(body.game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Игра не найдена")
    try:
        game.add_player(body.username, body.username)
        return JoinGameResponse(status="joined", game_id=body.game_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/start_game", response_model=StartGameResponse)
async def start_game(body: StartGameRequest):
    game = game_manager.get_game(body.game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Игра не найдена")
    # Проверяем, что запрос от владельца
    if game.owner_id != body.username:
        raise HTTPException(status_code=403, detail="Только создатель игры может начать")
    try:
        await game.start_game()
        return StartGameResponse(status="started")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))