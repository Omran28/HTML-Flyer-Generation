from langchain_google_genai import ChatGoogleGenerativeAI
from core import config


def initialize_llm():
    try:
        llm = ChatGoogleGenerativeAI(
            model=config.GEMINI_MODEL,
            google_api_key=config.GEMINI_API_KEY,
            temperature=0.6,
            convert_system_message_to_human=True
        )
        return llm
    except Exception as e:
        raise RuntimeError(f"❌ Failed to initialize Gemini LLM: {e}")