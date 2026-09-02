import json
from google import genai
from google.genai import types
from config import GEMINI_API_KEY, GEMINI_MODEL_L5
from schemas import FinalLanguageOutput, UnifiedData

client = genai.Client(api_key=GEMINI_API_KEY)


def generate_final(unified: UnifiedData) -> FinalLanguageOutput:
    prompt = f"""
You are ORCA Level 5.

Use ONLY this validated JSON. Do not browse. Do not call tools. Do not invent values,
sources, timestamps, or safety facts.

{json.dumps(unified.model_dump(), indent=2, ensure_ascii=False)}

Write a concise, factual marine-intelligence response in JSON with:
status, summary, observations, recommendations.

Rules:
- Keep status aligned with assessment.overall_status.
- Distinguish model data from observations.
- Mention critical missing data.
- If safety_assessment is not a full safety assessment, say so.
- Do not create new numbers.
- Do not create source names or URLs.
"""
    r = client.models.generate_content(
        model=GEMINI_MODEL_L5,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=FinalLanguageOutput.model_json_schema(),
            temperature=0.2,
        ),
    )
    return FinalLanguageOutput.model_validate_json(r.text)
