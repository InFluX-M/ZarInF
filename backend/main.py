import asyncio
import os
import logging
import io
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from scheduler import handle_user_command, schedule_task, init_db, scheduler_loop, get_all_device_statuses
from assistant import VoiceAssistant

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

# --- Enable CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Model for JSON Command Input ---
class CommandRequest(BaseModel):
    command: str
    response_type: str = "text"

# --- Startup Events ---
@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Starting up: initializing DB and assistant.")
    await init_db()

    try:
        access_key = os.getenv("ACCESS_KEY")
        keyword_paths = os.getenv("KEYWORD_PATHS")
        app.state.assistant = VoiceAssistant(access_key, keyword_paths)
        logger.info("🧠 VoiceAssistant initialized.")
    except Exception as e:
        logger.exception("❌ Failed to initialize VoiceAssistant.")

    asyncio.create_task(scheduler_loop())
    logger.info("📡 Scheduler loop started.")

# --- Upload Audio Endpoint ---
@app.post("/upload-audio/")
async def upload_audio(file: UploadFile = File(...), response_type: str = "text"):
    logger.info(f"📥 Received audio upload: {file.filename}")
    contents = await file.read()
    os.makedirs("temp", exist_ok=True)
    audio_path = os.path.join("temp", file.filename)

    with open(audio_path, "wb") as f:
        f.write(contents)
    logger.info(f"💾 Saved uploaded audio to: {audio_path}")

    command = await asyncio.to_thread(app.state.assistant.transcribe_command, audio_path)
    logger.info(f"🗣️ Transcribed command: {command}")

    scheduled = await handle_user_command(command)
    logger.info(f"✅ Scheduled tasks: {scheduled}")

    # Format response
    TTS_text = "\nand".join(
        f"{func} {room} {action} in {dt.strftime('%Y-%m-%d %H:%M:%S')}" if room
        else f"{func} {action} in {dt.strftime('%Y-%m-%d %H:%M:%S')}"
        for func, dt, action, room in scheduled
    ).replace('_', ' ')

    if response_type.lower() == "voice":
        logger.info("🔊 Returning audio response for upload-audio")
        audio_stream = app.state.assistant.text_to_speech(TTS_text)
        if isinstance(audio_stream, bytes):
            audio_stream = io.BytesIO(audio_stream)
        audio_stream.seek(0)

        output_path = os.path.join("output", "output.mp3")
        os.makedirs("output", exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(audio_stream.read())

        audio_stream.seek(0)
        return StreamingResponse(audio_stream, media_type="audio/mpeg")

    return {"command": command, "scheduled_tasks": scheduled}

# --- Send Command via JSON ---
@app.post("/send-command/")
async def send_command(request: CommandRequest):
    logger.info(f"✉️ Received text command: {request.command}")
    
    scheduled = await handle_user_command(request.command)
    logger.info(f"✅ Scheduled tasks: {scheduled}")

    # Format response
    TTS_text = "\nand".join(
        f"{func} {room} {action} in {dt.strftime('%Y-%m-%d %H:%M:%S')}" if room
        else f"{func} {action} in {dt.strftime('%Y-%m-%d %H:%M:%S')}"
        for func, dt, action, room in scheduled
    ).replace('_', ' ')

    if request.response_type.lower() == "voice":
        logger.info("🔊 Returning audio response")
        audio_stream = app.state.assistant.text_to_speech(TTS_text)
        if isinstance(audio_stream, bytes):
            audio_stream = io.BytesIO(audio_stream)
        audio_stream.seek(0)

        output_path = os.path.join("output", "output.mp3")
        os.makedirs("output", exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(audio_stream.read())

        audio_stream.seek(0)
        return StreamingResponse(audio_stream, media_type="audio/mpeg")

    logger.info("💬 Returning text response")
    return {"command": request.command, "scheduled_tasks": scheduled}

# --- Get Device Statuses ---
@app.get("/device-statuses/")
async def device_statuses():
    statuses = await get_all_device_statuses()
    logger.info(f"📊 Fetched all device statuses: {statuses}")
    return statuses
