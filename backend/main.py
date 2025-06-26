import asyncio
import os
import logging
import io
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import torch
import torchaudio

from scheduler import handle_user_command, schedule_task, init_db, scheduler_loop, get_all_device_statuses
from assistant import VoiceAssistant

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
        app.state.assistant = VoiceAssistant()
        logger.info("🧠 VoiceAssistant initialized.")
    except Exception as e:
        logger.exception("❌ Failed to initialize VoiceAssistant.")

    asyncio.create_task(scheduler_loop())
    logger.info("📡 Scheduler loop started.")

@app.post("/upload-audio/")
async def upload_audio(file: UploadFile = File(...), response_type: str = "text"):
    logger.info(f"📥 Received audio upload: {file.filename}")
    
    contents = await file.read()
    os.makedirs("temp", exist_ok=True)
    audio_path = os.path.join("temp", file.filename)
    with open(audio_path, "wb") as f:
        f.write(contents)
    logger.info(f"💾 Saved uploaded audio to: {audio_path}")

    # Load and resample before VAD
    wav, sr = torchaudio.load(audio_path)
    if sr != 16000:
        logger.info(f"🔄 Resampling from {sr}Hz to 16000Hz before VAD")
        resampler = torchaudio.transforms.Resample(orig_freq=sr, new_freq=16000)
        wav = resampler(wav)
        sr = 16000

        # Save resampled wav for VAD input
        resampled_path = os.path.join("temp", f"resampled_{file.filename}")
        torchaudio.save(resampled_path, wav, sample_rate=sr)
    else:
        resampled_path = audio_path

    # Now run VAD on the 16kHz resampled audio file
    logger.info("🧠 Running VAD preprocessing...")
    speech_segments = await app.state.assistant.async_vad_detect(resampled_path)
    
    if not speech_segments:
        logger.warning("⚠️ No speech segments detected.")
        return {"response": "No speech detected in the audio."}

    # Concatenate detected speech parts (already 16kHz)
    speech_parts = [wav[:, seg['start']:seg['end']] for seg in speech_segments]
    speech_audio = torch.cat(speech_parts, dim=1)

    vad_audio_path = os.path.join("temp", f"vad_{file.filename}")
    torchaudio.save(vad_audio_path, speech_audio, sample_rate=sr)
    logger.info(f"✅ VAD-processed audio saved to: {vad_audio_path}")

    # Transcribe and handle the rest...
    command = await asyncio.to_thread(app.state.assistant.transcribe_command, vad_audio_path)
    logger.info(f"🗣️ Transcribed command: {command}")

    response = await handle_user_command(command.lower())
    logger.info(f"✅ Response: {response}")

    if response_type.lower() == "voice":
        logger.info("🔊 Returning audio response")
        audio_stream = await app.state.assistant.text_to_speech(response)
        audio_stream.seek(0)

        output_path = os.path.join("output", "output.mp3")
        os.makedirs("output", exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(audio_stream.read())
        audio_stream.seek(0)

        return StreamingResponse(audio_stream, media_type="audio/mpeg")

    return {"response": response}


# --- Send Command via JSON ---
@app.post("/send-command/")
async def send_command(request: CommandRequest):
    logger.info(f"✉️ Received text command: {request.command}")
    
    response = await handle_user_command(request.command.lower())
    logger.info(f"✅ Response: {response}")

    if request.response_type.lower() == "voice":
        logger.info("🔊 Returning audio response")
        audio_stream = app.state.assistant.text_to_speech(response)
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
    return {"response": response}

# --- Get Device Statuses ---
@app.get("/device-statuses/")
async def device_statuses():
    statuses = await get_all_device_statuses()
    logger.info(f"📊 Fetched all device statuses: {statuses}")
    return statuses
