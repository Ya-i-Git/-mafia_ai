import asyncio
import websockets
import json
import requests
import time
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def create_and_start_game():
    log("Creating game...")
    r = requests.post(f"{BASE_URL}/lobby/create_game")
    game_id = r.json()["game_id"]
    log(f"Game created: {game_id}")
    for name in ["Alice", "Bob", "Charlie", "Dave", "Eve", "Frank"]:
        resp = requests.post(f"{BASE_URL}/lobby/join_game", json={"game_id": game_id, "username": name})
        log(f"Join {name}: {resp.status_code}")
    log("Starting game...")
    requests.post(f"{BASE_URL}/lobby/start_game", json={"game_id": game_id, "username": "admin"})
    return game_id

async def player(username, game_id, actions_queue):
    uri = f"ws://127.0.0.1:8000/ws/{game_id}?username={username}"
    async with websockets.connect(uri) as ws:
        log(f"{username} connected")
        async def listener():
            async for msg in ws:
                data = json.loads(msg)
                if data["type"] == "system":
                    text = data["text"]
                    # Фильтруем интересные сообщения
                    if any(key in text for key in ["проверку", "лечит", "выбор цели", "Цель убийства", "Проверка", "убит", "победа", "Слово предоставляется", "голос", "первый день", "выставлять"]):
                        log(f"[{username}] {text[:80]}")
                elif data["type"] == "chat" and data.get("from") == username:
                    log(f"[{username}] отправил чат: {data['text']}")
        asyncio.create_task(listener())
        while True:
            action = await actions_queue.get()
            if action is None:
                break
            await ws.send(json.dumps(action))
            log(f"{username} -> {action}")

async def main():
    game_id = create_and_start_game()
    await asyncio.sleep(2)

    queues = {name: asyncio.Queue() for name in ["Alice", "Bob", "Charlie", "Dave", "Eve", "Frank"]}
    tasks = [asyncio.create_task(player(name, game_id, queues[name])) for name in queues]

    log("=== ДЕНЬ 1 (знакомство) ===")
    # Все игроки могут говорить, но не выставлять. Завершаем их ходы досрочно, чтобы ускорить.
    for name in ["Alice", "Bob", "Charlie", "Dave", "Eve", "Frank"]:
        await asyncio.sleep(2)  # небольшая пауза, чтобы увидеть начало речи
        await queues[name].put({"type": "end_turn"})
        log(f"{name} завершил ход досрочно")

    log("Ожидаем окончания дня 1 и начала ночи...")
    await asyncio.sleep(8)  # время на переход к ночи (с учётом таймеров)

    log("=== НОЧЬ 1 ===")
    # Предполагаемые роли (подставьте фактические из первых сообщений)
    # Alice - мафия, Bob - доктор, Charlie - шериф, Dave - дон, Eve и Frank - мирные
    await queues["Alice"].put({"type": "action", "action": "kill", "target": "Charlie"})
    await asyncio.sleep(8)  # мафия выбирает цель
    await queues["Dave"].put({"type": "action", "action": "check", "target": "Eve"})
    await asyncio.sleep(6)
    await queues["Charlie"].put({"type": "action", "action": "check", "target": "Dave"})
    await asyncio.sleep(6)
    await queues["Bob"].put({"type": "action", "action": "heal", "target": "Alice"})
    await asyncio.sleep(8)

    log("Ожидаем начала дня 2...")
    await asyncio.sleep(8)

    log("=== ДЕНЬ 2 ===")
    await asyncio.sleep(2)
    # Теперь можно выставлять
    await queues["Alice"].put({"type": "nominate", "target": "Bob"})
    await asyncio.sleep(8)
    await queues["Alice"].put({"type": "end_turn"})
    for name in ["Bob", "Charlie", "Dave", "Eve", "Frank"]:
        await asyncio.sleep(2)
        await queues[name].put({"type": "end_turn"})
    log("Ожидаем защиту, голосование...")
    await asyncio.sleep(12)
    # Голосование за Bob
    for name in queues:
        await queues[name].put({"type": "vote", "target": "Bob"})
    await asyncio.sleep(12)

    log("=== НОЧЬ 2 ===")
    await asyncio.sleep(2)
    await queues["Alice"].put({"type": "action", "action": "kill", "target": "Frank"})
    await asyncio.sleep(8)
    await queues["Dave"].put({"type": "action", "action": "check", "target": "Charlie"})
    await asyncio.sleep(6)
    # Шериф Charlie мог быть убит в первую ночь – если мёртв, его действие проигнорируется
    await queues["Charlie"].put({"type": "action", "action": "check", "target": "Alice"})
    await asyncio.sleep(6)
    await queues["Bob"].put({"type": "action", "action": "heal", "target": "Dave"})  # Bob мёртв? (убит днём) - игнор
    await asyncio.sleep(10)

    # Дадим игре завершиться (победа мафии или продолжение)
    await asyncio.sleep(30)

    for q in queues.values():
        await q.put(None)
    await asyncio.gather(*tasks)
    log("Тест завершён")

if __name__ == "__main__":
    asyncio.run(main())