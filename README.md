# 🎙️ Voice Scheduling Agent (Deployed)

**An open-source, full-stack voice AI scheduling assistant.**

A **real-time voice assistant** that schedules meetings through natural conversation and creates real Google Calendar events. 

Rather than relying on expensive abstraction layers or paid voice platforms (like VAPI or ElevenLabs), I chose to build this full-stack solution from scratch using a **100% free, developer-first tech stack**. This demonstrates a deep understanding of the underlying moving parts—from managing continuous STT/TTS loops in the browser to orchestrating stateful LLM conversations and OAuth flows on the backend.

> **Live Demo:** [https://scheduling-agent-ashy.vercel.app](https://scheduling-agent-ashy.vercel.app/)

> **Loom Demo:** [Watch the demo here](https://www.loom.com/share/5e2a1456e693415bb46985f7bbad1f71)

---

## 🎯 Core Features

- ✅ **Initiates Conversation:** The agent immediately greets the user and proactively offers to schedule a meeting upon launch.
- ✅ **Context Extraction:** Naturally asks for the user's name, preferred date & time, and meeting title.
- ✅ **Confirmation:** Summarizes and confirms the final details before taking action.
- ✅ **Calendar Event Creation:** Successfully creates a real event directly on the user's Google Calendar.
- ✅ **Deployed & Accessible:** Live on Vercel (Frontend) and Render (Backend).

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

## 🛠️ The Tech Stack (100% Free & Open-Source Approach)

I deliberately avoided "black-box" voice SaaS solutions to show how a robust, real-time agent can be built cost-effectively with core web technologies and raw LLM power.

| Component | Technology | Why I Chose It |
|-----------|-----------|-----------------|
| **Frontend** | React + Vite + Framer Motion | Lightweight, fast compilation, and allows for building a custom, premium "glassmorphic" UI with smooth mic animations. |
| **Speech-to-Text (STT) & TTS** | Web Speech API | Browser-native, zero-latency, and zero-cost. I implemented custom silence detection to manage conversation turns naturally. |
| **LLM Engine** | Google Gemini 2.5 Flash | Lightning fast, excellent reasoning capabilities for tool calling, and offers a generous free tier via Google AI Studio. |
| **State Management** | LangGraph (Python) | Perfect for managing stateful, cyclic conversational flows and ensuring the agent doesn't lose context between voice turns. |
| **Backend API** | FastAPI (Python 3.11) | High-performance, async-native framework that perfectly handles the real-time speed required for voice interactions. |
| **Integration** | Google Calendar API + OAuth2 | Secure, user-consented access to create real calendar events. |

---

## � Calendar Integration Explained

To ensure security and proper user attribution, I implemented a full **OAuth 2.0 Authorization Code Flow** rather than relying on a hardcoded Service Account. 

Here is how the integration works:

1. **User Authentication:** 
   - The user clicks "Connect Google" on the Vercel frontend.
   - They are securely redirected to the Google consent screen (via `@react-oauth/google`).
   - The user grants permission to the `https://www.googleapis.com/auth/calendar` scope.

2. **Token Exchange:** 
   - Google returns an Authorization Code to the React frontend.
   - The frontend sends this code to the FastAPI backend (`/auth/google`).
   - The backend securely exchanges the code (using the server's `client_secret`) for an **Access Token** and **Refresh Token**.
   - The tokens are securely passed back and stored client-side.

3. **Event Creation (Tool Calling):**
   - When the user confirms the meeting details via voice, the Gemini LLM triggers the `create_event` tool within the LangGraph state machine.
   - the frontend includes the User's Access Token in the payload.
   - The backend uses the `google-api-python-client` to inject the user's token and make an authenticated `POST` request to the Calendar API, successfully creating the event on the *user's specific calendar*.

---

## 🧪 How to Test the Agent

1. **Open the Live URL:** Go to [https://scheduling-agent-ashy.vercel.app](https://scheduling-agent-ashy.vercel.app/)
2. **Provide API Key:** The app operates on a "Bring Your Own Key" model. You will be prompted to enter a **Google Gemini API Key** (Get one for free at [Google AI Studio](https://aistudio.google.com/apikey)).
3. **Connect Calendar:** Click the "Connect Google" button in the Settings panel to authorize calendar access. *(Note: Since this app is in testing mode, you may see an "Unverified App" warning from Google. Click Advanced -> Continue).*
4. **Start Speaking:** Click "Start Experience" or the Microphone button. 
5. **Test the Flow:** 
   - Let the agent greet you.
   - Say: *"Hi, I need to schedule a meeting with John Doe."*
   - Let the agent guide you through picking a date and time.
   - Confirm the details when asked.
   - Check your actual Google Calendar to see the new event!

---

## 🧠 AI Agent Architecture (LangGraph)

Instead of relying on a simple script that loses context over time, the backend is built as a robust, cyclic State Machine using **LangGraph**. The architecture is fully modularized in `backend/services/agent/` to cleanly separate concerns:

1. **`state.py` (Memory):** Defines the `SchedulingState` object. It tracks the entire conversation history and strictly typed extracted data (Name, Date/Time, Title, Confirmation status).
2. **`nodes.py` (Execution Steps):** Contains the core logic blocks. Each node (`greeting`, `collect_info`, `confirm`, `create_event`) provides the LLM with a specific, isolated system prompt tailored to its current objective, drastically reducing hallucinations.
3. **`edges.py` (Routing & Extraction):** Acts as the brain's connective tissue. It parses the JSON output from the LLM via regex to update the state, and runs conditional routing logic to determine if the agent should keep collecting information or advance to the confirmation stage.
4. **`graph.py` (Orchestrator):** Compiles the nodes and edges into a directed cyclic graph. Crucially, it yields execution (`END`) back to the user after every logical turn, ensuring the AI never "runs away" and books a meeting without explicit human confirmation.

---

## 💻 Local Development Instructions (Optional)

If you wish to spin this up locally and inspect the code:

### 1. Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file in the `backend` directory:
```env
# Get these from Google Cloud Console (OAuth Credentials)
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
FRONTEND_URL=http://localhost:5173
```

Run the API:
```bash
uvicorn main:app --reload --port 8000
```

### 2. Frontend Setup

```bash
cd frontend
npm install
```

Create a `.env` file in the `frontend` directory:
```env
VITE_API_URL=http://localhost:8000/api
VITE_GOOGLE_CLIENT_ID=your_client_id
```

Run the UI:
```bash
npm run dev
```
*(Open http://localhost:5173 in Chrome or Edge for full Web Speech API support).*

---

Feel free to explore the code, deploy your own instance, or contribute to the project!
