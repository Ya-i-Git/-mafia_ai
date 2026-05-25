import os
from dotenv import load_dotenv
from pathlib import Path
from typing import Literal
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from narrator.schemas import NarratorState
import yaml

env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)
GROQ_API_KEY = os.environ["GROQ_API_KEY"]

# Загружаем промпты из YAML один раз при старте
with open("narrator/prompts/cyberpunk.yaml", "r") as f:
    PROMPTS_CYBERPUNK = yaml.safe_load(f)

with open("narrator/prompts/medieval.yaml", "r") as f:
    PROMPTS_MEDIEVAL = yaml.safe_load(f)

def get_system_prompt(world: str) -> str:
    """Возвращает системный промпт для указанного мира."""
    prompts = PROMPTS_CYBERPUNK if world == "cyberpunk" else PROMPTS_MEDIEVAL
    return prompts["system"]

def get_event_prompt_template(event_type: str, world: str) -> str:
    """Возвращает шаблон пользовательского запроса для конкретного события."""
    prompts = PROMPTS_CYBERPUNK if world == "cyberpunk" else PROMPTS_MEDIEVAL
    return prompts["events"].get(event_type, "Расскажи о событии: {event_type}.")

def select_prompt(state: NarratorState) -> NarratorState:
    """Узел: формирует сообщения для LLM."""
    system_text = get_system_prompt(state["world"])
    event_template = get_event_prompt_template(state["event_type"], state["world"])
    
    # Подставляем данные события в шаблон
    event_message = event_template.format(
        event_type=state["event_type"],
        players_alive=", ".join(state["players_alive"]),
        **state["event_data"],
        history=state["history"],
        daily_fact=state.get("daily_fact", "")
    )
    
    # Сохраняем сообщения в состоянии (как список словарей)
    state["messages"] = [
        SystemMessage(content=system_text),
        HumanMessage(content=event_message)
    ]
    return state

def call_model(state: NarratorState) -> NarratorState:
    """Узел: вызывает LLM и сохраняет ответ."""
    llm = ChatGroq(
        model=os.getenv("LLM_MODEL", "llama-3.1-8b-instant"),
        temperature=0.8,
        max_tokens=300,
        api_key=GROQ_API_KEY
    )
    response = llm.invoke(state["messages"])
    state["response"] = response.content
    return state

def validate(state: NarratorState) -> NarratorState:
    """Узел: проверяет, что ответ не содержит запрещённой информации.
       Если находит нарушение, заменяет ответ на стандартное сообщение.
    """
    forbidden_words = ["мафия — это", "доктор —", "шериф", "роль"]
    for word in forbidden_words:
        if word in state["response"].lower():
            # Запасной текст при нарушении
            state["response"] = "Ведущий загадочно молчит, не выдавая секретов."
            break
    return state

def should_validate(world: str) -> bool:
    # Включаем валидацию для всех миров (можно отключить, если не нужно)
    return True

# Строим граф
def create_narrator_graph(validate_output: bool = True) -> StateGraph:
    builder = StateGraph(NarratorState)
    
    builder.add_node("select_prompt", select_prompt)
    builder.add_node("call_model", call_model)
    if validate_output:
        builder.add_node("validate", validate)
    
    builder.set_entry_point("select_prompt")
    builder.add_edge("select_prompt", "call_model")
    if validate_output:
        builder.add_edge("call_model", "validate")
        builder.add_edge("validate", END)
    else:
        builder.add_edge("call_model", END)
    
    return builder.compile()