import asyncio
import os
import logging
import io
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse
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
async def upload_audio(file: UploadFile = File(...), response_type: str = "text" ):
    logger.info(f"📥 Received audio upload: {file.filename}")
    contents = await file.read()
    os.makedirs("temp", exist_ok=True)
    audio_path = f"temp/{file.filename}"

    with open(audio_path, "wb") as f:
        f.write(contents)
    logger.info(f"💾 Saved uploaded audio to: {audio_path}")

    command = await asyncio.to_thread(app.state.assistant.transcribe_command, audio_path)
    logger.info(f"🗣️ Transcribed command: {command}")

    scheduled = await handle_user_command(command)
    logger.info(f"✅ Scheduled tasks: {scheduled}")

    # Convert to readable text
    lines = []
    for func, dt, action, room in scheduled:
        dt_str = dt.strftime("%Y-%m-%d %H:%M:%S")
        line = f"{func} {room} {action} in {dt_str}" if room else f"{func} {action} in {dt_str}"
        lines.append(line)

    TTS_text = "\nand".join(lines)
    TTS_text = TTS_text.replace('_', ' ')

    if response_type.lower() == "voice":
        logger.info("🔊 Returning audio response for upload-audio")
        audio_stream = app.state.assistant.text_to_speech(TTS_text)
        if isinstance(audio_stream, bytes):  # If TTS returns bytes
            audio_stream = io.BytesIO(audio_stream)
        
        if isinstance(audio_stream, bytes):
            with open("/output/output.mp3", "wb") as f:
                f.write(audio_stream)
        else:
            print(111)
            audio_stream.seek(0)
            with open("/output/output.mp3", "wb") as f:
                f.write(audio_stream.read())

        return StreamingResponse(audio_stream, media_type="audio/mpeg")

    return {"command": command, "scheduled_tasks": scheduled}

@app.post("/send-command/")
async def send_command(command: str, response_type: str = "text"):
    logger.info(f"✉️ Received text command: {command}")
    
    scheduled = await handle_user_command(command)
    logger.info(f"✅ Scheduled tasks: {scheduled}")

    # Convert task tuples to readable text
    lines = []
    for func, dt, action, room in scheduled:
        dt_str = dt.strftime("%Y-%m-%d %H:%M:%S")
        line = f"{func} {room} {action} in {dt_str}" if room else f"{func} {action} in {dt_str}"
        lines.append(line)

    TTS_text = "\nand".join(lines)
    TTS_text = TTS_text.replace('_', ' ')

    # Choose response based on response_type
    if response_type.lower() == "voice":
        logger.info("🔊 Returning audio response")
        audio_stream = app.state.assistant.text_to_speech(TTS_text)
        if isinstance(audio_stream, bytes):  # If TTS returns bytes
            audio_stream = io.BytesIO(audio_stream)

        if isinstance(audio_stream, bytes):
            with open("output/output.mp3", "wb") as f:
                f.write(audio_stream)
        else:
            print(111)
            audio_stream.seek(0)
            with open("output/output.mp3", "wb") as f:
                f.write(audio_stream.read())

        return StreamingResponse(audio_stream, media_type="audio/mpeg")

    # Default is text/JSON
    logger.info("💬 Returning text response")
    return {"command": command, "scheduled_tasks": scheduled}

@app.get("/device-statuses/")
async def device_statuses():
    statuses = await get_all_device_statuses()
    logger.info(f"📊 Fetched all device statuses: {statuses}")
    return statuses
