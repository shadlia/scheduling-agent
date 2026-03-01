# 🎙️ Voice Scheduling Agent

A **real-time voice assistant** that schedules meetings through natural conversation and creates Google Calendar events — built entirely with **free, open-source technologies**.

> **Live Demo:** `[Coming Soon — will be deployed on Vercel]`

---

## ✨ Features

- 🗣️ **Real-time voice interaction** — speak naturally to schedule meetings
- 🤖 **AI-powered conversation** — understands context, asks follow-ups, confirms details
- 📅 **Google Calendar integration** — creates real calendar events automatically
- 🎨 **Modern, responsive UI** — dark mode, glassmorphism, animated mic button
- 🌐 **Fully deployed** — accessible via a hosted URL
- 💸 **100% free stack** — no paid APIs, no subscriptions

---

## 🏗️ Architecture

```
┌─────────────────────────────────────┐
│        Frontend (React + Vite)      │
│        Deployed on Vercel           │
│                                     │
│  ┌──────────┐    ┌───────────────┐  │
│  │ Voice UI │    │  Conversation │  │
│  │  (Mic)   │    │   Transcript  │  │
│  └────┬─────┘    └───────────────┘  │
│       │                             │
│  Web Speech API (STT + TTS)         │
│  Browser-native · Zero cost         │
└───────┬─────────────────────────────┘
        │ REST API (HTTPS)
        ▼
┌─────────────────────────────────────┐
│       Backend (Python FastAPI)      │
│       Deployed on Render.com        │
│                                     │
│  ┌──────────────┐  ┌────────────┐  │
│  │ Gemini 2.5   │  │  Google     │  │
│  │ Flash (Free) │  │  Calendar   │  │
│  │ Conversation │  │  API        │  │
│  │ Engine       │  │  Integration│  │
│  └──────────────┘  └────────────┘  │
└─────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

| Layer | Technology | Cost |
|-------|-----------|------|
| **Speech-to-Text** | Web Speech API (browser-native) | Free |
| **Text-to-Speech** | Web Speech API (browser-native) | Free |
| **LLM / AI** | Google Gemini 2.5 Flash | Free tier (1,000 req/day) |
| **Backend** | Python FastAPI | Free / Open-source |
| **Frontend** | React + Vite | Free / Open-source |
| **Calendar** | Google Calendar API | Free |
| **Backend Hosting** | Render.com | Free tier |
| **Frontend Hosting** | Vercel | Free tier |

### Why This Stack?

- **Web Speech API** — Built into Chrome/Edge browsers. Zero API keys, zero cost, zero latency for basic STT/TTS. We evaluated the **OpenAI Realtime API** but it costs ~$1/minute with no free tier — doesn't fit our 100% free requirement
- **Google Gemini 2.5 Flash** — Google's powerful multimodal model with a generous free tier (1,000 requests/day, 15 requests/minute). Excellent reasoning for natural language understanding
- **FastAPI** — Async Python framework, perfect for real-time API communication
- **React + Vite** — Lightweight, fast-building frontend with no unnecessary overhead

---

## 🚀 How It Works (Conversation Flow)

1. **🎤 Greeting** — "Hi! I'm your scheduling assistant. What's your name?"
2. **📅 Date & Time** — "When would you like to schedule the meeting?"
3. **📝 Title** *(optional)* — "Would you like to give the meeting a title?"
4. **✅ Confirmation** — "Let me confirm: meeting for [Name] on [Date] at [Time]. Shall I create it?"
5. **🎉 Created** — Creates the Google Calendar event → "Done! Your meeting has been scheduled!"

---

## 📋 Prerequisites

Before running locally, you'll need:

1. **Node.js** (v18+) — [Download](https://nodejs.org/)
2. **Python** (3.10+) — [Download](https://python.org/)
3. **Google Gemini API Key** (free) — [Get it from Google AI Studio](https://aistudio.google.com/apikey)
4. **Google Calendar API** credentials (free):
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project
   - Enable the **Google Calendar API**
   - Create a **Service Account** and download the JSON key
   - Share your Google Calendar with the service account email

---

## 🖥️ Local Development

### Backend Setup

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment variables
cp .env.example .env
# Edit .env with your Gemini API key and Google Calendar credentials

# Run the server
uvicorn main:app --reload --port 8000
```

### Frontend Setup

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Create .env file
echo "VITE_API_URL=http://localhost:8000" > .env

# Run dev server
npm run dev
```

Open **http://localhost:5173** in Chrome or Edge (required for Web Speech API).

---

## 📅 Calendar Integration Explained

This project uses the **Google Calendar API** with a **Service Account** for server-side event creation:

1. **Service Account** — A special Google account that acts on behalf of your application (no user login required)
2. **Calendar Sharing** — Your personal Google Calendar is shared with the service account email, granting it write access
3. **Event Creation** — When the user confirms meeting details via voice, the backend sends a `POST` request to the Google Calendar API with:
   - `summary` — Meeting title
   - `start.dateTime` — Start time (ISO 8601)
   - `end.dateTime` — End time (defaults to +1 hour)
   - `description` — Auto-generated with attendee name
4. **Confirmation** — The API returns the event link, which is displayed to the user

> **Why Service Account?** It's the simplest auth method — no OAuth consent screen, no user login flow. The service account is pre-authorized to write to your calendar.

---

## 🌐 Deployment

### Backend → Render.com

1. Push your code to GitHub
2. Connect your repo to [Render.com](https://render.com/)
3. Create a new **Web Service**
4. Set root directory to `backend`
5. Build command: `pip install -r requirements.txt`
6. Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
7. Add environment variables (`GROQ_API_KEY`, Google Calendar credentials)

### Frontend → Vercel

1. Connect your repo to [Vercel](https://vercel.com/)
2. Set root directory to `frontend`
3. Set `VITE_API_URL` environment variable to your Render backend URL
4. Deploy!

---

## 📸 Demo / Screenshots

> *Coming soon — screenshots and Loom video of a complete scheduling conversation with calendar event creation.*

---

## 📁 Project Structure

```
scheduling-agent/
├── README.md
├── backend/
│   ├── main.py              # FastAPI application
│   ├── config.py             # Environment variables
│   ├── requirements.txt      # Python dependencies
│   ├── .env.example          # Environment template
│   └── services/
│       ├── llm_service.py    # Groq LLM conversation engine
│       └── calendar_service.py  # Google Calendar integration
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   └── src/
│       ├── App.jsx           # Main application
│       ├── index.css         # Design system
│       ├── components/
│       │   ├── VoiceAssistant.jsx    # Voice UI + mic
│       │   ├── ConversationLog.jsx   # Chat transcript
│       │   └── MeetingCard.jsx       # Confirmed event card
│       ├── hooks/
│       │   ├── useSpeechRecognition.js
│       │   └── useSpeechSynthesis.js
│       └── services/
│           └── api.js        # Backend API client
└── .gitignore
```

---

## 📄 License

MIT License — free to use, modify, and distribute.

---

## 🙏 Acknowledgments

- [Google Gemini](https://ai.google.dev/) — Powerful AI with generous free tier
- [Google Calendar API](https://developers.google.com/calendar) — Calendar integration
- [Web Speech API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Speech_API) — Browser-native speech services
