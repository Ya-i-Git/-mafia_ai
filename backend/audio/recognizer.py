import logging
import asyncio
import tempfile
import os
from functools import partial
from faster_whisper import WhisperModel
from concurrent.futures import ThreadPoolExecutor


logger = logging.getLogger(__name__)

class AudioRecognizer:
    def __init__(self, model_size: str = "base", device: str = "cpu", compute_type: str = "int8"):
        """
        model_size: "tiny", "base", "small", "medium", "large-v3"
        device: "cpu" или "cuda"
        compute_type: "int8_float16", "int8", "float16"
        """
        logger.info(f"Загрузка faster-whisper модели: {model_size} (device={device})")
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
        self.executor = ThreadPoolExecutor(max_workers=2)

    async def transcribe(self, audio_bytes: bytes, sample_rate: int = 16000) -> str | None:
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as f:
                f.write(audio_bytes)
                tmp_path = f.name

            loop = asyncio.get_event_loop()
            transcribe_fn = partial(
                self.model.transcribe,
                tmp_path,
                beam_size=5,
                language="ru",
                vad_filter=True
            )
            segments, info = await loop.run_in_executor(self.executor, transcribe_fn)
            transcribed_text = " ".join(s.text for s in segments)
            logger.info(f"Распознано: '{transcribed_text}'")
            return transcribed_text.strip() or None
        except Exception as e:
            logger.error(f"Ошибка распознавания: {e}", exc_info=True)
            return None
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)