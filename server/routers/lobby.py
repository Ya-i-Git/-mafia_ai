import uuid
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from server.services.game_manager import game_manager

router = APIRouter()

class CreateGameResponse(BaseModel):
    game_id: str

class JoinGameRequest(BaseModel):
    game_id: str
    username: str

class JoinGameResponse(BaseModel):
    status: str
    role: str | None = None

class StartGameResponse(BaseModel):
    status: str

@router.post("/create_game", response_model=CreateGameResponse)
async def create_game():
    game_id = game_manager.create_game()
    return CreateGameResponse(game_id=game_id)

@router.post("/join_game", response_model=JoinGameResponse)
async def join_game(body: JoinGameRequest):
    game = game_manager.get_game(body.game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Игра не найдена")
    try:
        game.add_player(body.username, body.username)  # временно user_id == username
        return JoinGameResponse(status="joined")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/start_game", response_model=StartGameResponse)
async def start_game(body: JoinGameRequest):  # повторно используем JoinGameRequest
    game = game_manager.get_game(body.game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Игра не найдена")
    try:
        await game.start_game()  # start_game теперь async (см. правки ниже)
        return StartGameResponse(status="started")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))