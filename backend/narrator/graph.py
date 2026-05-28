import os
import re
from pathlib import Path
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from .schemas import NarratorState
import yaml

env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not found")

# Загружаем промпты один раз (кеш)
PROMPTS_CACHE = {}

def load_prompts(world: str) -> dict:
    """Загружает YAML-файл с промптами для указанного мира."""
    if world not in PROMPTS_CACHE:
        base = Path(__file__).parent / "prompts"
        path = base / f"{world}.yaml"
        if not path.exists():
            raise ValueError(f"Файл промптов не найден: {path}")
        with open(path, "r", encoding="utf-8") as f:
            PROMPTS_CACHE[world] = yaml.safe_load(f)
    return PROMPTS_CACHE[world]

def select_prompt(state: NarratorState) -> NarratorState:
    prompts = load_prompts(state["world"])
    system_text = prompts["system"]
    
    # Получаем шаблон для конкретного события
    event_template = prompts["events"].get(
        state["event_type"],
        "Расскажи о событии: {event_type}."
    )
    
    # Подставляем переменные
    user_text = event_template.format(
        event_type=state["event_type"],
        players_alive=", ".join(state["players_alive"]),
        **state["event_data"],
        history=state["history"],
        daily_fact=state.get("daily_fact", "")
    )
    
    state["messages"] = [
        SystemMessage(content=system_text),
        HumanMessage(content=user_text)
    ]
    return state

def call_model(state: NarratorState) -> NarratorState:
    llm = ChatGroq(
        model=os.getenv("LLM_MODEL", "llama-3.1-8b-instant"),
        temperature=0.8,
        max_tokens=700,
        api_key=GROQ_API_KEY
    )
    response = llm.invoke(state["messages"])
    state["response"] = response.content
    return state

FORBIDDEN_PATTERNS = [
    r"\b\w+\s*[-—]\s*мафия\b",      # "Алиса — мафия"
    r"\b\w+\s*[-—]\s*дон\b",
    r"\b\w+\s*[-—]\s*шериф\b",
    r"\b\w+\s*[-—]\s*доктор\b",
    r"\b\w+\s*[-—]\s*мирный\b",
    r"\b\w+\s*является\s+(мафией|доном|шерифом|доктором|мирным)\b",
    r"\b(мафия|дон|шериф|доктор)\s+[-—]\s*\w+\b",  # "мафия — Алиса"
]

def validate(state: NarratorState) -> NarratorState:
    if state["response"] is None:
        return state
    response = state["response"]
    for pattern in FORBIDDEN_PATTERNS:
        if re.search(pattern, response, re.IGNORECASE):
            print(f"[WARNING] Найдено раскрытие роли: {pattern}")
            state["response"] = "Ведущий хранит молчание..."
            return state
    return state

def create_narrator_graph(validate_output: bool = True) -> StateGraph:
    builder = StateGraph(NarratorState)
    builder.add_node("select_prompt", select_prompt)
    builder.add_node("call_model", call_model)
    builder.add_node("validate", validate)
    
    builder.set_entry_point("select_prompt")
    builder.add_edge("select_prompt", "call_model")
    builder.add_edge("call_model", "validate")
    builder.add_edge("validate", END)
    
    return builder.compile()