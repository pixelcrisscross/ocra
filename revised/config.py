import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL_L1 = os.getenv("GEMINI_MODEL_L1", "gemini-2.5-flash-lite")
GEMINI_MODEL_L5 = os.getenv("GEMINI_MODEL_L5", "gemini-2.5-flash")

if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY is missing. Put it in .env")
