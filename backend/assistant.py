import pvporcupine
import pyaudio
import numpy as np
import whisper
import torch
import logging
from time import time
import asyncio
from gtts import gTTS
import io

from dotenv import load_dotenv
load_dotenv()

# --- Logging setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("log/voice_assistant.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class VoiceAssistant:
    def __init__(self, access_key, keyword_paths, vad_model_name='silero_vad', whisper_model_name="base"):
        logger.info("🔧 Initializing VoiceAssistant...")
        try:
            self.whisper_model = whisper.load_model(whisper_model_name)
            logger.info("✅ Whisper model loaded.")
        except Exception as e:
            logger.exception(f"❌ Error during VoiceAssistant initialization: {e}")

    def transcribe_command(self, audio):
        logger.info("🔤 Transcribing audio to text...")
        try:
            result = self.whisper_model.transcribe(audio, fp16=False, language="en")
            text = result.get("text", "").strip()
            logger.info(f"📄 Transcription result: {text}")
            return text
        except Exception as e:
            logger.exception(f"❌ Error during transcription: {e}")
            return ""

    def close(self):
        logger.info("🔌 Releasing audio and Porcupine resources.")
        try:
            self.stream.stop_stream()
            self.stream.close()
            self.pa.terminate()
            self.porcupine.delete()
            logger.info("✅ Resources successfully released.")
        except Exception as e:
            logger.exception(f"❌ Error while closing audio resources: {e}")


    def text_to_speech(self, text, lang='en'):
        tts = gTTS(text=text, lang=lang)
        audio_bytes = io.BytesIO()
        tts.write_to_fp(audio_bytes)
        audio_bytes.seek(0)
        return audio_bytes  

    async def async_transcribe_command(self, audio):
        return await asyncio.to_thread(self.transcribe_command, audio)
    
    async def async_text_to_speech(self, text):
        return await asyncio.to_thread(self.text_to_speech, text)
