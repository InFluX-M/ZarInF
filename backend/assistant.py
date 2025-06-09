import pvporcupine
import pyaudio
import numpy as np
import whisper
import torch
from time import time
import asyncio

class VoiceAssistant:
    def __init__(self, access_key, keyword_paths, vad_model_name='silero_vad', whisper_model_name="base"):
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
        self.vad_model, utils = torch.hub.load('snakers4/silero-vad', model=vad_model_name, trust_repo=True)
        (self.get_speech_timestamps, _, _, _, _) = utils
        self.whisper_model = whisper.load_model(whisper_model_name)

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

    def transcribe_command(self, audio):
        result = self.whisper_model.transcribe(audio, fp16=False, language="en")
        return result.get("text", "").strip()

    def close(self):
        self.stream.stop_stream()
        self.stream.close()
        self.pa.terminate()
        self.porcupine.delete()

    # Async wrappers
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

    async def async_transcribe_command(self, audio):
        return await asyncio.to_thread(self.transcribe_command, audio)
