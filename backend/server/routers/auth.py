from fastapi import APIRouter, HTTPException, Depends, Header
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

class UserResponse(BaseModel):
    username: str
    id: str

users_db = {}

# Вспомогательная функция для получения текущего пользователя по токену
def get_current_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing token")
    token = authorization.split(" ")[1]
    # У нас токен = username
    if token not in users_db:
        raise HTTPException(status_code=401, detail="Invalid token")
    return token

@router.post("/login", response_model=AuthResponse)
async def login(body: LoginRequest):
    if body.username not in users_db or users_db[body.username] != body.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return AuthResponse(token=body.username)

@router.post("/register", response_model=AuthResponse)
async def register(body: RegisterRequest):
    if body.username in users_db:
        raise HTTPException(status_code=400, detail="User already exists")
    users_db[body.username] = body.password
    return AuthResponse(token=body.username)

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: str = Depends(get_current_user)):
    return UserResponse(username=current_user, id=current_user)