# Use official Python image
FROM python:3.10-slim

# Install system dependencies needed for PyAudio and Whisper
RUN apt-get update && apt-get install -y \
    gcc \
    libasound-dev \
    portaudio19-dev \
    libportaudio2 \
    libportaudiocpp0 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Only copy the necessary files
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

RUN pip install python-multipart openai-whisper

# Copy all backend code except excluded ones
COPY . .

# Remove frontend directory from inside container (just in case)
RUN rm -rf frontend

# Expose FastAPI port
EXPOSE 8000

# Start FastAPI app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
