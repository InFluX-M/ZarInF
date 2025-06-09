import asyncio
import os
import logging
from fastapi import FastAPI, UploadFile, File
from scheduler import handle_user_command, schedule_task, init_db, scheduler_loop, get_all_device_statuses
from assistant import VoiceAssistant
from dotenv import load_dotenv
load_dotenv()

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

@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Starting up: initializing DB and assistant.")
    await init_db()

    # Initialize assistant and store in app state
    try:
        access_key = os.getenv("ACCESS_KEY")
        keyword_paths = os.getenv("KEYWORD_PATHS")
        app.state.assistant = VoiceAssistant(access_key, keyword_paths)
        logger.info("🧠 VoiceAssistant initialized.")
    except Exception as e:
        logger.exception("❌ Failed to initialize VoiceAssistant.")

    # Start scheduler
    asyncio.create_task(scheduler_loop())
    logger.info("📡 Scheduler loop started.")

@app.post("/upload-audio/")
async def upload_audio(file: UploadFile = File(...)):
    logger.info(f"📥 Received audio upload: {file.filename}")
    contents = await file.read()
    os.makedirs("temp", exist_ok=True)
    audio_path = f"temp/{file.filename}"

    with open(audio_path, "wb") as f:
        f.write(contents)
    logger.info(f"💾 Saved uploaded audio to: {audio_path}")

    assistant = app.state.assistant
    command = await asyncio.to_thread(assistant.transcribe_command, audio_path)
    logger.info(f"🗣️ Transcribed command: {command}")

    scheduled = await handle_user_command(command)
    logger.info(f"✅ Scheduled tasks: {scheduled}")
    return {"command": command, "scheduled_tasks": scheduled}

@app.post("/send-command/")
async def send_command(command: str):
    logger.info(f"✉️ Received text command: {command}")
    scheduled = await handle_user_command(command)
    logger.info(f"✅ Scheduled tasks: {scheduled}")
    return {"scheduled_tasks": scheduled}

@app.get("/device-statuses/")
async def device_statuses():
    statuses = await get_all_device_statuses()
    logger.info(f"📊 Fetched all device statuses: {statuses}")
    return statuses
