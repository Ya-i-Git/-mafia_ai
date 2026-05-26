import asyncio
import websockets
import json
import requests
import sys
import time

BASE_URL = "http://127.0.0.1:8000"

def create_and_start_game():
    for attempt in range(5):
        try:
            r = requests.post(f"{BASE_URL}/lobby/create_game", timeout=5)
            r.raise_for_status()
            game_id = r.json()["game_id"]
            print("Game created:", game_id)
            break
        except Exception as e:
            print(f"Attempt {attempt+1} failed: {e}")
            time.sleep(1)
    else:
        raise RuntimeError("Could not create game after 5 attempts")
    
    for name in ["Alice", "Bob", "Charlie", "Dave", "Eve", "Frank"]:
        resp = requests.post(f"{BASE_URL}/lobby/join_game", json={
            "game_id": game_id,
            "username": name
        }, timeout=5)
        resp.raise_for_status()
        print(f"Join {name}: {resp.status_code}")
    
    resp = requests.post(f"{BASE_URL}/lobby/start_game", json={
        "game_id": game_id,
        "username": "admin"
    }, timeout=5)
    resp.raise_for_status()
    print("Game started")
    return game_id

async def player(username, game_id, actions_queue):
    uri = f"ws://127.0.0.1:8000/ws/{game_id}?username={username}"
    try:
        async with websockets.connect(uri) as ws:
            print(f"{username} connected")
            # Задача для приёма сообщений
            async def listener():
                async for msg in ws:
                    data = json.loads(msg)
                    print(f"[{username}] {data}")
            asyncio.create_task(listener())
            
            # Ждём, пока игра дойдёт до нужной фазы
            while True:
                action = await actions_queue.get()
                if action is None:
                    break
                await ws.send(json.dumps(action))
                print(f"{username} sent: {action}")
                await asyncio.sleep(0.5)
    except Exception as e:
        print(f"{username} WebSocket error: {e}")

async def main():
    game_id = create_and_start_game()
    
    # Очереди действий для каждого игрока
    queues = {name: asyncio.Queue() for name in ["Alice", "Bob", "Charlie", "Dave", "Eve", "Frank"]}
    
    # Запускаем игроков
    tasks = [player(name, game_id, queues[name]) for name in queues]
    
    # Планируем действия по фазам (временные задержки зависят от таймеров в игре)
    # ДЕНЬ 1: слово даётся по очереди: Alice, Bob, Charlie, Dave, Eve, Frank.
    # У каждого 60 сек на речь + 15 сек на номинацию. Мы просимулируем номинацию от Alice.
    await asyncio.sleep(2)  # Дадим игре прогреть фазу DAY
    # Alice выставляет Bob
    await queues["Alice"].put({"type": "nominate", "target": "Bob"})
    # Через 5 секунд Alice завершает свой ход (досрочно)
    await asyncio.sleep(5)
    await queues["Alice"].put({"type": "end_turn"})
    
    # Следующие игроки могут пропустить ход через end_turn, чтобы быстрее дойти до голосования
    for name in ["Bob", "Charlie", "Dave", "Eve", "Frank"]:
        await asyncio.sleep(2)
        await queues[name].put({"type": "end_turn"})
    
    # После того как все высказались, начинается защита выставленных (Bob). У него 60 сек.
    # Мы не будем отправлять сообщения из защиты, просто ждём.
    await asyncio.sleep(65)  # 60 сек защита + 5 сек запас
    
    # Начинается голосование (30 сек). Все голосуют за Bob (убить).
    for name in ["Alice", "Bob", "Charlie", "Dave", "Eve", "Frank"]:
        await queues[name].put({"type": "vote", "target": "Bob"})
    
    # Ждём окончания голосования (30 сек)
    await asyncio.sleep(35)
    
    # После казни Bob (мирный) – ночь. Ночные фазы:
    # - Мафия (60 сек чат + 15 сек выбор). Убить Charlie.
    await asyncio.sleep(2)
    await queues["Dave"].put({"type": "action", "action": "kill", "target": "Charlie"})  # Dave - mafia
    # - Дон (30 сек) проверяет Eve
    await asyncio.sleep(65)  # ждём, пока мафия закончит
    await queues["Bob"].put({"type": "action", "action": "check", "target": "Eve"})    # Bob - don (уже мёртв? но дон мёртв – привилегия передаётся мафии)
    # - Шериф (30 сек) проверяет Dave
    await asyncio.sleep(35)
    await queues["Frank"].put({"type": "action", "action": "check", "target": "Dave"}) # Frank - sheriff
    # - Доктор (30 сек) лечит Alice
    await asyncio.sleep(35)
    await queues["Charlie"].put({"type": "action", "action": "heal", "target": "Alice"}) # Charlie - doctor
    
    # Ждём окончания ночи и начала второго дня
    await asyncio.sleep(40)
    
    # ДЕНЬ 2: будет объявлено убийство Charlie (или нет, если доктор вылечил? по условию doctor лечит Alice, Charlie не спасён – Charlie умрёт)
    # Даём игре ещё 2 минуты для наблюдения
    await asyncio.sleep(120)
    
    # Останавливаем всех игроков
    for q in queues.values():
        await q.put(None)
    
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())