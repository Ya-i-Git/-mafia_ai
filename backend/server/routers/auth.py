# backend/server/routers/auth.py
from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from typing import Optional

from backend.db.config_sync import get_db
from backend.db.repositories.user_repository_sync import UserRepository

router = APIRouter()

class RegisterRequest(BaseModel):
    username: str
    password: str
    email: Optional[str] = None

class LoginRequest(BaseModel):
    username: str
    password: str

class AuthResponse(BaseModel):
    token: str
    username: str

# Используем Depends с правильной аннотацией
def get_user_repository(db=Depends(get_db)):
    return UserRepository(db)

@router.post("/register", response_model=AuthResponse)
async def register(body: RegisterRequest, request: Request, repo: UserRepository = Depends(get_user_repository)):
    # Проверка существования пользователя
    existing_user = repo.get_user_by_username(body.username)
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")
    
    # Создание пользователя
    user = repo.create_user(body.username, body.password, body.email)
    
    # Создание сессии
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    token = repo.create_session(user.id, client_ip, user_agent)
    
    return AuthResponse(token=token, username=user.username)

@router.post("/login", response_model=AuthResponse)
async def login(body: LoginRequest, request: Request, repo: UserRepository = Depends(get_user_repository)):
    user = repo.authenticate_user(body.username, body.password)
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Создание новой сессии
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    token = repo.create_session(user.id, client_ip, user_agent)
    
    return AuthResponse(token=token, username=user.username)

@router.post("/logout")
async def logout(token: str, repo: UserRepository = Depends(get_user_repository)):
    repo.logout(token)
    return {"status": "logged out"}

@router.get("/me")
async def get_current_user(token: str, repo: UserRepository = Depends(get_user_repository)):
    user = repo.validate_session(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid session")
    return {"id": user.id, "username": user.username, "email": user.email}
