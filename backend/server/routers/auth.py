# backend/server/routers/auth.py
import uuid
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

# Временное хранилище пользователей
users_db: dict[str, dict] = {}

@router.post("/login", response_model=AuthResponse)
async def login(body: LoginRequest):
    entry = users_db.get(body.username)
    if not entry or entry["password"] != body.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return AuthResponse(token=body.username)

@router.post("/register", response_model=AuthResponse)
async def register(body: RegisterRequest):
    if body.username in users_db:
        raise HTTPException(status_code=400, detail="User already exists")
    users_db[body.username] = {
        "password": body.password,
        "user_id": str(uuid.uuid4()),
    }
    return AuthResponse(token=body.username)

@router.get("/me")
async def me(authorization: str = Header(...)):
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid token format")
    username = parts[1]
    if username not in users_db:
        raise HTTPException(status_code=401, detail="User not found")
    return {"username": username, "user_id": users_db[username]["user_id"]}