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

```env
# === LLM Providers ===
TOGETHER_API_KEY=your_together_api_key           # Get from https://www.together.ai/api-keys
GROQ_API_KEY=your_groq_api_key                   # Get from https://console.groq.com/
OPENAI_API_KEY=your_openai_api_key               # Get from https://platform.openai.com/account/api-keys

# === External APIs ===
OPENWEATHER_API_KEY=your_openweather_api_key     # Get from https://openweathermap.org/api
NEWS_API_KEY=your_newsapi_key                    # Get from https://newsapi.org/

# === Wake Word Detection (Porcupine) ===
ACCESS_KEY_WAKE_WORD=your_picovoice_access_key   # Get from https://console.picovoice.ai/
KEYWORD_PATHS_WAKE_WORD=keywords/kitchen.ppn     # Path to .ppn keyword file(s)

# === LLM Backend Selection ===
API_AGENT=GROQ                                   # Choose: TOGETHER or GROQ
API_COND=GROQ                                    # Choose: TOGETHER or GROQ
API_RES=GROQ                                     # Choose: TOGETHER or GROQ

# === Optional Proxy Configuration ===
OPENAI_PROXY=socks5://127.0.0.1:2080             # Optional proxy, or leave blank
```

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
[GitHub](https://github.com/InFluX-M)

Zahra Masoumi  
[GitHub](https://github.com/asAlwaysZahra)

---

## 📄 License

MIT License :)

