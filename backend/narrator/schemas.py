from typing import TypedDict, List, Optional
from langchain_core.messages import BaseMessage

class NarratorState(TypedDict, total=False):
    event_type: str
    world: str
    players_alive: List[str]
    event_data: dict
    history: str
    daily_fact: Optional[str]
    response: Optional[str]
    messages: Optional[List[BaseMessage]]   # теперь необязательное