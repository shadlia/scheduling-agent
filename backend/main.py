import json
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import settings
from services.llm_service import process_message
from services.calendar_service import list_events
from services.auth_service import exchange_code_for_token

# ─── App Setup ────────────────────────────────────────────────────────

app = FastAPI(
    title="Voice Scheduling Agent",
    description="AI-powered voice assistant that schedules meetings via Google Calendar",
    version="1.0.0",
)

# CORS — allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.FRONTEND_URL,
        "http://localhost:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Request/Response Models ─────────────────────────────────────────

class ChatRequest(BaseModel):
    """Incoming chat message from the frontend."""
    message: str
    conversation_state: Optional[dict] = None
    user_token: Optional[dict] = None  # NEW: OAuth token for the user
    gemini_api_key: Optional[str] = None  # NEW: User's own Gemini API key


class ChatResponse(BaseModel):
    """Response sent back to the frontend."""
    response: str
    state: dict
    event: Optional[dict] = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    timestamp: str
    services: dict


# ─── Endpoints ────────────────────────────────────────────────────────

@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint to verify the service is running."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        services={
            "calendar": bool(settings.GOOGLE_CALENDAR_ID),
        },
    )


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Process a chat message through the scheduling agent.

    Send a user message along with the current conversation state.
    Returns the AI response and updated state.
    """
    if not request.gemini_api_key:
        raise HTTPException(status_code=400, detail="Gemini API Key is missing. Please provide it in the Settings.")
    
    try:
        result = await process_message(
            user_message=request.message,
            conversation_state=request.conversation_state or {},
            user_token=request.user_token,
            gemini_api_key=request.gemini_api_key,
        )

        return ChatResponse(
            response=result["response"],
            state=result["state"],
            event=result.get("event"),
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing message: {str(e)}",
        )


@app.post("/api/auth/google")
async def google_auth(request: dict):
    """
    Exchange authorization code for a token.
    """
    print(f"DEBUG: Received Auth Request: {request}")
    code = request.get("code")
    if not code:
        print("DEBUG: Authorization code missing in request")
        raise HTTPException(status_code=400, detail="Authorization code missing")
    
    try:
        print(f"DEBUG: Attempting exchange for code: {code[:10]}...")
        token_data = exchange_code_for_token(code)
        print(f"DEBUG: Exchange Successful. Token issued: {token_data.get('access_token')[:10]}...")
        return token_data
    except Exception as e:
        print(f"DEBUG: Exchange Failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


class StartRequest(BaseModel):
    """Payload for starting a new conversation."""
    gemini_api_key: str


@app.post("/api/start", response_model=ChatResponse)
async def start_conversation(req: StartRequest):
    """
    Start a new conversation — returns the initial greeting.
    Called when the user first opens the app or clicks 'New Conversation'.
    """
    if not req.gemini_api_key:
        raise HTTPException(status_code=400, detail="Gemini API Key is missing. Please provide it in the Settings.")

    try:
        result = await process_message(
            user_message="",
            conversation_state={"current_step": "greeting"},
            gemini_api_key=req.gemini_api_key,
        )

        return ChatResponse(
            response=result["response"],
            state=result["state"],
            event=None,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error starting conversation: {str(e)}",
        )


@app.get("/api/calendar/events")
async def get_calendar_events(
    token: Optional[str] = None,
    time_min: Optional[str] = None,
    time_max: Optional[str] = None
):
    """Fetch upcoming events from Google Calendar (Service Account or User)."""
    try:
        user_token = None
        if token:
            user_token = json.loads(token)
            
        events = list_events(user_token=user_token, time_min=time_min, time_max=time_max)
        return events
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching calendar events: {str(e)}",
        )


# ─── Run ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    import json # Need json for parsing token in endpoint

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.BACKEND_PORT,
        reload=True,
    )
