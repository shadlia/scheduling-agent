from datetime import datetime
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from services.agent.state import SchedulingState
from services.agent.utils import get_llm, clean_response
from services.agent.prompts import SYSTEM_PROMPT
from services.agent.edges import parse_extraction
from services.calendar_service import create_event

def greeting_node(state: SchedulingState) -> dict:
    """Initial greeting — only triggered for the first message."""
    llm = get_llm(state.gemini_api_key)
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
        "messages": [AIMessage(content=clean_response(response.content))],
        "current_step": "collect_info",
    }

def collect_info_node(state: SchedulingState) -> dict:
    """Collect name, date/time, title from the user."""
    llm = get_llm(state.gemini_api_key)
    today = datetime.now().strftime("%Y-%m-%d (%A)")

    collected = []
    missing = []

    if state.date_time:
        collected.append(f"Date/Time: {state.date_time}")
    else:
        missing.append("preferred date AND exact time for the meeting")

    if state.meeting_title:
        collected.append(f"Meeting Title: {state.meeting_title}")
    else:
        missing.append("title or topic for the meeting")
        
    if state.name:
        collected.append(f"Name: {state.name}")

    state_info = f"""
Already collected: {', '.join(collected) if collected else 'Nothing yet'}
Still need: {', '.join(missing) if missing else 'Required info collected!'}
The user's name is optional. You MUST collect a date/time AND a meeting title.
If date/time and title are collected, immediately summarize the details and explicitly ask the user to confirm so you can create the event.
"""

    system_msg = SystemMessage(content=SYSTEM_PROMPT.format(state_info=state_info, today=today))

    messages = [system_msg]
    if not state.messages:
        messages.append(HumanMessage(content="Continue collecting information."))
    else:
        messages.extend(state.messages)

    response = llm.invoke(messages)

    # Parse extraction JSON from the response
    updates = parse_extraction(response.content, state)
    updates["messages"] = [AIMessage(content=clean_response(response.content))]

    return updates

def confirm_node(state: SchedulingState) -> dict:
    """Handle user confirmation."""
    llm = get_llm(state.gemini_api_key)
    today = datetime.now().strftime("%Y-%m-%d (%A)")

    # Format details gracefully
    details_str = f"- Date/Time: {state.date_time}\n- Title: {state.meeting_title}"
    if state.name:
        details_str = f"- Name: {state.name}\n" + details_str

    state_info = f"""
The user has been asked to confirm these meeting details:
{details_str}

Check if the user's latest message is a confirmation (yes, sure, correct, go ahead, etc.) or a rejection/change request.
If confirmed, respond with something like "Creating your meeting now..."
If they want changes, ask what they'd like to change.
"""

    system_msg = SystemMessage(content=SYSTEM_PROMPT.format(state_info=state_info, today=today))

    messages = [system_msg]
    if not state.messages:
        messages.append(HumanMessage(content="Checking for confirmation."))
    else:
        messages.extend(state.messages)

    response = llm.invoke(messages)

    last_user_msg = ""
    for msg in reversed(state.messages):
        if isinstance(msg, HumanMessage):
            last_user_msg = msg.content.lower()
            break

    confirmation_words = ["yes", "yeah", "yep", "sure", "correct", "confirm", "go ahead", "do it", "ok", "okay", "perfect", "sounds good", "that's right", "absolutely", "please"]
    is_confirmed = any(word in last_user_msg for word in confirmation_words)

    updates = {
        "messages": [AIMessage(content=clean_response(response.content))],
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
        title = state.meeting_title or "Scheduled Meeting"

        result = create_event(
            summary=title,
            start_time=dt,
            duration_minutes=60,
            attendee_name=state.name or "",
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
