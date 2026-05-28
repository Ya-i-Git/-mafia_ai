from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel

router = APIRouter()

class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    password: str

class AuthResponse(BaseModel):
    token: str

# Временное хранилище пользователей (в реальном проекте – БД)
users_db = {}

@router.post("/login", response_model=AuthResponse)
async def login(body: LoginRequest):
    if body.username not in users_db or users_db[body.username] != body.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return AuthResponse(token=body.username)  # token = username (упрощённо)

@router.post("/register", response_model=AuthResponse)
async def register(body: RegisterRequest):
    if body.username in users_db:
        raise HTTPException(status_code=400, detail="User already exists")
    users_db[body.username] = body.password
    return AuthResponse(token=body.username)

@router.get("/me")
async def me(authorization: str = Header(...)):
    """
    Возвращает информацию о текущем пользователе по Bearer token.
    Токен – это просто username (упрощённо).
    """
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid token format")
    username = parts[1]
    if username not in users_db:
        raise HTTPException(status_code=401, detail="User not found")
    return {"username": username}