from langchain_google_genai import ChatGoogleGenerativeAI
from core import config


def initialize_llm():
    try:
        model = config.ACTIVE_MODEL
        api_key = config.ACTIVE_API_KEY

        if not api_key:
            raise ValueError(f"Missing API key for Gemini {model_type.upper()} model.")

        llm = ChatGoogleGenerativeAI(
            model=model,
            google_api_key=api_key,
            temperature=0.6,
            convert_system_message_to_human=True,
        )
        return llm

    except Exception as e:
        raise RuntimeError(f"❌ Failed to initialize Gemini LLM ({model_type}): {e}")

