import asyncio
import os
import logging
from fastapi import FastAPI, UploadFile, File
from scheduler import handle_user_command, schedule_task, init_db, scheduler_loop
from assistant import VoiceAssistant
from scheduler import get_all_device_statuses

# --- Setup Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("log/assistant.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI()
assistant = VoiceAssistant(os.getenv("ACCESS_KEY"), os.getenv("KEYWORD_PATHS"))

@app.on_event("startup")
async def startup_event():
    logger.info("Starting up: initializing DB and scheduler loop.")
    await init_db()
    asyncio.create_task(scheduler_loop())
    logger.info("📡 Scheduler & FastAPI running...")

@app.post("/upload-audio/")
async def upload_audio(file: UploadFile = File(...)):
    logger.info(f"Received audio upload: {file.filename}")
    contents = await file.read()
    audio_path = f"temp/{file.filename}"
    os.makedirs("temp", exist_ok=True)

    with open(audio_path, "wb") as f:
        f.write(contents)
    logger.info(f"Saved uploaded audio to: {audio_path}")

    detected = await asyncio.to_thread(assistant.detect_wake_word, audio_path)
    logger.info(f"Wake word detection result: {detected}")

    if not detected:
        return {"status": "no wake word detected"}

    command = await asyncio.to_thread(assistant.transcribe_command, audio_path)
    logger.info(f"Transcribed command: {command}")

    scheduled = await handle_user_command(command)
    logger.info(f"Scheduled tasks: {scheduled}")

    return {"command": command, "scheduled_tasks": scheduled}

@app.post("/send-command/")
async def send_command(command: str):
    logger.info(f"Received text command: {command}")
    scheduled = await handle_user_command(command)
    logger.info(f"Scheduled tasks: {scheduled}")
    return {"scheduled_tasks": scheduled}

@app.get("/device-statuses/")
async def device_statuses():
    statuses = await get_all_device_statuses()
    logger.info(f"Fetched all device statuses: {statuses}")
    return statuses
