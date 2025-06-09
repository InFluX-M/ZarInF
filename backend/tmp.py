import asyncio
from datetime import datetime
from agent import control_tv, control_cooler, control_ac, control_lamp, handle_user_request
from task_db import ScheduledTaskDBItem, get_due_tasks, delete_task, add_task, init_db
import asyncio
import threading
import time
import numpy as np
import sounddevice as sd
from openwakeword.model import Model
import whisper

FUNCTION_MAP = {
    "control_tv": control_tv,
    "control_cooler": control_cooler,
    "control_ac": control_ac,
    "control_lamp": control_lamp,
}

class ScheduledTask:
    def __init__(self, db_item: ScheduledTaskDBItem):
        self.db_item = db_item

    async def run(self):
        func = FUNCTION_MAP.get(self.db_item.function_name)
        if not func:
            print(f"❌ Unknown function name: {self.db_item.function_name}")
            return

        if hasattr(func, "ainvoke"):
            await func.ainvoke(self.db_item.kwargs)
        else:
            result = func(*self.db_item.args, **self.db_item.kwargs)
            if asyncio.iscoroutine(result):
                await result

async def scheduler_loop():
    while True:
        due_db_tasks = await get_due_tasks()
        for db_task in due_db_tasks:
            task = ScheduledTask(db_task)
            try:
                await task.run()
            except Exception as e:
                print(f"❌ Error running task {db_task.id}: {e}")
            await delete_task(db_task.id)
        await asyncio.sleep(1)

async def schedule_task(function_name: str, run_at: datetime, args=None, kwargs=None):
    await add_task(function_name, run_at, args=args, kwargs=kwargs)

async def handle_user_command(user_input: str):
    commands = handle_user_request(user_input)
    scheduled = []

    for fn_name, args, run_at in commands:
        await schedule_task(fn_name, run_at, kwargs=args)
        scheduled.append((fn_name, run_at))

    return scheduled

model = Model()
samplerate = 16000
frame_duration_ms = 80
frame_size = int(samplerate * frame_duration_ms / 1000)
COOLDOWN_SECONDS = 3

wakeword_detected_event = asyncio.Event()
last_detection_time = 0

whisper_model = whisper.load_model("large")

def audio_callback(indata, frames, time_info, status):
    global last_detection_time
    if status:
        print(status)
    audio_frame = (indata[:, 0] * 32768).astype(np.int16)
    prediction = model.predict(audio_frame)
    current_time = time.time()
    for ww, score in prediction.items():
        if score > 0.85 and (current_time - last_detection_time > COOLDOWN_SECONDS):
            last_detection_time = current_time
            # Set event in asyncio loop thread-safe way
            asyncio.run_coroutine_threadsafe(set_wakeword_event(), loop)

async def set_wakeword_event():
    wakeword_detected_event.set()

def start_wakeword_listener():
    with sd.InputStream(channels=1, samplerate=samplerate, blocksize=frame_size, callback=audio_callback):
        print("Wakeword detection started")
        while True:
            time.sleep(1)

async def record_audio_for_whisper(duration=5):
    print("🎙️ Recording audio for Whisper...")
    recording = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype='int16')
    sd.wait()
    audio = np.squeeze(recording).astype(np.float32) / 32768.0
    return audio

async def transcribe_audio(audio):
    print("📝 Transcribing audio with Whisper...")
    # Whisper expects 16kHz float32 mono audio, length at least 1 sec.
    result = whisper_model.transcribe(audio, language='en')
    return result['text']

async def wakeword_handler():
    while True:
        await wakeword_detected_event.wait()
        wakeword_detected_event.clear()

        # Record audio from mic after wakeword
        audio = await record_audio_for_whisper(duration=15)

        # Transcribe using Whisper
        text = await transcribe_audio(audio)
        print(f"🗣️ Transcribed text: {text}")

        # Pass to your async command handler (from your code)
        scheduled = await handle_user_command(text)
        print(f"Scheduled commands: {scheduled}")

async def main():
    global loop
    loop = asyncio.get_running_loop()

    await init_db()

    # Start your existing scheduler loop task
    asyncio.create_task(scheduler_loop())

    # Start wakeword handler async task
    asyncio.create_task(wakeword_handler())

    # Start wakeword detection thread
    threading.Thread(target=start_wakeword_listener, daemon=True).start()

    print("📡 Scheduler and Wakeword+Whisper running...")

    while True:
        await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(main())
