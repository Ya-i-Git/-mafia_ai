import asyncio
from narrator.generator import generate

async def main():
    text = await generate(
        event={"type": "night_kill", "data": {"victim": "Джонни"}},
        world="cyberpunk",
        context={
            "players_alive": ["Алиса", "Боб", "Клара"],
            "history": "Вчера казнили Еву, она была мирной.",
            "daily_fact": "Корпорация «НейроДайн» выпустила новый имплант для чтения мыслей."
        }
    )
    print(text)

asyncio.run(main())