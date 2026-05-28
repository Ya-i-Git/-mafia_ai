# backend/server/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.server.routers import auth, lobby, websocket, stats
from backend.server.services.game_manager import game_manager

app = FastAPI(title="Mafia Game Server")

# CORS для фронтенда (Vite на 3000, React на 5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(lobby.router, prefix="/lobby", tags=["lobby"])
app.include_router(websocket.router, tags=["websocket"])
app.include_router(stats.router, prefix="/stats", tags=["stats"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)