# Use official Python base image
FROM docker.arvancloud.ir/python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8501

# Set work directory
WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libportaudio2 \
    libsndfile1 \
    libasound-dev \
    && rm -rf /var/lib/apt/lists/*

# Install pip requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN apt-get update && apt-get install -y \
    alsa-utils \
    libasound2 \
    portaudio19-dev \
    libportaudiocpp0

RUN pip install openwakeword

# Copy application code
COPY . .

# Expose Streamlit port
EXPOSE ${PORT}

# Streamlit-specific environment variables
ENV STREAMLIT_SERVER_PORT=${PORT}
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_ENABLECORS=false
ENV STREAMLIT_SERVER_ENABLEXSENDHEADERS=true

# Entrypoint
CMD ["streamlit", "run", "app.py"]
