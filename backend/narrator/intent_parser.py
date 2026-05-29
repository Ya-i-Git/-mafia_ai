import re
import json
from typing import Optional, List, Dict, Any
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
import os

class IntentParser:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not found for IntentParser")
        self.llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0.2, api_key=self.api_key)
        self.system_prompt_template = """
Ты помощник в игре «Мафия». Из текста игрока нужно определить намерение и цель.
Возможные действия: "nominate" (выдвинуть игрока на голосование), "vote" (голосовать за игрока), 
"action" (ночное действие: убить, проверить, вылечить). 
Также может быть просто "chat" – обычная речь.

Цель – имя или номер игрока (например "5" или "Антон").
Если действие не распознано, верни {{"action": "chat"}}.
Формат ответа – JSON. Примеры:
{{"action": "nominate", "target": "Антон"}}
{{"action": "vote", "target": "3"}}
{{"action": "action", "action_type": "kill", "target": "Мария"}}

Игроки (живые): {players_list}
Текущая фаза: {phase}
Роль игрока: {role}
"""
    
    async def parse(self, text: str, phase: str, role: str, players: List[str]) -> Dict[str, Any]:
        # Сначала попробуем извлечь номер игрока регуляркой
        match_num = re.search(r'\b([1-9])\b', text)
        if match_num:
            num = int(match_num.group(1))
            if 1 <= num <= len(players):
                player_name = players[num-1]
                # Определим действие по ключевым словам
                if "выдвига" in text.lower() or "номин" in text.lower():
                    return {"action": "nominate", "target": player_name}
                elif "голосу" in text.lower() or "отдаю голос" in text.lower():
                    return {"action": "vote", "target": player_name}
                elif "убива" in text.lower() or "мочи" in text.lower() or "ликвидиру" in text.lower():
                    return {"action": "action", "action_type": "kill", "target": player_name}
                elif "проверя" in text.lower() or "шер" in text.lower():
                    return {"action": "action", "action_type": "check", "target": player_name}
                elif "леч" in text.lower() or "спас" in text.lower():
                    return {"action": "action", "action_type": "heal", "target": player_name}
        
        # Иначе вызываем LLM
        system_prompt = self.system_prompt_template.format(
            players_list=", ".join(players),
            phase=phase,
            role=role
        )
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=text)
        ]
        response = await self.llm.ainvoke(messages)
        try:
            # Извлечём JSON из ответа (может быть обёрнут в ```json ... ```)
            content = response.content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            result = json.loads(content)
            # Валидация
            if result.get("action") in ("nominate", "vote", "action", "chat"):
                return result
        except Exception:
            pass
        return {"action": "chat"} 