import pvporcupine
import pyaudio
import numpy as np
import whisper
import torch
from time import time

class VoiceAssistant:
    def __init__(self, access_key, keyword_paths, vad_model_name='silero_vad', whisper_model_name="base"):
        # Load wake word detector
        self.porcupine = pvporcupine.create(
            access_key=access_key,
            keyword_paths=keyword_paths
        )
        
        # Setup audio stream
        self.pa = pyaudio.PyAudio()
        self.stream = self.pa.open(
            rate=self.porcupine.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=self.porcupine.frame_length
        )

        # Load VAD model
        self.vad_model, utils = torch.hub.load('snakers4/silero-vad', model=vad_model_name, trust_repo=True)
        (self.get_speech_timestamps, _, _, _, _) = utils
        
        # Load Whisper ASR model
        self.whisper_model = whisper.load_model(whisper_model_name)

    def vad_detect(self, audio_np):
        audio_tensor = torch.from_numpy(audio_np)
        speech_timestamps = self.get_speech_timestamps(audio_tensor, self.vad_model, sampling_rate=self.porcupine.sample_rate)
        return speech_timestamps

    @staticmethod
    def normalize_audio(audio):
        max_amp = np.max(np.abs(audio))
        if max_amp > 0:
            return audio / max_amp
        return audio

    def listen_for_wake_word(self):
        pcm = self.stream.read(self.porcupine.frame_length)
        pcm_int16 = np.frombuffer(pcm, dtype=np.int16)
        result = self.porcupine.process(pcm_int16)
        return result >= 0

    def listen_for_command(self,
                           max_silence_duration=1.0,
                           min_speech_duration=0.5,
                           max_command_duration=10.0):
        command_frames = []
        silence_start = None
        speech_time = 0
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

        command_audio = self.normalize_audio(audio_np)
        return command_audio

    def transcribe_command(self, audio):
        result = self.whisper_model.transcribe(audio, fp16=False, language="en")
        command = result.get("text", "").strip()
        return command

    def close(self):
        self.stream.stop_stream()
        self.stream.close()
        self.pa.terminate()
        self.porcupine.delete()


def main():
    ACCESS_KEY = "KjFJIHycu/LCghU3SFVYv1XzoC/KSW6mDxQWBmc4K8I+ktk6hKL6Mw=="
    KEYWORD_PATHS = ["D:\\Downloads\\hey-assistant_en_windows_v3_0_0.ppn"]

    assistant = VoiceAssistant(ACCESS_KEY, KEYWORD_PATHS)
    print("Listening for wake word...")

    try:
        while True:
            if assistant.listen_for_wake_word():
                print("Wake word detected! Listening for command...")
                command_audio = assistant.listen_for_command()
                command = assistant.transcribe_command(command_audio)
                print(f"Command: {command}")

                if "turn off" in command.lower():
                    print("Turning off the program...")
                    break

                print("Listening for wake word...")

    except KeyboardInterrupt:
        print("Stopping...")

    finally:
        assistant.close()


if __name__ == "__main__":
    main()
