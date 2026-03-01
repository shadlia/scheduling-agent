from langchain_core.messages import HumanMessage, AIMessage
from services.agent.graph import scheduling_agent

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
            "title": final_state.get("meeting_title") or f"Meeting with {final_state.get('name') or 'User'}",
            "date_time": final_state.get("date_time"),
            "name": final_state.get("name"),
        }

    return response_data
