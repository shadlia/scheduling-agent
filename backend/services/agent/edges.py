import re
import json
from services.agent.state import SchedulingState

def parse_extraction(content: str, state: SchedulingState) -> dict:
    """Parse the JSON extraction block from LLM response and determine next step."""
    updates = {}
    
    # Complete match with json markdown
    json_match = re.search(r"```json\s*(\{.*?\})\s*```", content, re.DOTALL | re.IGNORECASE)
    
    # Fallback: markdown without language specifier
    if not json_match:
        json_match = re.search(r"```\s*(\{.*?\})\s*```", content, re.DOTALL)
        
    # Fallback: Raw JSON dictionary at the very end containing "extracted_"
    if not json_match:
        json_match = re.search(r"(\{[\s\n]*\"extracted_.*?\})[\s\n]*$", content, re.DOTALL)

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
    has_datetime = updates.get("date_time") or state.date_time
    has_title = updates.get("meeting_title") or state.meeting_title

    if has_datetime and has_title and "current_step" not in updates:
        updates["current_step"] = "confirm"
    elif "current_step" not in updates:
        updates["current_step"] = "collect_info"

    return updates

def router(state: SchedulingState) -> str:
    """Determine the next node based on current state."""
    if not state.messages:
        return "greeting"
    
    if state.current_step == "create_event":
        return "create_event"
    
    if state.current_step == "confirm":
        return "confirm"
    
    return "collect_info"
