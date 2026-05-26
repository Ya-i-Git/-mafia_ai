import asyncio
import websockets
import json
import requests

BASE_URL = "http://127.0.0.1:8000"

def create_and_start_game():
    r = requests.post(f"{BASE_URL}/lobby/create_game")
    game_id = r.json()["game_id"]
    print(f"Game created: {game_id}")
    for name in ["Alice", "Bob", "Charlie", "Dave", "Eve", "Frank"]:
        requests.post(f"{BASE_URL}/lobby/join_game", json={"game_id": game_id, "username": name})
    requests.post(f"{BASE_URL}/lobby/start_game", json={"game_id": game_id, "username": "admin"})
    return game_id

async def watch(username, game_id):
    uri = f"ws://127.0.0.1:8000/ws/{game_id}?username={username}"
    async with websockets.connect(uri) as ws:
        print(f"{username} connected")
        async for msg in ws:
            data = json.loads(msg)
            if data["type"] == "system":
                print(f"[{username}] {data['text']}")
            elif data["type"] == "chat":
                print(f"[{username}] {data['from']}: {data['text']}")

async def main():
    game_id = create_and_start_game()
    await asyncio.sleep(2)
    tasks = [watch(name, game_id) for name in ["Alice", "Bob", "Charlie", "Dave", "Eve", "Frank"]]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())