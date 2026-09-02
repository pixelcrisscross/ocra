import json
from google import genai
from google.genai import types

from config import GEMINI_API_KEY, GEMINI_MODEL
from schemas import Intent


client = genai.Client(
    api_key=GEMINI_API_KEY
)


INTENT_SCHEMA = {
    "type": "object",
    "properties": {
        "user_query": {
            "type": "string"
        },
        "intent": {
            "type": "string"
        },
        "location": {
            "type": "object",
            "properties": {
                "latitude": {
                    "type": "number"
                },
                "longitude": {
                    "type": "number"
                },
                "name": {
                    "type": "string"
                }
            },
            "required": [
                "latitude",
                "longitude"
            ]
        },
        "requested_parameters": {
            "type": "array",
            "items": {
                "type": "string"
            }
        },
        "time_range": {
            "type": "string"
        },
        "region": {
            "type": "string"
        }
    },
    "required": [
        "user_query",
        "intent",
        "location",
        "requested_parameters",
        "time_range"
    ]
}


def parse_user_query(query: str) -> Intent:

    prompt = f"""
You are ORCA Level 1.

Convert the user's natural-language request into structured JSON.

User request:
{query}

Identify:

- intent
- location
- latitude
- longitude
- requested ocean parameters
- time range
- region

Supported parameters include:

sea_surface_temperature
wave_height
wave_period
wave_direction
ocean_current_speed
ocean_current_direction
sea_level
salinity
chlorophyll
wind
weather
cyclone

Do not invent measurements.

Return only JSON.
"""

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=INTENT_SCHEMA,
            temperature=0
        )
    )

    if not response.text:
        raise RuntimeError("Gemini returned an empty response")

    return Intent.model_validate(
        json.loads(response.text)
    )