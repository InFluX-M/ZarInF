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
            self.porcupine = pvporcupine.create(
                access_key=access_key,
                keyword_paths=[keyword_paths]
            )
            self.pa = pyaudio.PyAudio()
            self.stream = self.pa.open(
                rate=self.porcupine.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=self.porcupine.frame_length
            )
            logger.info("✅ Wake Word model loaded.")
        except Exception as e:
            logger.exception(f"❌ Error during Wake Word initialization: {e}")

        try:
            self.vad_model, utils = torch.hub.load('snakers4/silero-vad', model=vad_model_name, trust_repo=True)
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

    def listen_for_wake_word(self):
        pcm = self.stream.read(self.porcupine.frame_length)
        pcm_int16 = np.frombuffer(pcm, dtype=np.int16)
        return self.porcupine.process(pcm_int16) >= 0

    def vad_detect(self, audio_np):
        audio_tensor = torch.from_numpy(audio_np)
        return self.get_speech_timestamps(audio_tensor, self.vad_model, sampling_rate=self.porcupine.sample_rate)

    def normalize_audio(self, audio):
        max_amp = np.max(np.abs(audio))
        return audio / max_amp if max_amp > 0 else audio

    def listen_for_command(self, max_silence_duration=2.0, min_speech_duration=2.0, max_command_duration=30.0):
        command_frames, silence_start, speech_time = [], None, 0
        start_time = time()
        while True:
            data = self.stream.read(self.porcupine.frame_length)
            frame_int16 = np.frombuffer(data, dtype=np.int16)
            command_frames.append(frame_int16)
            audio_np = np.concatenate(command_frames).astype(np.float32) / 32768.0
            speech_timestamps = self.vad_detect(audio_np)

            if speech_timestamps:
                silence_start = None
                speech_time = sum([(ts['end'] - ts['start']) / self.porcupine.sample_rate for ts in speech_timestamps])
            else:
                if silence_start is None:
                    silence_start = time()
                elif time() - silence_start > max_silence_duration and speech_time >= min_speech_duration:
                    break
            if time() - start_time > max_command_duration:
                break
        return self.normalize_audio(audio_np)


    async def detect_wake_word(self):
        while True:
            pcm = self.stream.read(self.porcupine.frame_length)
            pcm_int16 = np.frombuffer(pcm, dtype=np.int16)
            result = self.porcupine.process(pcm_int16)
            if result >= 0:
                return True
            await asyncio.sleep(0)  # yield control back to event loop

    async def async_listen_for_command(self):
        return await asyncio.to_thread(self.listen_for_command)
