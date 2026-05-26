import os
from langsmith import traceable

def setup_tracing():
    """Включает глобальное трейсинг в LangSmith, если задан API-ключ."""
    api_key = os.getenv("LANGSMITH_API_KEY")
    if not api_key:
        print("⚠️ LANGSMITH_API_KEY не найден – трассировка отключена")
        return

    os.environ.setdefault("LANGSMITH_TRACING", "true")
    os.environ.setdefault("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")
    os.environ.setdefault("LANGSMITH_PROJECT", "mafia_ai_py")

def traced_generate(original_func):
    """Декоратор, оборачивающий функцию generate в traceable."""
    return traceable(
        run_type="chain",
        name="Narrator_Generation"
    )(original_func)