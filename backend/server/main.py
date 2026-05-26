from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from backend.server.routers import auth, lobby
from backend.server.routers import websocket
from backend.server.services.game_manager import game_manager  # инициализируем синглтон
from fastapi.middleware.cors import CORSMiddleware 

app = FastAPI(title="Mafia Game Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="server/static"), name="static")

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(lobby.router, prefix="/lobby", tags=["lobby"])
app.include_router(websocket.router, tags=["websocket"])
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

class LoginRequest(BaseModel):
    username: str

class RegisterRequest(BaseModel):
    username: str
    password: str  # добавим пароль

class AuthResponse(BaseModel):
    token: str
    # или access_token: str - выберите один вариант

# Временное хранилище пользователей (в реальном проекте используйте БД)
users_db = {}

@router.post("/login", response_model=AuthResponse)
async def login(body: LoginRequest):
    if body.username not in users_db:
        raise HTTPException(status_code=401, detail="User not found")
    return AuthResponse(token=body.username)

@router.post("/register", response_model=AuthResponse)
async def register(body: RegisterRequest):
    if body.username in users_db:
        raise HTTPException(status_code=400, detail="User already exists")
    users_db[body.username] = body.password
    return AuthResponse(token=body.username)