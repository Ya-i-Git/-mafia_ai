import os
from pathlib import Path
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from backend.narrator.schemas import NarratorState
import yaml

env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not found")

PROMPTS_DIR = Path(__file__).parent / "prompts"
with open(PROMPTS_DIR / "cyberpunk.yaml", "r", encoding="utf-8") as f:
    PROMPTS_CYBERPUNK = yaml.safe_load(f)
with open(PROMPTS_DIR / "medieval.yaml", "r", encoding="utf-8") as f:
    PROMPTS_MEDIEVAL = yaml.safe_load(f)

def get_system_prompt(world: str) -> str:
    prompts = PROMPTS_CYBERPUNK if world == "cyberpunk" else PROMPTS_MEDIEVAL
    return prompts["system"]

def get_event_prompt_template(event_type: str, world: str) -> str:
    prompts = PROMPTS_CYBERPUNK if world == "cyberpunk" else PROMPTS_MEDIEVAL
    return prompts["events"].get(event_type, "Расскажи о событии: {event_type}.")

def select_prompt(state: NarratorState) -> NarratorState:
    # Инициализируем messages, если его нет
    if "messages" not in state or state["messages"] is None:
        state["messages"] = []

    system_text = get_system_prompt(state["world"])
    event_template = get_event_prompt_template(state["event_type"], state["world"])
    event_message = event_template.format(
        event_type=state["event_type"],
        players_alive=", ".join(state["players_alive"]),
        **state["event_data"],
        history=state["history"],
        daily_fact=state.get("daily_fact", "")
    )
    state["messages"].extend([
        SystemMessage(content=system_text),
        HumanMessage(content=event_message)
    ])
    return state

def call_model(state: NarratorState) -> NarratorState:
    llm = ChatGroq(
        model=os.getenv("LLM_MODEL", "llama-3.1-8b-instant"),
        temperature=0.8,
        max_tokens=300,
        api_key=GROQ_API_KEY
    )
    response = llm.invoke(state["messages"])
    state["response"] = response.content
    return state

FORBIDDEN = ["мафия", "дон", "шериф", "доктор", "роль", "мирные жители", "мирный", "комиссар", "крестный отец"]

def validate(state: NarratorState) -> NarratorState:
    response_lower = state["response"].lower()
    for word in FORBIDDEN:
        if word in response_lower:
            state["response"] = "Ведущий хранит молчание..."
            return state
    return state

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