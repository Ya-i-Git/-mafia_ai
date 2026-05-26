import uuid
from typing import Dict

users_db: Dict[str, str] = {}  # username -> token

def register_or_login(username: str) -> str:
    if username not in users_db:
        users_db[username] = str(uuid.uuid4())
    return users_db[username]