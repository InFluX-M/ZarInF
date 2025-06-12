# 🤖 Smart Home Assistant with LLM Agents

A modular smart home assistant powered by LLMs, speech processing, and voice control. Users can interact via wake word, text, or voice commands to control smart devices, get updates, and schedule tasks.

---

## 🌟 Features

- 🎙️ Wake word detection via OpenWakeWord (or Porcupine)
- 🧠 Voice Activity Detection (VAD) for clean transcription
- 🔤 Whisper-based transcription
- 💡 Device control (lamps, AC, TV, cooler)
- 📆 Task scheduling and reminders
- 🔄 Text and voice response support
- 📊 Real-time device status
- 🌐 LLM integration (Together.ai, OpenAI, Groq)

---

## 🗂️ Project Structure

```
.
├── backend/               # FastAPI backend
│   └── Dockerfile
├── frontend/              # Streamlit UI
│   └── Dockerfile
├── docker-compose.yml     # Multi-container setup
├── .env.example           # Template for API keys
└── README.md
```

---

## 🚀 Getting Started (Without Docker)

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/smart-home-assistant.git
cd smart-home-assistant
```

### 2. Configure API keys

Copy the example `.env` files and fill in your actual API keys:

```bash
touch backend/.env
touch frontend/.env
```

You’ll need:
- `TOGETHER_API_KEY`, `OPENAI_API_KEY`, `GROQ_API_KEY`
- `NEWS_API_KEY`, `OPENWEATHER_API_KEY`
- `ACCESS_KEY_WAKE_WORD`, `KEYWORD_PATHS_WAKE_WORD`

---

### 3. Run Backend (FastAPI)

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### 4. Run Frontend (Streamlit)

```bash
cd ../frontend
pip install -r requirements.txt
streamlit run app.py
```

---

## 🐳 Docker Setup (Recommended)

### 1. Build and start all services

From the project root:

```bash
docker compose up --build
```

This will:
- Build and run the **FastAPI backend** on port `8000`
- Build and run the **Streamlit frontend** on port `8501`
- Mount your audio devices for wake word detection

### 2. Visit the app

Open your browser and go to:

```
http://localhost:8501
```

---

## 🔐 Required API Keys

You’ll need to set up a `.env` file in both `frontend/` and `backend/`:

### Backend `.env`
```
TOGETHER_API_KEY=...
OPENAI_API_KEY=...
GROQ_API_KEY=...
NEWS_API_KEY=...
OPENWEATHER_API_KEY=...
```

### Frontend `.env`
```
ACCESS_KEY_WAKE_WORD=...
KEYWORD_PATHS_WAKE_WORD=Hey-Assistant_en_linux_v3_0_0.ppn
```

> ⚠️ Never commit `.env` files with real API keys.

---

## 🧪 API Endpoints

| Endpoint               | Method | Description                      |
|------------------------|--------|----------------------------------|
| `/upload-audio/`       | POST   | Upload a voice command           |
| `/send-command/`       | POST   | Send a text-based command        |
| `/device-statuses/`    | GET    | Fetch all current device states  |

---

## 📦 Dependencies

- Python 3.9+
- FastAPI, Streamlit
- Whisper, OpenWakeWord
- LangChain, HuggingFace, Together.ai
- ALSA / PortAudio for voice I/O

---

## 📌 Future Features

- Persian voice support
- Raspberry Pi deployment
- Voice calendar integration
- Smart scene creation (e.g., "Movie Mode")

---

## 👤 Authors

Matin Azami  
[GitHub](https://github.com/yourusername)

Zahra Masoumi  
[GitHub](https://github.com/asAlwaysZahra)

---

## 📄 License

MIT License

