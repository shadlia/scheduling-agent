import re
from fastapi import HTTPException
from langchain_google_genai import ChatGoogleGenerativeAI

def get_llm(gemini_api_key: str):
    """Initialize the LLM with the user's API key."""
    if not gemini_api_key:
        raise HTTPException(status_code=400, detail="Gemini API Key is missing. Please provide it in the Settings.")
    
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=gemini_api_key,
        temperature=0.3,
    )

def clean_response(content: str) -> str:
    """Remove the JSON extraction block from the visible response."""
    cleaned = re.sub(r"```json\s*\{.*?\}\s*```", "", content, flags=re.DOTALL | re.IGNORECASE)
    cleaned = re.sub(r"```\s*\{.*?\}\s*```", "", cleaned, flags=re.DOTALL)
    cleaned = re.sub(r"\{[\s\n]*\"extracted_.*?\}.*?$", "", cleaned, flags=re.DOTALL)
    return cleaned.strip()
