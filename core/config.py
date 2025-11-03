import os
import os
from dotenv import load_dotenv

# Load environment variables from .env file (must be in project root)
load_dotenv()

"API Keys"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "models/gemini-2.5-pro")

# Ensure the main API key is available for usage
if GEMINI_API_KEY:
    os.environ["Gemini_API_KEY"] = GEMINI_API_KEY


def validate_config():
    # Check which API keys exist
    APIs_dict = {
        "Gemini API Key": bool(GEMINI_API_KEY),
    }

    # Print status of each key
    for key, exists in APIs_dict.items():
        print(f"{key}: {'Found' if exists else 'Missing'}")

    return True


validate_config()
