from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta
import random

router = APIRouter()

@router.get("/global")
async def global_stats():
    # Заглушка – генерируем случайные данные для демонстрации
    roles = ["mafia", "don", "sheriff", "doctor", "civilian"]
    winrate_by_role = {role: round(random.uniform(30, 70), 1) for role in roles}
    
    # Последние 7 дней
    today = datetime.now().date()
    games_per_day = []
    for i in range(6, -1, -1):
        date = today - timedelta(days=i)
        games_per_day.append({
            "date": date.strftime("%Y-%m-%d"),
            "count": random.randint(1, 20)
        })
    
    top_players = [
        {"username": "Игрок1", "wins": random.randint(5, 30)},
        {"username": "Игрок2", "wins": random.randint(5, 30)},
        {"username": "Игрок3", "wins": random.randint(5, 30)},
    ]
    
    return {
        "winrateByRole": winrate_by_role,
        "gamesPerDay": games_per_day,
        "averageGameDuration": random.randint(15, 45) * 60,  # секунды
        "topPlayers": top_players
    }

@router.get("/user/{username}")
async def user_stats(username: str):
    # Заглушка – если пользователь существует в базе (имитируем)
    # В реальности нужно проверять в БД
    if username == "":
        raise HTTPException(status_code=404, detail="Player not found")
    return {
        "totalGames": random.randint(1, 100),
        "wins": random.randint(0, 50),
        "losses": random.randint(0, 50),
        "firstGuessAccuracy": round(random.uniform(0, 100), 1),
        "favoriteRole": random.choice(["mafia", "sheriff", "doctor", "civilian"])
    }