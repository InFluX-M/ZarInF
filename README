# 🤖 Smart Home Assistant with LLM Agents

A modular smart home assistant powered by LLMs, speech processing, and voice control. Users can interact via wake word, text, or voice commands to control smart devices, get updates, and schedule tasks.

---

## 🌟 Features

- 🎙️ Wake word detection via Porcupine
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
├── frontend/              # Streamlit UI
├── .env.example           # Environment variable template
└── README.md              # Project guide
```

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/smart-home-assistant.git
cd smart-home-assistant
```

### 2. Add environment variables

Copy the `.env.example` files into your frontend and backend directories:

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

Edit the `.env` files to include your own API keys and paths.

---

### 3. Backend setup

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

---

### 4. Frontend setup

```bash
cd ../frontend
pip install -r requirements.txt
streamlit run app.py
```

---

## 🌐 API Endpoints

| Endpoint               | Method | Description                      |
|------------------------|--------|----------------------------------|
| `/upload-audio/`       | POST   | Upload voice command             |
| `/send-command/`       | POST   | Send text command                |
| `/device-statuses/`    | GET    | Get status of all devices        |

---

## 🔐 Required API Keys

You’ll need the following keys in your `.env` files:

### Backend `.env`
- `TOGETHER_API_KEY`
- `OPENAI_API_KEY`
- `GROQ_API_KEY`
- `NEWS_API_KEY`
- `OPENWEATHER_API_KEY`

### Frontend `.env`
- `ACCESS_KEY_WAKE_WORD` – from Picovoice Console
- `KEYWORD_PATHS_WAKE_WORD` – path to `.ppn` file (e.g., `Hey-Assistant_en_linux_v3_0_0.ppn`)

> ⚠️ Do **not** commit your `.env` files with real API keys.

---

## 🛠 Dependencies

- Python 3.9+
- FastAPI
- Streamlit
- PyTorch + Torchaudio
- Picovoice Porcupine
- Whisper (via API or local)

---

## 📌 Future Ideas

- Persian voice support
- Raspberry Pi deployment
- Voice calendar integration
- Smart scene creation (e.g., "Movie Mode")

---

## 📄 License

MIT License

---

## 👤 Authors

Matin Azami  
[GitHub](https://github.com/InFluX-M)
Zahra Masoumi  
[GitHub](https://github.com/asAlwaysZahra)
