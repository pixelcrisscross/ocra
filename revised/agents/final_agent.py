import json
from google import genai
from google.genai import types

from config import GEMINI_API_KEY, GEMINI_MODEL_L5
from schemas import FinalLanguageOutput, UnifiedData

client = genai.Client(api_key=GEMINI_API_KEY)


def generate_final(unified: UnifiedData) -> FinalLanguageOutput:
    payload = unified.model_dump()
    prompt = f"""
You are ORCA Level 5, the final ocean intelligence communicator.

Use ONLY the supplied JSON. Do not browse. Do not call tools. Do not invent or alter numeric measurements.
Do not create, remove, or modify source URLs. Do not say a location is safe for navigation/fishing unless the supplied risk data actually supports that conclusion; use cautious language.

INPUT JSON:
{json.dumps(payload, indent=2)}

Return JSON with:
- status: short status matching the deterministic assessment
- summary: 1-3 sentence plain-language explanation
- observations: concise, evidence-based observations
- recommendations: practical next steps, especially when data is missing

Do not repeat every number in the summary. Mention important missing variables when relevant.
"""

    response = client.models.generate_content(
        model=GEMINI_MODEL_L5,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=FinalLanguageOutput.model_json_schema(),
            temperature=0.2,
        ),
    )
    if not response.text:
        raise RuntimeError("Level 5 Gemini returned empty output")
    return FinalLanguageOutput.model_validate(json.loads(response.text))
