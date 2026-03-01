"""
LangGraph Scheduling Agent — A stateful conversation graph that:
1. Greets the user and asks for their name
2. Collects preferred date & time
3. Asks for an optional meeting title
4. Confirms all details
5. Creates a Google Calendar event

Uses Google Gemini 2.5 Flash via langchain-google-genai.
"""

import json
import re
from datetime import datetime, timedelta
from typing import Annotated, Optional

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field

from config import settings
from services.calendar_service import create_event

# ─── State Definition ────────────────────────────────────────────────

class SchedulingState(BaseModel):
    """State tracked throughout the scheduling conversation."""

    messages: Annotated[list, add_messages] = Field(default_factory=list)
    name: Optional[str] = None
    date_time: Optional[str] = None  # ISO format string
    meeting_title: Optional[str] = None
    confirmed: bool = False
    event_created: bool = False
    event_link: Optional[str] = None
    current_step: str = "greeting"  # greeting | collect_info | confirm | create_event | done
    user_token: Optional[dict] = None  # NEW: Google OAuth2 token
    gemini_api_key: Optional[str] = None  # NEW: User's own Gemini API key


# ─── LLM Setup ────────────────────────────────────────────────────────

def _get_llm(api_key: str = None):
    """Initialize Gemini model with a mandatory API key."""
    if not api_key:
        raise ValueError("Gemini API Key is missing. Please provide it in the Settings.")
    
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=api_key,
        temperature=0.7,
    )


# ─── System Prompt ────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a friendly, professional voice scheduling assistant. Your job is to help users schedule meetings by collecting their information through natural conversation.

IMPORTANT RULES:
- Be conversational and warm, but concise (this is for voice — keep responses SHORT, 1-2 sentences max)
- You need to collect: name, date/time, and optionally a meeting title
- INITIAL GREETING: Your first message should always greet the user and proactively ask if they want to schedule a meeting or add something to their calendar.
- When the user gives you information, acknowledge it naturally
- Always respond in plain text (no markdown, no bullet points, no special formatting) — your response will be read aloud
- Use natural date references (today, tomorrow, next Monday, etc.) and confirm with specific dates

CURRENT STATE:
{state_info}

Based on the current state, generate an appropriate response. If you have enough info, ask for confirmation.

EXTRACTION RULES:
After your conversational response, if the user's message contains scheduling info, add a JSON block at the very end in this exact format:
```json
{{"extracted_name": "value or null", "extracted_datetime": "ISO format or null", "extracted_title": "value or null", "confirmed": true/false}}
```

Only include the JSON block if there's new information to extract. If the user is just chatting or saying hello, don't include it.
For date/time, convert relative dates (tomorrow, next Tuesday, etc.) to actual ISO dates based on today being {today}.
"""


# ─── Graph Nodes ──────────────────────────────────────────────────────

def greeting_node(state: SchedulingState) -> dict:
    """Initial greeting — only triggered for the first message."""
    llm = _get_llm(state.gemini_api_key)
    today = datetime.now().strftime("%Y-%m-%d (%A)")

    state_info = "This is the START of the conversation. Greet the user warmly, ask for their name, and proactively ask if they would like to schedule a new meeting today."

    system_msg = SystemMessage(content=SYSTEM_PROMPT.format(state_info=state_info, today=today))
    
    # Gemini requires at least one HumanMessage
    messages = [system_msg]
    if not state.messages:
        messages.append(HumanMessage(content="Hello! Please start the scheduling conversation by greeting me."))
    else:
        messages.extend(state.messages)

    response = llm.invoke(messages)

    return {
        "messages": [response],
        "current_step": "collect_info",
    }


def collect_info_node(state: SchedulingState) -> dict:
    """Collect name, date/time, title from the user."""
    llm = _get_llm(state.gemini_api_key)
    today = datetime.now().strftime("%Y-%m-%d (%A)")

    collected = []
    missing = []

    if state.name:
        collected.append(f"Name: {state.name}")
    else:
        missing.append("name")

    if state.date_time:
        collected.append(f"Date/Time: {state.date_time}")
    else:
        missing.append("preferred date and time for the meeting")

    if state.meeting_title:
        collected.append(f"Meeting Title: {state.meeting_title}")

    state_info = f"""
Already collected: {', '.join(collected) if collected else 'Nothing yet'}
Still need: {', '.join(missing) if missing else 'All required info collected!'}
Meeting title is optional — if name and date/time are collected, ask if they want to add a title or proceed to confirmation.
If all required info is collected, summarize the details and ask the user to confirm.
"""

    system_msg = SystemMessage(content=SYSTEM_PROMPT.format(state_info=state_info, today=today))

    # Ensure we have at least one HumanMessage
    messages = [system_msg]
    if not state.messages:
        messages.append(HumanMessage(content="Continue collecting information."))
    else:
        messages.extend(state.messages)

    response = llm.invoke(messages)

    # Parse extraction JSON from the response
    updates = _parse_extraction(response.content, state)
    updates["messages"] = [AIMessage(content=_clean_response(response.content))]

    return updates


def confirm_node(state: SchedulingState) -> dict:
    """Handle user confirmation."""
    llm = _get_llm(state.gemini_api_key)
    today = datetime.now().strftime("%Y-%m-%d (%A)")

    state_info = f"""
The user has been asked to confirm these meeting details:
- Name: {state.name}
- Date/Time: {state.date_time}
- Title: {state.meeting_title or 'Meeting with ' + (state.name or 'User')}

Check if the user's latest message is a confirmation (yes, sure, correct, go ahead, etc.) or a rejection/change request.
If confirmed, respond with something like "Creating your meeting now..."
If they want changes, ask what they'd like to change.
"""

    system_msg = SystemMessage(content=SYSTEM_PROMPT.format(state_info=state_info, today=today))

    # Ensure we have at least one HumanMessage
    messages = [system_msg]
    if not state.messages:
        messages.append(HumanMessage(content="Checking for confirmation."))
    else:
        messages.extend(state.messages)

    response = llm.invoke(messages)

    # Check if user confirmed
    last_user_msg = ""
    for msg in reversed(state.messages):
        if isinstance(msg, HumanMessage):
            last_user_msg = msg.content.lower()
            break

    confirmation_words = ["yes", "yeah", "yep", "sure", "correct", "confirm", "go ahead", "do it", "create", "book", "schedule", "ok", "okay", "perfect", "sounds good", "that's right", "absolutely"]
    is_confirmed = any(word in last_user_msg for word in confirmation_words)

    updates = {
        "messages": [AIMessage(content=_clean_response(response.content))],
    }

    if is_confirmed:
        updates["confirmed"] = True
        updates["current_step"] = "create_event"
    else:
        # User wants changes, go back to collecting
        updates["current_step"] = "collect_info"

    return updates


def create_event_node(state: SchedulingState) -> dict:
    """Create the Google Calendar event."""
    try:
        # Parse the datetime
        dt = datetime.fromisoformat(state.date_time)
        title = state.meeting_title or f"Meeting with {state.name}"

        result = create_event(
            summary=title,
            start_time=dt,
            duration_minutes=60,
            attendee_name=state.name or "User",
            user_token=state.user_token,  # PASS THE TOKEN!
        )

        success_msg = (
            f"Your meeting '{result['summary']}' has been created! "
            f"It's scheduled for {dt.strftime('%A, %B %d at %I:%M %p')}. "
            f"Is there anything else I can help you with?"
        )

        return {
            "messages": [AIMessage(content=success_msg)],
            "event_created": True,
            "event_link": result.get("event_link", ""),
            "current_step": "done",
        }

    except Exception as e:
        error_msg = (
            f"I'm sorry, I ran into an issue creating the calendar event: {str(e)}. "
            "Would you like me to try again?"
        )
        return {
            "messages": [AIMessage(content=error_msg)],
            "current_step": "confirm",
        }


# ─── Routing Logic ────────────────────────────────────────────────────

def router(state: SchedulingState) -> str:
    """Determine the next node based on current state."""
    if not state.messages:
        return "greeting"
    
    if state.confirmed and state.current_step == "create_event":
        return "create_event"
    
    if state.name and state.date_time:
        return "confirm"
    
    return "collect_info"


# ─── Helper Functions ─────────────────────────────────────────────────

def _parse_extraction(content: str, state: SchedulingState) -> dict:
    """Parse the JSON extraction block from LLM response."""
    updates = {}
    json_match = re.search(r"```json\s*(\{.*?\})\s*```", content, re.DOTALL)
    if not json_match:
        json_match = re.search(r'\{[^{}]*"extracted_name"[^{}]*\}', content, re.DOTALL)

    if json_match:
        try:
            json_str = json_match.group(1) if "```" in content else json_match.group(0)
            data = json.loads(json_str)

            if data.get("extracted_name") and not state.name:
                updates["name"] = data["extracted_name"]
            if data.get("extracted_datetime") and not state.date_time:
                updates["date_time"] = data["extracted_datetime"]
            if data.get("extracted_title") and not state.meeting_title:
                updates["meeting_title"] = data["extracted_title"]
            if data.get("confirmed"):
                updates["confirmed"] = True
                updates["current_step"] = "create_event"

        except json.JSONDecodeError:
            pass

    # Determine next step based on what we have
    has_name = updates.get("name") or state.name
    has_datetime = updates.get("date_time") or state.date_time

    if has_name and has_datetime and "current_step" not in updates:
        updates["current_step"] = "confirm"
    elif "current_step" not in updates:
        updates["current_step"] = "collect_info"

    return updates


def _clean_response(content: str) -> str:
    """Remove the JSON extraction block from the visible response."""
    cleaned = re.sub(r"```json\s*\{.*?\}\s*```", "", content, flags=re.DOTALL)
    cleaned = re.sub(r'\{[^{}]*"extracted_name"[^{}]*\}', "", cleaned, flags=re.DOTALL)
    return cleaned.strip()


# ─── Build the Graph ──────────────────────────────────────────────────

def build_scheduling_graph() -> StateGraph:
    """Build and compile the LangGraph scheduling workflow."""
    graph = StateGraph(SchedulingState)

    graph.add_node("greeting", greeting_node)
    graph.add_node("collect_info", collect_info_node)
    graph.add_node("confirm", confirm_node)
    graph.add_node("create_event", create_event_node)

    graph.set_conditional_entry_point(
        router,
        {
            "greeting": "greeting",
            "collect_info": "collect_info",
            "confirm": "confirm",
            "create_event": "create_event",
        }
    )
    
    graph.add_edge("greeting", END)

    graph.add_conditional_edges(
        "collect_info",
        lambda state: "confirm" if (state.name and state.date_time) else "wait",
        {
            "confirm": "confirm",
            "wait": END
        }
    )

    graph.add_conditional_edges(
        "confirm",
        lambda state: "create_event" if state.confirmed else "collect_info",
        {
            "create_event": "create_event",
            "collect_info": "collect_info"
        }
    )

    graph.add_edge("create_event", END)

    return graph.compile()


scheduling_agent = build_scheduling_graph()


async def process_message(
    user_message: str, 
    conversation_state: dict, 
    user_token: dict = None,
    gemini_api_key: str = None
) -> dict:
    """Process a user message through the scheduling agent."""
    messages = []
    for m in conversation_state.get("messages", []):
        if m["role"] == "user":
            messages.append(HumanMessage(content=m["content"]))
        else:
            messages.append(AIMessage(content=m["content"]))

    initial_state = {
        "messages": messages,
        "name": conversation_state.get("name"),
        "date_time": conversation_state.get("date_time"),
        "meeting_title": conversation_state.get("meeting_title"),
        "confirmed": conversation_state.get("confirmed", False),
        "event_created": conversation_state.get("event_created", False),
        "event_link": conversation_state.get("event_link"),
        "current_step": conversation_state.get("current_step", "greeting"),
        "user_token": user_token or conversation_state.get("user_token"),
        "gemini_api_key": gemini_api_key or conversation_state.get("gemini_api_key"),
    }

    if user_message:
        initial_state["messages"].append(HumanMessage(content=user_message))

    final_state = await scheduling_agent.ainvoke(initial_state)

    ai_response = ""
    for msg in reversed(final_state["messages"]):
        if isinstance(msg, AIMessage):
            ai_response = msg.content
            break

    response_data = {
        "response": ai_response,
        "state": {
            "messages": [
                {"role": "user" if isinstance(m, HumanMessage) else "assistant", "content": m.content}
                for m in final_state["messages"]
            ],
            "name": final_state.get("name"),
            "date_time": final_state.get("date_time"),
            "meeting_title": final_state.get("meeting_title"),
            "confirmed": final_state.get("confirmed", False),
            "event_created": final_state.get("event_created", False),
            "event_link": final_state.get("event_link"),
            "current_step": final_state.get("current_step", "greeting"),
            "user_token": final_state.get("user_token"),
            "gemini_api_key": final_state.get("gemini_api_key"),
        },
    }

    if final_state.get("event_created"):
        response_data["event"] = {
            "link": final_state.get("event_link"),
            "title": final_state.get("meeting_title") or f"Meeting with {final_state.get('name')}",
            "date_time": final_state.get("date_time"),
            "name": final_state.get("name"),
        }

    return response_data
