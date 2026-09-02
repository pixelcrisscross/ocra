import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError("GEMINI_API_KEY not found")

print("API key found:", api_key[:8] + "...")


client = genai.Client(
    api_key=api_key
)

print("Calling Gemini...")

response = client.models.generate_content(
    model="gemini-3.5-flash",
    contents="Reply with exactly: ORCA_OK"
)

print("Gemini response:")
print(response.text)