from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class LoginRequest(BaseModel):
    username: str

class LoginResponse(BaseModel):
    token: str

@router.post("/login", response_model=LoginResponse)
async def login(body: LoginRequest):
    # Временная реализация: токен == имя пользователя
    return LoginResponse(token=body.username)