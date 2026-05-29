<<<<<<< Updated upstream
from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
=======
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from jose import JWTError, jwt
from pydantic import BaseModel, Field, validator
from typing import Optional
import os
>>>>>>> Stashed changes

from ...db import get_db
from ...db.models import User, UserRole

router = APIRouter(prefix="/auth", tags=["authentication"])

# JWT настройки
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production-min-32-chars")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False)

# Pydantic модели
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: Optional[str] = None
    password: str = Field(..., min_length=6)
    password_confirm: str
    
    @validator('password_confirm')
    def passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v

class UserResponse(BaseModel):
    id: int
    username: str
    email: Optional[str]
    role: str
    total_games: int
    total_wins: int
    win_rate: float
    rating: float
    rank: str
    created_at: Optional[str]
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class LoginRequest(BaseModel):
    username: str
    password: str

# Вспомогательные функции
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Эндпоинты
@router.post("/register", response_model=Token)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    try:
        # Проверка существующего пользователя
        existing_user = db.query(User).filter(User.username == user_data.username).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        
        # Создание пользователя
        new_user = User(
            username=user_data.username,
            email=user_data.email,
            role=UserRole.PLAYER
        )
        new_user.set_password(user_data.password)
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # Создание токена
        access_token = create_access_token(data={"sub": new_user.id})
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": UserResponse(
                id=new_user.id,
                username=new_user.username,
                email=new_user.email,
                role=new_user.role.value,
                total_games=new_user.total_games,
                total_wins=new_user.total_wins,
                win_rate=round(new_user.total_wins / max(1, new_user.total_games) * 100, 2),
                rating=round(new_user.rating, 0),
                rank=new_user.rank or "Bronze",
                created_at=new_user.created_at.isoformat() if new_user.created_at else None
            )
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

<<<<<<< Updated upstream
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
=======
@router.post("/login", response_model=Token)
async def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    try:
        # Поиск пользователя
        user = db.query(User).filter(
            (User.username == login_data.username) | (User.email == login_data.username)
        ).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password"
            )
        
        if not user.verify_password(login_data.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is disabled"
            )
        
        # Обновление времени последнего входа
        user.last_login = datetime.utcnow()
        db.commit()
        
        # Создание токена
        access_token = create_access_token(data={"sub": user.id})
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": UserResponse(
                id=user.id,
                username=user.username,
                email=user.email,
                role=user.role.value,
                total_games=user.total_games,
                total_wins=user.total_wins,
                win_rate=round(user.total_wins / max(1, user.total_games) * 100, 2),
                rating=round(user.rating, 0),
                rank=user.rank or "Bronze",
                created_at=user.created_at.isoformat() if user.created_at else None
            )
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )

@router.get("/me", response_model=UserResponse)
async def get_me(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        
        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            role=user.role.value,
            total_games=user.total_games,
            total_wins=user.total_wins,
            win_rate=round(user.total_wins / max(1, user.total_games) * 100, 2),
            rating=round(user.rating, 0),
            rank=user.rank or "Bronze",
            created_at=user.created_at.isoformat() if user.created_at else None
        )
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
>>>>>>> Stashed changes
