import json

from google import genai
from google.genai import types

from config import GEMINI_API_KEY, GEMINI_MODEL
from schemas import UnifiedOceanData, FinalResponse


client = genai.Client(
    api_key=GEMINI_API_KEY
)


FINAL_SCHEMA = {
    "type": "object",

    "properties": {

        "location": {
            "type": "object",
            "properties": {
                "latitude": {"type": "number"},
                "longitude": {"type": "number"},
                "name": {"type": "string"}
            },
            "required": [
                "latitude",
                "longitude"
            ]
        },

        "status": {
            "type": "string"
        },

        "summary": {
            "type": "string"
        },

        "current_conditions": {
            "type": "object"
        },

        "risks": {
            "type": "object"
        },

        "observations": {
            "type": "array",
            "items": {
                "type": "string"
            }
        },

        "recommendations": {
            "type": "array",
            "items": {
                "type": "string"
            }
        },

        "sources": {
            "type": "array",
            "items": {
                "type": "object"
            }
        }
    },

    "required": [
        "location",
        "status",
        "summary",
        "current_conditions",
        "risks",
        "observations",
        "recommendations",
        "sources"
    ]
}


def generate_final_response(
    unified: UnifiedOceanData
):

    payload = unified.model_dump()

    prompt = f"""
You are ORCA Level 5, the final ocean intelligence agent.

The user has already been processed by previous agents.

You have been given structured ocean information.

IMPORTANT:

- Do NOT search the web.
- Do NOT use Google Search.
- Do NOT invent numerical values.
- Do NOT modify measurements.
- Do NOT claim an observation if the value is missing.
- Explain uncertainty where appropriate.
- Use ONLY the supplied JSON.
- Produce ONLY valid JSON.

INPUT DATA:

{json.dumps(payload, indent=2)}

Create a clear marine intelligence response.

The output should contain:

1. Overall status
2. Plain-language summary
3. Current measured/modelled conditions
4. Risks
5. Important observations
6. Practical recommendations
7. Sources
"""

    response = client.models.generate_content(

        model=GEMINI_MODEL,

        contents=prompt,

        config=types.GenerateContentConfig(

            response_mime_type="application/json",

            response_schema=FINAL_SCHEMA,

            temperature=0.2
        )
    )

    result = json.loads(response.text)

    return FinalResponse.model_validate(result)