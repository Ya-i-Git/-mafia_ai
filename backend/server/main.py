# backend/server/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .routers import auth, lobby, websocket, stats   # stats тоже есть?
from ..db import engine, Base

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    print("Database tables created/verified")
    yield
    print("Shutting down...")

app = FastAPI(
    title="Mafia Game API",
    description="Multiplayer Mafia game with AI narrator",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # для разработки, позже ограничить
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔧 Добавляем prefix="/auth" для роутера auth
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(lobby.router, prefix="/lobby", tags=["lobby"])
app.include_router(websocket.router, tags=["websocket"])
app.include_router(stats.router, prefix="/stats", tags=["stats"])

@app.get("/")
async def root():
    return {"message": "Mafia Game API", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}