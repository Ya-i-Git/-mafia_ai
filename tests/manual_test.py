# tests/manual_test.py
import asyncio
import sys
import json
import httpx
import websockets

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

BASE_URL = "http://127.0.0.1:8000"
WS_URL = "ws://127.0.0.1:8000"
PLAYERS = ["Alice", "Bob", "Charlie", "Dave", "Eve", "Frank"]

async def create_and_start_game():
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Создаём игру
        r = await client.post(f"{BASE_URL}/lobby/create_game")
        r.raise_for_status()
        game_id = r.json()["game_id"]
        print(f"Game created: {game_id}")

        for name in PLAYERS:
            r = await client.post(f"{BASE_URL}/lobby/join_game",
                                  json={"game_id": game_id, "username": name})
            r.raise_for_status()
            print(f"Joined: {name}")

        r = await client.post(f"{BASE_URL}/lobby/start_game",
                              json={"game_id": game_id, "username": "admin"})
        r.raise_for_status()
        print("Game started")
        return game_id

async def player_session(username, game_id):
    """Подключается к игре, узнаёт свою роль и действует по скрипту."""
    uri = f"{WS_URL}/ws/{game_id}?username={username}"
    async with websockets.connect(uri) as ws:
        queue = asyncio.Queue()

        async def listener():
            async for msg in ws:
                data = json.loads(msg)
                await queue.put(data)

        listen_task = asyncio.create_task(listener())
        role = None

        try:
            # 1. Ждём приветственное сообщение с ролью
            while True:
                msg = await asyncio.wait_for(queue.get(), timeout=5)
                print(f"[{username}] <<< {msg}")
                text = msg.get("text", "")
                if msg.get("type") == "system" and "Ваша роль:" in text:
                    role = text.split("Ваша роль:")[1].strip().rstrip(".").lower()
                    print(f"[{username}] My role: {role}")
                    break

            # 2. Основной цикл: реагируем на события игры
            while True:
                msg = await asyncio.wait_for(queue.get(), timeout=10)
                print(f"[{username}] <<< {msg}")
                text = msg.get("text", "")

                # Дневная речь – говорит только тот, кому дали слово
                if "Слово предоставляется" in text and username in text:
                    if username == "Alice":
                        await ws.send(json.dumps({"type": "chat", "text": "Я мирный, подозреваю Bob."}))
                        await asyncio.sleep(1)
                        await ws.send(json.dumps({"type": "nominate", "target": "Bob"}))
                        await asyncio.sleep(1)
                        await ws.send(json.dumps({"type": "end_turn"}))
                    else:
                        await ws.send(json.dumps({"type": "end_turn"}))

                # Фаза голосования – все голосуют за Bob (если он жив)
                elif "Голосование" in text:
                    await ws.send(json.dumps({"type": "vote", "target": "Bob"}))

                # Ночные действия
                elif "засыпает" in text or "Ночь" in text:
                    if role in ("don", "mafia"):
                        await ws.send(json.dumps({"type": "action", "action": "kill", "target": "Alice"}))
                    if role == "sheriff":
                        await ws.send(json.dumps({"type": "action", "action": "check", "target": "Bob"}))
                    if role == "doctor":
                        await ws.send(json.dumps({"type": "action", "action": "heal", "target": "Alice"}))

                # Завершение игры или выход игрока
                if "покидает игру" in text or "Победа" in text or "победили" in text:
                    break

        except asyncio.TimeoutError:
            print(f"[{username}] Timeout waiting for messages")
        finally:
            listen_task.cancel()

async def main():
    game_id = await create_and_start_game()
    tasks = [player_session(name, game_id) for name in PLAYERS]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())