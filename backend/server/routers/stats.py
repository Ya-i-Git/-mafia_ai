from fastapi import APIRouter

router = APIRouter(prefix="/stats", tags=["stats"])

@router.get("/global")
async def global_stats():
    return {
        "winrateByRole": {
            "mafia": 48.5,
            "don": 52.1,
            "sheriff": 49.3,
            "doctor": 50.2,
            "civilian": 45.8,
        },
        "gamesPerDay": [
            {"date": "2025-01-01", "count": 12},
            {"date": "2025-01-02", "count": 18},
            {"date": "2025-01-03", "count": 14},
        ],
        "averageGameDuration": 1860,  # секунд
        "topPlayers": [
            {"username": "Alice", "wins": 42},
            {"username": "Bob", "wins": 38},
            {"username": "Charlie", "wins": 35},
        ],
    }

@router.get("/user/{username}")
async def user_stats(username: str):
    return {
        "totalGames": 23,
        "wins": 12,
        "losses": 11,
        "firstGuessAccuracy": 67,
        "favoriteRole": "sheriff",
    }