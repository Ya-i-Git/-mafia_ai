# backend/audio/synthesizer.py
import edge_tts
import logging
from typing import AsyncGenerator

logger = logging.getLogger(__name__)

class TextToSpeech:
    def __init__(self, voice: str = "ru-RU-DariyaNeural"):
        """
        voice: выберите голос. Список можно получить через `edge_tts.list_voices()`
        Русские голоса: "ru-RU-DariyaNeural", "ru-RU-SvetlanaNeural"
        """
        self.voice = voice

    async def synthesize(self, text: str) -> bytes | None:
        """Синтезирует речь и возвращает аудио в формате MP3."""
        if not text:
            return None
            
        try:
            communicate = edge_tts.Communicate(text, self.voice)
            audio_data = b''
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_data += chunk["data"]
                    
            logger.info(f"Синтезировано аудио для: '{text[:30]}...'")
            return audio_data
            
        except Exception as e:
            logger.error(f"Ошибка синтеза речи: {e}")
            return None

    async def stream(self, text: str) -> AsyncGenerator[bytes, None]:
        """Генерирует аудио-чанки для потоковой передачи."""
        communicate = edge_tts.Communicate(text, self.voice)
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                yield chunk["data"]