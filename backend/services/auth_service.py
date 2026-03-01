import json
import requests
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from config import settings

# This scope is for the specific user's calendar
SCOPES = ["https://www.googleapis.com/auth/calendar"]

def exchange_code_for_token(code: str) -> dict:
    """
    Exchange the authorization code for access and refresh tokens.
    """
    # Note: We are using the 'post-message' or 'frontend-flow' which means 
    # we usually get an auth code that the backend exchanges.
    
    token_url = "https://oauth2.googleapis.com/token"
    payload = {
        "code": code,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": "postmessage",
        "grant_type": "authorization_code",
    }
    
    response = requests.post(token_url, data=payload)
    if response.status_code != 200:
        raise Exception(f"Failed to exchange code: {response.text}")
    
    return response.json()

def get_credentials_from_token(token_data: dict) -> Credentials:
    """
    Create a Google Credentials object from raw token data.
    """
    return Credentials(
        token=token_data.get("access_token"),
        refresh_token=token_data.get("refresh_token"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        scopes=SCOPES
    )
