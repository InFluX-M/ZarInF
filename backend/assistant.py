import torch
import torchaudio
import whisper
import torch
import logging
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
    def __init__(self, whisper_model_name="base"):
        logger.info("🔧 Initializing VoiceAssistant...")

        try:
            self.vad_model, utils = torch.hub.load('snakers4/silero-vad', 'silero_vad', trust_repo=True)
            (self.get_speech_timestamps, _, _, _, _) = utils
            logger.info("✅ VAD model loaded.")
        except Exception as e:
            logger.exception(f"❌ Error during VAD initialization: {e}")

        try:
            self.whisper_model = whisper.load_model(whisper_model_name)
            logger.info("✅ Whisper model loaded.")
        except Exception as e:
            logger.exception(f"❌ Error during Whisper initialization: {e}")

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

    def vad_detect(self, audio_file):
        logger.info("🧠 Running VAD detection...")
        try:
            wav, sr = torchaudio.load(audio_file)
            print(sr)
            assert sr == 16000, "Sample rate must be 16kHz for Silero VAD"

            # Convert to mono if stereo
            if wav.shape[0] > 1:
                wav = wav.mean(dim=0, keepdim=True)
                logger.info("🔉 Converted stereo to mono for VAD")

            speech_timestamps = self.get_speech_timestamps(wav, self.vad_model, sampling_rate=sr)
            logger.info(f"🔍 Detected {len(speech_timestamps)} speech segments")
            return speech_timestamps
        except Exception as e:
            logger.exception(f"❌ Error during VAD detection: {e}")
            return []
            
    async def async_vad_detect(self, audio_file):
        return await asyncio.to_thread(self.vad_detect, audio_file)

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
