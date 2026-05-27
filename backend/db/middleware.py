# backend/db/middleware.py
from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
from backend.db.config_sync import SessionLocal

class DBSessionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Создаем сессию для запроса
        request.state.db = SessionLocal()
        try:
            response = await call_next(request)
            return response
        finally:
            # Закрываем сессию после запроса
            request.state.db.close()
            request.state.db = None

# В main.py:
# app.add_middleware(DBSessionMiddleware)

# В эндпоинтах:
@router.get("/users") # type: ignore
async def get_users(request: Request):
    db = request.state.db
    # используем db