"""
Google Calendar Service — Creates and lists events via the Google Calendar API.
Supports both Service Account (Legacy) and User OAuth2 (New).
"""

import os
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from google.oauth2 import service_account
from config import settings
from services.auth_service import get_credentials_from_token

SCOPES = ["https://www.googleapis.com/auth/calendar"]

def _get_calendar_service(user_credentials=None):
    """Build and return an authenticated Google Calendar service."""
    if user_credentials:
        # Use individual user credentials (OAuth2)
        return build("calendar", "v3", credentials=user_credentials)
        
    # FALLBACK to Service Account (Phase 1 legacy)
    # If not found, just return None. Service methods will handle it.
    if not os.path.exists(settings.GOOGLE_SERVICE_ACCOUNT_FILE):
        return None
    
    credentials = service_account.Credentials.from_service_account_file(
        settings.GOOGLE_SERVICE_ACCOUNT_FILE,
        scopes=SCOPES,
    )
    return build("calendar", "v3", credentials=credentials)


def create_event(
    summary: str,
    start_time: datetime,
    duration_minutes: int = 60,
    description: str = "",
    attendee_name: str = "",
    user_token: dict = None,
) -> dict:
    """
    Create a Google Calendar event.
    """
    user_creds = get_credentials_from_token(user_token) if user_token else None
    service = _get_calendar_service(user_creds)
    
    calendar_id = "primary" if user_token else settings.GOOGLE_CALENDAR_ID
    end_time = start_time + timedelta(minutes=duration_minutes)

    # Build description
    full_description = f"Scheduled by: {attendee_name}\n" if attendee_name else ""
    if description:
        full_description += description

    event_body = {
        "summary": summary,
        "description": full_description.strip(),
        "start": {
            "dateTime": start_time.isoformat(),
            "timeZone": "UTC",
        },
        "end": {
            "dateTime": end_time.isoformat(),
            "timeZone": "UTC",
        },
    }

    event = (
        service.events()
        .insert(calendarId=calendar_id, body=event_body)
        .execute()
    )

    return {
        "event_id": event.get("id"),
        "event_link": event.get("htmlLink"),
        "summary": event.get("summary"),
        "start": event["start"].get("dateTime"),
        "end": event["end"].get("dateTime"),
    }


def list_events(
    max_results: int = 50, 
    user_token: dict = None,
    time_min: str = None,
    time_max: str = None
) -> list:
    """
    Fetch upcoming events from the Google Calendar.
    """
    print(f"DEBUG: Fetching events. User Token provided: {bool(user_token)}")
    try:
        user_creds = get_credentials_from_token(user_token) if user_token else None
    except Exception as e:
        print(f"DEBUG: Token Error: {str(e)}")
        raise HTTPException(status_code=401, detail=f"Invalid or expired token: {str(e)}")

    service = _get_calendar_service(user_creds)
    
    calendar_id = "primary" if user_token else settings.GOOGLE_CALENDAR_ID
    
    # Defaults to now if not provided
    if not time_min:
        time_min = datetime.utcnow().isoformat() + "Z"

    try:
        events_result = (
            service.events()
            .list(
                calendarId=calendar_id,
                timeMin=time_min,
                timeMax=time_max,
                maxResults=max_results,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        events = events_result.get("items", [])
        print(f"DEBUG: Successfully fetched {len(events)} events.")
        
        return [
            {
                "id": event.get("id"),
                "summary": event.get("summary"),
                "start": event["start"].get("dateTime") or event["start"].get("date"),
                "end": event["end"].get("dateTime") or event["end"].get("date"),
                "link": event.get("htmlLink"),
                "description": event.get("description"),
                "location": event.get("location"),
            }
            for event in events
        ]
    except Exception as e:
        print(f"DEBUG: Google API List Error: {str(e)}")
        # If it's a 404/403, we might want to return empty list instead of 500
        if "HttpError 404" in str(e) or "HttpError 403" in str(e):
            return []
        raise e
