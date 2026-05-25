from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from server.routers import auth, lobby, websocket
from server.services.game_manager import game_manager  # инициализируем синглтон

app = FastAPI(title="Mafia Game Server")

app.mount("/static", StaticFiles(directory="server/static"), name="static")

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(lobby.router, prefix="/lobby", tags=["lobby"])
app.include_router(websocket.router, tags=["websocket"])