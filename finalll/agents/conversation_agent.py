import json
from google import genai
from google.genai import types
from config import GEMINI_API_KEY, GEMINI_MODEL_L1
from schemas import Intent

client = genai.Client(api_key=GEMINI_API_KEY)


def parse_user_query(query: str, supplied_location=None) -> Intent:
    prompt = f"""
You are ORCA Level 1, the conversational intent agent.
Convert the user request to JSON for downstream tools.

USER: {query}
SUPPLIED LOCATION: {supplied_location or 'none'}

Detect the language and set `language` to an ISO-like language code (en, hi, te, ta, kn, ml, bn, mr, or another suitable code).

Treat these broad requests as specific parameter groups:
- sea conditions => SST, wave height, wave period, wave direction, current speed/direction, sea level
- weather => wind speed/direction, pressure, precipitation, weather code
- fishing productivity => SST, chlorophyll, currents, relevant historical indicators
- safe venture / safe fishing => marine + weather + hazard + tide/sea level
- PFZ => nearest PFZ / fishing advisory
- route => safe route optimization
- alerts => cyclone, lightning, severe weather, wave/wind hazards

Do not invent coordinates. If the user supplied a location name but not coordinates, leave lat/lon null.
Return ONLY JSON.
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
        raise RuntimeError("Level 1 returned empty output")
    obj = json.loads(response.text)
    if supplied_location:
        obj["location"] = {
            **obj.get("location", {}),
            **supplied_location.model_dump(exclude_none=True),
        }
    # Expand broad language that models sometimes leave unchanged.
    if obj.get("requested_parameters") == ["sea conditions"]:
        obj["requested_parameters"] = [
            "sea_surface_temperature", "wave_height", "wave_period",
            "wave_direction", "current_speed", "current_direction",
            "sea_level", "wind_speed", "wind_direction", "pressure",
            "precipitation", "weather_code",
        ]
    return Intent.model_validate(obj)
