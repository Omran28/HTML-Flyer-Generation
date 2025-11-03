import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Keys & Model Names
Gemini2Pro_API_KEY = os.getenv("Gemini2Pro_API_KEY", "")
Gemini2Pro_MODEL = os.getenv("Gemini2Pro_MODEL", "models/gemini-2.5-pro")

Gemini2Flash_API_KEY = os.getenv("Gemini2Flash_API_KEY", "")
Gemini2Flash_MODEL = os.getenv("Gemini2Flash_MODEL", "models/gemini-2.5-flash")


ACTIVE_MODEL = Gemini2Pro_MODEL
ACTIVE_API_KEY = Gemini2Pro_API_KEY

MODEL_MODE = "pro"
if MODEL_MODE == "flash":
    ACTIVE_MODEL = Gemini2Flash_MODEL
    ACTIVE_API_KEY = Gemini2Flash_API_KEY


if ACTIVE_API_KEY:
    os.environ["GOOGLE_API_KEY"] = ACTIVE_API_KEY

print(f"\nModel Used: {ACTIVE_MODEL}")