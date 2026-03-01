from typing import Optional
from langchain_core.messages import BaseMessage
from pydantic import BaseModel, Field

class SchedulingState(BaseModel):
    """The conversation state for the scheduling agent."""
    # Conversation history
    messages: list[BaseMessage] = Field(default_factory=list)
    
    # Extracted fields
    name: Optional[str] = None
    date_time: Optional[str] = None
    meeting_title: Optional[str] = None

    # Flow control
    confirmed: bool = False
    event_created: bool = False
    event_link: Optional[str] = None
    current_step: str = "greeting"  # greeting, collect_info, confirm, create_event, done
    
    # Auth and keys passed from frontend
    user_token: Optional[dict] = None
    gemini_api_key: Optional[str] = None
