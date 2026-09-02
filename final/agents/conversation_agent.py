import json
from google import genai
from google.genai import types
from config import GEMINI_API_KEY, GEMINI_MODEL_L1
from schemas import Intent

client = genai.Client(api_key=GEMINI_API_KEY)


def parse_user_query(query: str) -> Intent:
    prompt = f"""
You are ORCA Level 1. Convert the user's natural-language request into structured JSON.

USER:
{query}

Rules:
- Extract the intent.
- Extract the location name.
- Only use coordinates if the user explicitly provides them.
- Extract specific requested parameters.
- If the request is broad (for example 'sea conditions', 'ocean conditions',
  'marine conditions', or 'what is the sea like'), set requested_parameters to:
  ["sea_surface_temperature", "wave_height", "wave_period", "wave_direction",
   "current_speed", "current_direction", "wind_speed", "wind_direction",
   "pressure", "precipitation", "weather_code", "sea_level"]
- If the user explicitly asks about ocean health/biology, additionally include:
  salinity, chlorophyll, mixed_layer_depth.
- Never invent numeric measurements.
- Use time_range='current' for now/current/currently.
- Return ONLY JSON.
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

    return Intent.model_validate_json(response.text)
