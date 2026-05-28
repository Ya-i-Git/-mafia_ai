import asyncio
from backend.narrator.graph import create_narrator_graph
from backend.narrator.schemas import NarratorState
from backend.narrator.tracing import setup_tracing, traced_generate

setup_tracing()

async def generate(event: dict, world: str, context: dict) -> str:
    """
    Основная точка входа для игрового сервера.
    :param event: словарь с ключами 'type' (str) и 'data' (dict)
    :param world: название мира ('cyberpunk' или 'medieval')
    :param context: словарь с ключами 'players_alive', 'history', 'daily_fact'
    :return: реплика ведущего
    """
    graph = create_narrator_graph(validate_output=True)

    # Создаём состояние без поля messages (оно будет добавлено в select_prompt)
    initial_state: NarratorState = {
        "event_type": event["type"],
        "world": world,
        "players_alive": context.get("players_alive", []),
        "event_data": event.get("data", {}),
        "history": context.get("history", ""),
        "daily_fact": context.get("daily_fact", ""),
        "response": None,
        # messages отсутствует – select_prompt сам его создаст
    }

    final_state = await graph.ainvoke(initial_state)
    return final_state["response"]

generate = traced_generate(generate)