from typing import TypedDict, List, Optional
from langchain_core.messages import BaseMessage

class NarratorState(TypedDict):
    event_type: str          # "day_start", "night_kill", "player_lynched", ...
    world: str               # "cyberpunk" или "medieval"
    players_alive: List[str]
    event_data: dict         # детали события (например, {"victim": "Alice", "killer": "Mafia"})
    history: str             # краткая история последних действий
    daily_fact: Optional[str] # факт дня (если есть)
    response: Optional[str]  # сгенерированная реплика ведущего
    messages: list[BaseMessage]