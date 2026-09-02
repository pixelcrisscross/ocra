import json
from google import genai
from google.genai import types

from config import GEMINI_API_KEY, GEMINI_MODEL_L1
from schemas import Intent

client = genai.Client(api_key=GEMINI_API_KEY)


def parse_user_query(query: str) -> Intent:
    prompt = f"""
You are ORCA Level 1, a conversational intent extractor.

Convert the user's natural language into JSON for downstream ocean-data agents.

USER:
{query}

Rules:
- Extract the place name exactly as understood.
- If coordinates are explicitly given by the user, preserve them.
- Otherwise leave latitude/longitude null. A later deterministic geocoder will resolve them.
- Identify the requested marine/weather parameters.
- If user says current/now/today, use time_range='current'.
- Never invent measurements.
- Return only JSON.
"""

    response = client.models.generate_content(
        model=GEMINI_MODEL_L1,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=Intent.model_json_schema(),
            temperature=0,
        ),
    )
    if not response.text:
        raise RuntimeError("Level 1 Gemini returned empty output")
    return Intent.model_validate(json.loads(response.text))
